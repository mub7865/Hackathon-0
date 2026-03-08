"""
Accounting Actions Module
Processes accounting task requests (invoices, payments, expenses) with approval workflow
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

from src.models.transaction import (
    BusinessTransaction,
    TransactionType,
    TransactionStatus,
    validate_transaction
)
from src.utils.odoo_client import OdooClient, OdooError, OdooAuthenticationError
from src.utils.odoo_methods import (
    create_invoice,
    record_payment,
    create_expense,
    post_invoice
)
from src.utils.file_utils import (
    parse_task_file,
    update_task_frontmatter,
    move_task_file
)
from src.utils.retry_handler import with_retry, queue_action_on_failure
from src.utils.error_utils import ErrorLog, ErrorType, log_error_to_file
from src.utils.dashboard_utils import add_activity_entry
import uuid

logger = logging.getLogger(__name__)


class AccountingActionError(Exception):
    """Base exception for accounting action errors"""
    pass


def _get_vault_path() -> Path:
    """Get vault path from environment or default"""
    vault_path = os.getenv('VAULT_PATH', str(Path(__file__).parent.parent.parent / 'vault'))
    return Path(vault_path)


def _check_approval_threshold(transaction: BusinessTransaction) -> bool:
    """
    Check if transaction requires approval based on threshold

    Args:
        transaction: BusinessTransaction to check

    Returns:
        True if requires approval, False otherwise
    """
    return transaction.amount > transaction.approval_threshold


def _move_to_pending_approval(
    task_file_path: str,
    transaction: BusinessTransaction,
    reason: str
) -> str:
    """
    Move task to Pending_Approval folder

    Args:
        task_file_path: Path to task file
        transaction: BusinessTransaction requiring approval
        reason: Reason for approval requirement

    Returns:
        New file path
    """
    # Update frontmatter
    update_task_frontmatter(
        task_file_path,
        {
            'status': 'pending_approval',
            'requires_approval': True,
            'approval_reason': reason,
            'approval_requested_at': datetime.now().isoformat(),
            'transaction_amount': transaction.amount,
            'transaction_party': transaction.party
        }
    )

    # Move to Pending_Approval folder
    new_path = move_task_file(task_file_path, 'Pending_Approval')
    logger.info(f"Task moved to pending approval: {new_path}")

    # Add dashboard activity
    vault_path = _get_vault_path()
    add_activity_entry(
        str(vault_path),
        source='Accounting',
        activity_type='Approval Required',
        status='Pending',
        summary=f"${transaction.amount:.2f} {transaction.transaction_type.value} - {transaction.party}"
    )

    return new_path


def _execute_transaction(
    client: OdooClient,
    transaction: BusinessTransaction
) -> Dict[str, Any]:
    """
    Execute transaction in Odoo

    Args:
        client: Authenticated OdooClient
        transaction: BusinessTransaction to execute

    Returns:
        Dictionary with execution results (id, name, url)

    Raises:
        OdooError: If execution fails
    """
    if transaction.transaction_type == TransactionType.INVOICE:
        result = create_invoice(client, transaction)
        # Post the invoice immediately
        post_invoice(client, result['invoice_id'])
        return result
    elif transaction.transaction_type == TransactionType.PAYMENT:
        return record_payment(client, transaction)
    elif transaction.transaction_type == TransactionType.EXPENSE:
        result = create_expense(client, transaction)
        # Post the expense immediately
        post_invoice(client, result['expense_id'])
        return result
    else:
        raise ValueError(f"Unknown transaction type: {transaction.transaction_type}")


def _complete_task(
    task_file_path: str,
    transaction: BusinessTransaction,
    odoo_result: Dict[str, Any]
) -> str:
    """
    Mark task as complete and move to Done folder

    Args:
        task_file_path: Path to task file
        transaction: Completed BusinessTransaction
        odoo_result: Result from Odoo execution

    Returns:
        New file path
    """
    # Update transaction with Odoo details
    transaction.post_to_odoo(
        odoo_id=str(odoo_result.get('invoice_id') or odoo_result.get('payment_id') or odoo_result.get('expense_id')),
        odoo_url=odoo_result.get('odoo_url', '')
    )

    # Update frontmatter
    update_task_frontmatter(
        task_file_path,
        {
            'status': 'done',
            'completed_at': datetime.now().isoformat(),
            'odoo_id': transaction.transaction_id,
            'odoo_url': transaction.odoo_url,
            'odoo_name': odoo_result.get('invoice_name') or odoo_result.get('payment_name') or odoo_result.get('expense_name')
        }
    )

    # Move to Done folder
    new_path = move_task_file(task_file_path, 'Done')
    logger.info(f"Task completed: {new_path}")

    # Add dashboard activity
    vault_path = _get_vault_path()
    add_activity_entry(
        str(vault_path),
        source='Accounting',
        activity_type='Transaction Completed',
        status='Done',
        summary=f"${transaction.amount:.2f} {transaction.transaction_type.value} - {transaction.party}"
    )

    return new_path


def _handle_error(
    task_file_path: str,
    transaction: BusinessTransaction,
    error: Exception,
    component: str,
    operation: str
) -> None:
    """
    Handle error during transaction processing

    Args:
        task_file_path: Path to task file
        transaction: BusinessTransaction that failed
        error: Exception that occurred
        component: Component name for error log
        operation: Operation name for error log
    """
    from src.utils.error_utils import classify_error

    # Classify error
    error_type = classify_error(error, component, operation)

    # Create error log
    error_log = ErrorLog(
        error_id=str(uuid.uuid4()),
        timestamp=datetime.now(),
        error_type=error_type,
        component=component,
        operation=operation,
        error_message=str(error),
        task_id=Path(task_file_path).stem,
        context={
            'transaction_type': transaction.transaction_type.value,
            'amount': transaction.amount,
            'party': transaction.party
        }
    )

    # Log error
    log_error_to_file(error_log)

    # Update task with error
    update_task_frontmatter(
        task_file_path,
        {
            'status': 'error',
            'error_message': str(error),
            'error_type': error_type.value,
            'error_at': datetime.now().isoformat(),
            'error_id': error_log.error_id
        }
    )

    # Add dashboard activity
    vault_path = _get_vault_path()
    add_activity_entry(
        str(vault_path),
        source='Accounting',
        activity_type='Error',
        status='Error',
        summary=f"Failed: {transaction.transaction_type.value} - {str(error)[:50]}"
    )

    logger.error(f"Error processing transaction: {error}")


@with_retry(
    max_attempts=3,
    base_delay=1.0,
    component="accounting_actions",
    operation="process_invoice_request"
)
def process_invoice_request(task_file_path: str) -> str:
    """
    Process invoice creation request

    Args:
        task_file_path: Path to task file with invoice request

    Returns:
        Status: 'done', 'pending_approval', or 'error'

    Workflow:
    1. Parse task file and extract invoice details
    2. Create BusinessTransaction object
    3. Validate transaction data
    4. Check approval threshold
    5. If under threshold: create invoice in Odoo, mark done
    6. If over threshold: move to Pending_Approval
    """
    try:
        logger.info(f"Processing invoice request: {task_file_path}")

        # Parse task file
        frontmatter, body = parse_task_file(task_file_path)

        # Create transaction from task file
        transaction = BusinessTransaction.from_task_file(frontmatter, body)
        transaction.transaction_type = TransactionType.INVOICE

        # Validate transaction
        is_valid, error_msg = validate_transaction(transaction)
        if not is_valid:
            raise AccountingActionError(f"Invalid transaction: {error_msg}")

        # Add audit entry
        transaction.add_audit_entry('created', 'system', 'Invoice request received')

        # Check approval threshold
        if _check_approval_threshold(transaction):
            reason = f"Invoice amount ${transaction.amount:.2f} exceeds approval threshold ${transaction.approval_threshold:.2f}"
            logger.info(f"Invoice requires approval: {reason}")
            _move_to_pending_approval(task_file_path, transaction, reason)
            return 'pending_approval'

        # Execute transaction (under threshold)
        logger.info(f"Creating invoice in Odoo (under threshold): ${transaction.amount:.2f}")
        client = OdooClient()
        client.authenticate()

        odoo_result = _execute_transaction(client, transaction)
        client.close()

        # Complete task
        _complete_task(task_file_path, transaction, odoo_result)

        logger.info(f"Invoice created successfully: {odoo_result.get('invoice_name')}")
        return 'done'

    except OdooAuthenticationError as e:
        _handle_error(task_file_path, transaction, e, 'accounting_actions', 'process_invoice_request')
        raise
    except Exception as e:
        _handle_error(task_file_path, transaction, e, 'accounting_actions', 'process_invoice_request')
        return 'error'


@with_retry(
    max_attempts=3,
    base_delay=1.0,
    component="accounting_actions",
    operation="process_payment_request"
)
def process_payment_request(task_file_path: str) -> str:
    """
    Process payment recording request

    Args:
        task_file_path: Path to task file with payment request

    Returns:
        Status: 'done', 'pending_approval', or 'error'

    Workflow:
    1. Parse task file and extract payment details
    2. Create BusinessTransaction object
    3. Validate transaction data
    4. Check approval threshold
    5. If under threshold: record payment in Odoo, mark done
    6. If over threshold: move to Pending_Approval
    """
    try:
        logger.info(f"Processing payment request: {task_file_path}")

        # Parse task file
        frontmatter, body = parse_task_file(task_file_path)

        # Create transaction from task file
        transaction = BusinessTransaction.from_task_file(frontmatter, body)
        transaction.transaction_type = TransactionType.PAYMENT

        # Validate transaction
        is_valid, error_msg = validate_transaction(transaction)
        if not is_valid:
            raise AccountingActionError(f"Invalid transaction: {error_msg}")

        # Add audit entry
        transaction.add_audit_entry('created', 'system', 'Payment request received')

        # Check approval threshold
        if _check_approval_threshold(transaction):
            reason = f"Payment amount ${transaction.amount:.2f} exceeds approval threshold ${transaction.approval_threshold:.2f}"
            logger.info(f"Payment requires approval: {reason}")
            _move_to_pending_approval(task_file_path, transaction, reason)
            return 'pending_approval'

        # Execute transaction (under threshold)
        logger.info(f"Recording payment in Odoo (under threshold): ${transaction.amount:.2f}")
        client = OdooClient()
        client.authenticate()

        odoo_result = _execute_transaction(client, transaction)
        client.close()

        # Complete task
        _complete_task(task_file_path, transaction, odoo_result)

        logger.info(f"Payment recorded successfully: {odoo_result.get('payment_name')}")
        return 'done'

    except OdooAuthenticationError as e:
        _handle_error(task_file_path, transaction, e, 'accounting_actions', 'process_payment_request')
        raise
    except Exception as e:
        _handle_error(task_file_path, transaction, e, 'accounting_actions', 'process_payment_request')
        return 'error'


@with_retry(
    max_attempts=3,
    base_delay=1.0,
    component="accounting_actions",
    operation="process_expense_request"
)
def process_expense_request(task_file_path: str) -> str:
    """
    Process expense recording request

    Args:
        task_file_path: Path to task file with expense request

    Returns:
        Status: 'done', 'pending_approval', or 'error'

    Workflow:
    1. Parse task file and extract expense details
    2. Create BusinessTransaction object
    3. Validate transaction data
    4. Check approval threshold
    5. If under threshold: create expense in Odoo, mark done
    6. If over threshold: move to Pending_Approval
    """
    try:
        logger.info(f"Processing expense request: {task_file_path}")

        # Parse task file
        frontmatter, body = parse_task_file(task_file_path)

        # Create transaction from task file
        transaction = BusinessTransaction.from_task_file(frontmatter, body)
        transaction.transaction_type = TransactionType.EXPENSE

        # Validate transaction
        is_valid, error_msg = validate_transaction(transaction)
        if not is_valid:
            raise AccountingActionError(f"Invalid transaction: {error_msg}")

        # Add audit entry
        transaction.add_audit_entry('created', 'system', 'Expense request received')

        # Check approval threshold
        if _check_approval_threshold(transaction):
            reason = f"Expense amount ${transaction.amount:.2f} exceeds approval threshold ${transaction.approval_threshold:.2f}"
            logger.info(f"Expense requires approval: {reason}")
            _move_to_pending_approval(task_file_path, transaction, reason)
            return 'pending_approval'

        # Execute transaction (under threshold)
        logger.info(f"Creating expense in Odoo (under threshold): ${transaction.amount:.2f}")
        client = OdooClient()
        client.authenticate()

        odoo_result = _execute_transaction(client, transaction)
        client.close()

        # Complete task
        _complete_task(task_file_path, transaction, odoo_result)

        logger.info(f"Expense created successfully: {odoo_result.get('expense_name')}")
        return 'done'

    except OdooAuthenticationError as e:
        _handle_error(task_file_path, transaction, e, 'accounting_actions', 'process_expense_request')
        raise
    except Exception as e:
        _handle_error(task_file_path, transaction, e, 'accounting_actions', 'process_expense_request')
        return 'error'


def process_approved_transaction(task_file_path: str) -> str:
    """
    Process transaction after human approval

    Args:
        task_file_path: Path to approved task file (in Approved folder)

    Returns:
        Status: 'done' or 'error'

    Workflow:
    1. Parse task file and extract transaction details
    2. Create BusinessTransaction object
    3. Execute transaction in Odoo (skip approval check)
    4. Mark task as done
    """
    try:
        logger.info(f"Processing approved transaction: {task_file_path}")

        # Parse task file
        frontmatter, body = parse_task_file(task_file_path)

        # Create transaction from task file
        transaction = BusinessTransaction.from_task_file(frontmatter, body)

        # Mark as approved
        approved_by = frontmatter.get('approved_by', 'human')
        transaction.approve(approved_by)

        # Execute transaction
        logger.info(f"Executing approved transaction: ${transaction.amount:.2f}")
        client = OdooClient()
        client.authenticate()

        odoo_result = _execute_transaction(client, transaction)
        client.close()

        # Complete task
        _complete_task(task_file_path, transaction, odoo_result)

        logger.info(f"Approved transaction completed: {odoo_result.get('invoice_name') or odoo_result.get('payment_name') or odoo_result.get('expense_name')}")
        return 'done'

    except Exception as e:
        _handle_error(task_file_path, transaction, e, 'accounting_actions', 'process_approved_transaction')
        return 'error'


def get_pending_approvals(vault_path: Optional[str] = None) -> list:
    """
    Get list of transactions pending approval

    Args:
        vault_path: Path to vault directory (optional)

    Returns:
        List of pending approval task files
    """
    if vault_path is None:
        vault_path = _get_vault_path()
    else:
        vault_path = Path(vault_path)

    pending_folder = vault_path / 'Pending_Approval'

    if not pending_folder.exists():
        return []

    # Get all .md files in Pending_Approval folder
    pending_files = list(pending_folder.glob('*.md'))

    logger.info(f"Found {len(pending_files)} transactions pending approval")
    return [str(f) for f in pending_files]

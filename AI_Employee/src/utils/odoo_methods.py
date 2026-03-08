"""
Odoo Business Methods
High-level methods for common business operations (invoices, payments, expenses)
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, date

from src.utils.odoo_client import OdooClient, OdooError
from src.models.transaction import BusinessTransaction, TransactionType, TransactionStatus

logger = logging.getLogger(__name__)


def create_invoice(
    client: OdooClient,
    transaction: BusinessTransaction
) -> Dict[str, Any]:
    """
    Create customer invoice in Odoo

    Args:
        client: Authenticated OdooClient instance
        transaction: BusinessTransaction with invoice details

    Returns:
        Dictionary with invoice_id and invoice_name

    Raises:
        OdooError: If invoice creation fails
    """
    try:
        # Validate transaction type
        if transaction.transaction_type != TransactionType.INVOICE:
            raise ValueError(f"Expected INVOICE transaction, got {transaction.transaction_type.value}")

        # Get or find partner ID
        partner_id = None
        if transaction.party_id:
            partner_id = int(transaction.party_id)
        elif transaction.party:
            # Search for partner by name
            logger.info(f"Searching for customer: {transaction.party}")
            partner_ids = client.search('res.partner', [['name', '=', transaction.party]])
            if partner_ids:
                partner_id = partner_ids[0]
                logger.info(f"Found customer ID: {partner_id}")
            else:
                # Customer not found - create it
                logger.info(f"Customer not found, creating: {transaction.party}")
                partner_id = client.create('res.partner', {
                    'name': transaction.party,
                    'customer_rank': 1
                })
                logger.info(f"Created customer ID: {partner_id}")

        if not partner_id:
            raise OdooError("Customer name or ID is required for invoice")

        # Prepare invoice data
        invoice_date = transaction.date.strftime('%Y-%m-%d') if isinstance(transaction.date, datetime) else transaction.date

        # Get default income account (Product Sales account)
        # Search for account with code starting with 400 (income accounts in standard chart)
        income_accounts = client.search('account.account', [
            ['code', '=like', '400%'],
            ['account_type', '=', 'income']
        ], limit=1)

        if not income_accounts:
            # Fallback: search for any income account
            income_accounts = client.search('account.account', [
                ['account_type', '=', 'income']
            ], limit=1)

        if not income_accounts:
            raise OdooError("No income account found in Odoo. Please configure chart of accounts.")

        income_account_id = income_accounts[0]
        logger.info(f"Using income account ID: {income_account_id}")

        invoice_data = {
            'partner_id': partner_id,
            'move_type': 'out_invoice',
            'invoice_date': invoice_date,
            'invoice_line_ids': [(0, 0, {
                'name': transaction.description or 'Service',
                'quantity': 1,
                'price_unit': transaction.amount,
                'account_id': income_account_id
            })]
        }

        # Create invoice
        logger.info(f"Creating invoice for {transaction.party} (ID: {partner_id}) - ${transaction.amount}")
        invoice_id = client.create('account.move', invoice_data)

        # Read invoice name
        invoice_record = client.read('account.move', [invoice_id], ['name'])[0]
        invoice_name = invoice_record['name']

        logger.info(f"Invoice created: {invoice_name} (ID: {invoice_id})")

        return {
            'invoice_id': invoice_id,
            'invoice_name': invoice_name,
            'odoo_url': f"{client.url.replace('/jsonrpc', '')}/web#id={invoice_id}&model=account.move&view_type=form"
        }

    except Exception as e:
        logger.error(f"Failed to create invoice: {e}")
        raise OdooError(f"Invoice creation failed: {e}") from e


def record_payment(
    client: OdooClient,
    transaction: BusinessTransaction,
    journal_id: int = 1
) -> Dict[str, Any]:
    """
    Record customer payment in Odoo

    Args:
        client: Authenticated OdooClient instance
        transaction: BusinessTransaction with payment details
        journal_id: Bank journal ID (default: 1)

    Returns:
        Dictionary with payment_id and payment_name

    Raises:
        OdooError: If payment recording fails
    """
    try:
        # Validate transaction type
        if transaction.transaction_type != TransactionType.PAYMENT:
            raise ValueError(f"Expected PAYMENT transaction, got {transaction.transaction_type.value}")

        # Prepare payment data
        payment_date = transaction.date.strftime('%Y-%m-%d') if isinstance(transaction.date, datetime) else transaction.date

        payment_data = {
            'payment_type': 'inbound',
            'partner_id': int(transaction.party_id) if transaction.party_id else None,
            'amount': transaction.amount,
            'date': payment_date,
            'journal_id': journal_id,
            'ref': transaction.description or f"Payment from {transaction.party}"
        }

        # Remove None values
        payment_data = {k: v for k, v in payment_data.items() if v is not None}

        # Create payment
        logger.info(f"Recording payment from {transaction.party} - ${transaction.amount}")
        payment_id = client.create('account.payment', payment_data)

        # Read payment name
        payment_record = client.read('account.payment', [payment_id], ['name'])[0]
        payment_name = payment_record['name']

        logger.info(f"Payment recorded: {payment_name} (ID: {payment_id})")

        return {
            'payment_id': payment_id,
            'payment_name': payment_name,
            'odoo_url': f"{client.url.replace('/jsonrpc', '')}/web#id={payment_id}&model=account.payment&view_type=form"
        }

    except Exception as e:
        logger.error(f"Failed to record payment: {e}")
        raise OdooError(f"Payment recording failed: {e}") from e


def create_expense(
    client: OdooClient,
    transaction: BusinessTransaction
) -> Dict[str, Any]:
    """
    Create vendor bill (expense) in Odoo

    Args:
        client: Authenticated OdooClient instance
        transaction: BusinessTransaction with expense details

    Returns:
        Dictionary with expense_id and expense_name

    Raises:
        OdooError: If expense creation fails
    """
    try:
        # Validate transaction type
        if transaction.transaction_type != TransactionType.EXPENSE:
            raise ValueError(f"Expected EXPENSE transaction, got {transaction.transaction_type.value}")

        # Prepare expense data
        expense_date = transaction.date.strftime('%Y-%m-%d') if isinstance(transaction.date, datetime) else transaction.date

        expense_data = {
            'partner_id': int(transaction.party_id) if transaction.party_id else None,
            'move_type': 'in_invoice',
            'invoice_date': expense_date,
            'invoice_line_ids': [(0, 0, {
                'name': transaction.description or transaction.category or 'Expense',
                'quantity': 1,
                'price_unit': transaction.amount,
            })]
        }

        # Remove None values
        expense_data = {k: v for k, v in expense_data.items() if v is not None}

        # Create expense
        logger.info(f"Creating expense for {transaction.party} - ${transaction.amount} ({transaction.category})")
        expense_id = client.create('account.move', expense_data)

        # Read expense name
        expense_record = client.read('account.move', [expense_id], ['name'])[0]
        expense_name = expense_record['name']

        logger.info(f"Expense created: {expense_name} (ID: {expense_id})")

        return {
            'expense_id': expense_id,
            'expense_name': expense_name,
            'odoo_url': f"{client.url.replace('/jsonrpc', '')}/web#id={expense_id}&model=account.move&view_type=form"
        }

    except Exception as e:
        logger.error(f"Failed to create expense: {e}")
        raise OdooError(f"Expense creation failed: {e}") from e


def search_transactions(
    client: OdooClient,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    transaction_type: Optional[TransactionType] = None,
    partner_id: Optional[int] = None,
    state: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Search for transactions in Odoo

    Args:
        client: Authenticated OdooClient instance
        start_date: Start date (YYYY-MM-DD format)
        end_date: End date (YYYY-MM-DD format)
        transaction_type: Filter by transaction type (INVOICE, PAYMENT, EXPENSE)
        partner_id: Filter by partner ID
        state: Filter by state (draft, posted, paid, cancelled)
        limit: Maximum number of results (default: 100)

    Returns:
        List of transaction dictionaries

    Raises:
        OdooError: If search fails
    """
    try:
        # Build search domain
        domain = []

        # Date filters
        if start_date:
            domain.append(['invoice_date', '>=', start_date])
        if end_date:
            domain.append(['invoice_date', '<=', end_date])

        # Transaction type filter
        if transaction_type:
            if transaction_type == TransactionType.INVOICE:
                domain.append(['move_type', '=', 'out_invoice'])
            elif transaction_type == TransactionType.EXPENSE:
                domain.append(['move_type', '=', 'in_invoice'])
            # Note: PAYMENT type uses different model (account.payment), handled separately

        # Partner filter
        if partner_id:
            domain.append(['partner_id', '=', partner_id])

        # State filter
        if state:
            domain.append(['state', '=', state])

        # Search invoices and expenses (account.move)
        logger.info(f"Searching transactions with domain: {domain}")

        results = client.search_read(
            'account.move',
            domain,
            fields=['name', 'partner_id', 'amount_total', 'invoice_date', 'move_type', 'state'],
            limit=limit,
            order='invoice_date desc'
        )

        # If searching for payments specifically
        if transaction_type == TransactionType.PAYMENT:
            payment_domain = []
            if start_date:
                payment_domain.append(['date', '>=', start_date])
            if end_date:
                payment_domain.append(['date', '<=', end_date])
            if partner_id:
                payment_domain.append(['partner_id', '=', partner_id])
            if state:
                payment_domain.append(['state', '=', state])

            payments = client.search_read(
                'account.payment',
                payment_domain,
                fields=['name', 'partner_id', 'amount', 'date', 'payment_type', 'state'],
                limit=limit,
                order='date desc'
            )

            # Convert payment records to unified format
            for payment in payments:
                results.append({
                    'id': payment['id'],
                    'name': payment['name'],
                    'partner_id': payment['partner_id'],
                    'amount_total': payment['amount'],
                    'invoice_date': payment['date'],
                    'move_type': 'payment',
                    'state': payment['state']
                })

        logger.info(f"Found {len(results)} transactions")
        return results

    except Exception as e:
        logger.error(f"Failed to search transactions: {e}")
        raise OdooError(f"Transaction search failed: {e}") from e


def get_weekly_summary(
    client: OdooClient,
    week_start: str,
    week_end: str
) -> Dict[str, Any]:
    """
    Get weekly transaction summary for CEO briefing

    Args:
        client: Authenticated OdooClient instance
        week_start: Week start date (YYYY-MM-DD)
        week_end: Week end date (YYYY-MM-DD)

    Returns:
        Dictionary with revenue, expenses, net, and transaction counts

    Raises:
        OdooError: If summary generation fails
    """
    try:
        logger.info(f"Generating weekly summary for {week_start} to {week_end}")

        # Get all posted transactions for the week
        transactions = search_transactions(
            client,
            start_date=week_start,
            end_date=week_end,
            state='posted',
            limit=1000
        )

        # Calculate totals
        revenue = 0.0
        expenses = 0.0
        invoice_count = 0
        expense_count = 0
        payment_count = 0

        for txn in transactions:
            move_type = txn.get('move_type', '')
            amount = txn.get('amount_total', 0.0)

            if move_type == 'out_invoice':
                revenue += amount
                invoice_count += 1
            elif move_type == 'in_invoice':
                expenses += amount
                expense_count += 1
            elif move_type == 'payment':
                payment_count += 1

        net = revenue - expenses

        summary = {
            'period': {
                'start': week_start,
                'end': week_end
            },
            'revenue': round(revenue, 2),
            'expenses': round(expenses, 2),
            'net': round(net, 2),
            'counts': {
                'invoices': invoice_count,
                'expenses': expense_count,
                'payments': payment_count,
                'total': len(transactions)
            },
            'transactions': transactions
        }

        logger.info(f"Weekly summary: Revenue ${revenue:.2f}, Expenses ${expenses:.2f}, Net ${net:.2f}")
        return summary

    except Exception as e:
        logger.error(f"Failed to generate weekly summary: {e}")
        raise OdooError(f"Weekly summary generation failed: {e}") from e


def post_invoice(client: OdooClient, invoice_id: int) -> bool:
    """
    Post (validate) an invoice in Odoo

    Args:
        client: Authenticated OdooClient instance
        invoice_id: Invoice ID to post

    Returns:
        True if successful

    Raises:
        OdooError: If posting fails
    """
    try:
        logger.info(f"Posting invoice {invoice_id}")

        # Call action_post method on the invoice
        result = client.call('account.move', 'action_post', [[invoice_id]])

        logger.info(f"Invoice {invoice_id} posted successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to post invoice {invoice_id}: {e}")
        raise OdooError(f"Invoice posting failed: {e}") from e


def cancel_invoice(client: OdooClient, invoice_id: int) -> bool:
    """
    Cancel an invoice in Odoo

    Args:
        client: Authenticated OdooClient instance
        invoice_id: Invoice ID to cancel

    Returns:
        True if successful

    Raises:
        OdooError: If cancellation fails
    """
    try:
        logger.info(f"Cancelling invoice {invoice_id}")

        # Call button_cancel method on the invoice
        result = client.call('account.move', 'button_cancel', [[invoice_id]])

        logger.info(f"Invoice {invoice_id} cancelled successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to cancel invoice {invoice_id}: {e}")
        raise OdooError(f"Invoice cancellation failed: {e}") from e

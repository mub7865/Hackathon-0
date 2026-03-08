"""
Accounting MCP Server
Exposes accounting operations (invoices, payments, expenses) as MCP tools
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.actions.accounting_actions import (
    process_invoice_request,
    process_payment_request,
    process_expense_request,
    process_approved_transaction,
    get_pending_approvals
)
from src.utils.odoo_client import OdooClient
from src.utils.odoo_methods import get_weekly_summary, search_transactions
from src.models.transaction import TransactionType
from src.utils.security_utils import (
    validate_transaction_data,
    validate_date,
    validate_integer_id,
    sanitize_file_path,
    check_rate_limit,
    SecurityValidationError
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AccountingMCPServer:
    """
    MCP Server for accounting operations

    Provides tools for:
    - Creating invoices
    - Recording payments
    - Creating expenses
    - Searching transactions
    - Getting weekly summaries
    - Managing approvals
    """

    def __init__(self, vault_path: Optional[str] = None):
        """
        Initialize Accounting MCP Server

        Args:
            vault_path: Path to vault directory (optional)
        """
        self.vault_path = vault_path or os.getenv('VAULT_PATH', str(Path(__file__).parent.parent.parent / 'vault'))
        self.vault_path = Path(self.vault_path)

        logger.info(f"Initialized Accounting MCP Server with vault: {self.vault_path}")

    def get_tools(self) -> List[Dict[str, Any]]:
        """
        Get list of available MCP tools

        Returns:
            List of tool definitions
        """
        return [
            {
                "name": "create_invoice",
                "description": "Create a customer invoice in Odoo. Requires approval if amount exceeds $100.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "customer_name": {
                            "type": "string",
                            "description": "Customer name"
                        },
                        "customer_id": {
                            "type": "integer",
                            "description": "Odoo customer/partner ID (optional)"
                        },
                        "amount": {
                            "type": "number",
                            "description": "Invoice amount in USD"
                        },
                        "description": {
                            "type": "string",
                            "description": "Invoice description/line item"
                        },
                        "invoice_date": {
                            "type": "string",
                            "description": "Invoice date (YYYY-MM-DD format, optional, defaults to today)"
                        }
                    },
                    "required": ["customer_name", "amount", "description"]
                }
            },
            {
                "name": "record_payment",
                "description": "Record a customer payment in Odoo. Requires approval if amount exceeds $100.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "customer_name": {
                            "type": "string",
                            "description": "Customer name"
                        },
                        "customer_id": {
                            "type": "integer",
                            "description": "Odoo customer/partner ID (optional)"
                        },
                        "amount": {
                            "type": "number",
                            "description": "Payment amount in USD"
                        },
                        "description": {
                            "type": "string",
                            "description": "Payment reference/description"
                        },
                        "payment_date": {
                            "type": "string",
                            "description": "Payment date (YYYY-MM-DD format, optional, defaults to today)"
                        }
                    },
                    "required": ["customer_name", "amount", "description"]
                }
            },
            {
                "name": "create_expense",
                "description": "Create a vendor bill/expense in Odoo. Requires approval if amount exceeds $100.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "vendor_name": {
                            "type": "string",
                            "description": "Vendor name"
                        },
                        "vendor_id": {
                            "type": "integer",
                            "description": "Odoo vendor/partner ID (optional)"
                        },
                        "amount": {
                            "type": "number",
                            "description": "Expense amount in USD"
                        },
                        "category": {
                            "type": "string",
                            "description": "Expense category (e.g., Software Subscriptions, Office Supplies)"
                        },
                        "description": {
                            "type": "string",
                            "description": "Expense description"
                        },
                        "expense_date": {
                            "type": "string",
                            "description": "Expense date (YYYY-MM-DD format, optional, defaults to today)"
                        }
                    },
                    "required": ["vendor_name", "amount", "category", "description"]
                }
            },
            {
                "name": "search_transactions",
                "description": "Search for transactions in Odoo by date range, type, or partner.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "start_date": {
                            "type": "string",
                            "description": "Start date (YYYY-MM-DD format, optional)"
                        },
                        "end_date": {
                            "type": "string",
                            "description": "End date (YYYY-MM-DD format, optional)"
                        },
                        "transaction_type": {
                            "type": "string",
                            "enum": ["invoice", "payment", "expense"],
                            "description": "Filter by transaction type (optional)"
                        },
                        "partner_id": {
                            "type": "integer",
                            "description": "Filter by partner ID (optional)"
                        },
                        "state": {
                            "type": "string",
                            "enum": ["draft", "posted", "paid", "cancelled"],
                            "description": "Filter by state (optional)"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results (default: 100)"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "get_weekly_summary",
                "description": "Get weekly transaction summary for CEO briefing (revenue, expenses, net).",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "week_start": {
                            "type": "string",
                            "description": "Week start date (YYYY-MM-DD format)"
                        },
                        "week_end": {
                            "type": "string",
                            "description": "Week end date (YYYY-MM-DD format)"
                        }
                    },
                    "required": ["week_start", "week_end"]
                }
            },
            {
                "name": "get_pending_approvals",
                "description": "Get list of transactions pending human approval (amount > $100).",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "approve_transaction",
                "description": "Approve a pending transaction and execute it in Odoo.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "task_file": {
                            "type": "string",
                            "description": "Path to task file in Pending_Approval folder"
                        },
                        "approved_by": {
                            "type": "string",
                            "description": "Name of approver"
                        }
                    },
                    "required": ["task_file", "approved_by"]
                }
            }
        ]

    def handle_create_invoice(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle create_invoice tool call with security validation

        Args:
            arguments: Tool arguments

        Returns:
            Result dictionary
        """
        try:
            # Rate limiting
            is_allowed, error_msg = check_rate_limit('mcp_create_invoice')
            if not is_allowed:
                return {
                    "success": False,
                    "error": error_msg
                }

            # Validate and sanitize inputs
            invoice_date = arguments.get('invoice_date', datetime.now().strftime('%Y-%m-%d'))

            is_valid, error_msg, sanitized_data = validate_transaction_data(
                amount=arguments['amount'],
                party=arguments['customer_name'],
                description=arguments['description'],
                transaction_date=invoice_date
            )

            if not is_valid:
                return {
                    "success": False,
                    "error": f"Validation failed: {error_msg}"
                }

            # Validate customer_id if provided
            if 'customer_id' in arguments:
                is_valid, error_msg, customer_id = validate_integer_id(arguments['customer_id'], 'customer_id')
                if not is_valid:
                    return {
                        "success": False,
                        "error": error_msg
                    }
                sanitized_data['customer_id'] = customer_id

            # Create task file in Needs_Action folder
            task_file = self._create_task_file(
                action='invoice',
                party=sanitized_data['party'],
                party_id=sanitized_data.get('customer_id'),
                amount=sanitized_data['amount'],
                description=sanitized_data['description'],
                date=sanitized_data['date']
            )

            # Process invoice request
            status = process_invoice_request(task_file)

            if status == 'pending_approval':
                return {
                    "success": True,
                    "status": "pending_approval",
                    "message": f"Invoice for ${arguments['amount']:.2f} requires approval (threshold: $100)",
                    "task_file": task_file
                }
            elif status == 'done':
                return {
                    "success": True,
                    "status": "completed",
                    "message": f"Invoice created successfully for ${arguments['amount']:.2f}",
                    "task_file": task_file
                }
            else:
                return {
                    "success": False,
                    "status": "error",
                    "message": "Failed to create invoice",
                    "task_file": task_file
                }

        except Exception as e:
            logger.error(f"Error handling create_invoice: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def handle_record_payment(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle record_payment tool call with security validation

        Args:
            arguments: Tool arguments

        Returns:
            Result dictionary
        """
        try:
            # Rate limiting
            is_allowed, error_msg = check_rate_limit('mcp_record_payment')
            if not is_allowed:
                return {
                    "success": False,
                    "error": error_msg
                }

            # Validate and sanitize inputs
            payment_date = arguments.get('payment_date', datetime.now().strftime('%Y-%m-%d'))

            is_valid, error_msg, sanitized_data = validate_transaction_data(
                amount=arguments['amount'],
                party=arguments['customer_name'],
                description=arguments['description'],
                transaction_date=payment_date
            )

            if not is_valid:
                return {
                    "success": False,
                    "error": f"Validation failed: {error_msg}"
                }

            # Validate customer_id if provided
            if 'customer_id' in arguments:
                is_valid, error_msg, customer_id = validate_integer_id(arguments['customer_id'], 'customer_id')
                if not is_valid:
                    return {
                        "success": False,
                        "error": error_msg
                    }
                sanitized_data['customer_id'] = customer_id

            # Create task file in Needs_Action folder
            task_file = self._create_task_file(
                action='payment',
                party=sanitized_data['party'],
                party_id=sanitized_data.get('customer_id'),
                amount=sanitized_data['amount'],
                description=sanitized_data['description'],
                date=sanitized_data['date']
            )

            # Process payment request
            status = process_payment_request(task_file)

            if status == 'pending_approval':
                return {
                    "success": True,
                    "status": "pending_approval",
                    "message": f"Payment of ${arguments['amount']:.2f} requires approval (threshold: $100)",
                    "task_file": task_file
                }
            elif status == 'done':
                return {
                    "success": True,
                    "status": "completed",
                    "message": f"Payment recorded successfully for ${arguments['amount']:.2f}",
                    "task_file": task_file
                }
            else:
                return {
                    "success": False,
                    "status": "error",
                    "message": "Failed to record payment",
                    "task_file": task_file
                }

        except Exception as e:
            logger.error(f"Error handling record_payment: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def handle_create_expense(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle create_expense tool call with security validation

        Args:
            arguments: Tool arguments

        Returns:
            Result dictionary
        """
        try:
            # Rate limiting
            is_allowed, error_msg = check_rate_limit('mcp_create_expense')
            if not is_allowed:
                return {
                    "success": False,
                    "error": error_msg
                }

            # Validate and sanitize inputs
            expense_date = arguments.get('expense_date', datetime.now().strftime('%Y-%m-%d'))

            is_valid, error_msg, sanitized_data = validate_transaction_data(
                amount=arguments['amount'],
                party=arguments['vendor_name'],
                description=arguments['description'],
                transaction_date=expense_date,
                category=arguments['category']
            )

            if not is_valid:
                return {
                    "success": False,
                    "error": f"Validation failed: {error_msg}"
                }

            # Validate vendor_id if provided
            if 'vendor_id' in arguments:
                is_valid, error_msg, vendor_id = validate_integer_id(arguments['vendor_id'], 'vendor_id')
                if not is_valid:
                    return {
                        "success": False,
                        "error": error_msg
                    }
                sanitized_data['vendor_id'] = vendor_id

            # Create task file in Needs_Action folder
            task_file = self._create_task_file(
                action='expense',
                party=sanitized_data['party'],
                party_id=sanitized_data.get('vendor_id'),
                amount=sanitized_data['amount'],
                category=sanitized_data['category'],
                description=sanitized_data['description'],
                date=sanitized_data['date']
            )

            # Process expense request
            status = process_expense_request(task_file)

            if status == 'pending_approval':
                return {
                    "success": True,
                    "status": "pending_approval",
                    "message": f"Expense of ${arguments['amount']:.2f} requires approval (threshold: $100)",
                    "task_file": task_file
                }
            elif status == 'done':
                return {
                    "success": True,
                    "status": "completed",
                    "message": f"Expense created successfully for ${arguments['amount']:.2f}",
                    "task_file": task_file
                }
            else:
                return {
                    "success": False,
                    "status": "error",
                    "message": "Failed to create expense",
                    "task_file": task_file
                }

        except Exception as e:
            logger.error(f"Error handling create_expense: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def handle_search_transactions(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle search_transactions tool call with security validation

        Args:
            arguments: Tool arguments

        Returns:
            Result dictionary
        """
        try:
            # Rate limiting
            is_allowed, error_msg = check_rate_limit('mcp_search_transactions')
            if not is_allowed:
                return {
                    "success": False,
                    "error": error_msg
                }

            # Validate dates if provided
            if 'start_date' in arguments:
                is_valid, error_msg = validate_date(arguments['start_date'], 'start_date')
                if not is_valid:
                    return {
                        "success": False,
                        "error": error_msg
                    }

            if 'end_date' in arguments:
                is_valid, error_msg = validate_date(arguments['end_date'], 'end_date')
                if not is_valid:
                    return {
                        "success": False,
                        "error": error_msg
                    }

            # Validate partner_id if provided
            if 'partner_id' in arguments:
                is_valid, error_msg, partner_id = validate_integer_id(arguments['partner_id'], 'partner_id')
                if not is_valid:
                    return {
                        "success": False,
                        "error": error_msg
                    }
                arguments['partner_id'] = partner_id

            # Validate limit
            limit = arguments.get('limit', 100)
            if not isinstance(limit, int) or limit < 1 or limit > 1000:
                return {
                    "success": False,
                    "error": "Limit must be between 1 and 1000"
                }

            # Connect to Odoo
            client = OdooClient()
            client.authenticate()

            # Map transaction type string to enum
            transaction_type = None
            if arguments.get('transaction_type'):
                type_map = {
                    'invoice': TransactionType.INVOICE,
                    'payment': TransactionType.PAYMENT,
                    'expense': TransactionType.EXPENSE
                }
                transaction_type = type_map.get(arguments['transaction_type'])

            # Search transactions
            results = search_transactions(
                client,
                start_date=arguments.get('start_date'),
                end_date=arguments.get('end_date'),
                transaction_type=transaction_type,
                partner_id=arguments.get('partner_id'),
                state=arguments.get('state'),
                limit=limit
            )

            client.close()

            return {
                "success": True,
                "count": len(results),
                "transactions": results
            }

        except Exception as e:
            logger.error(f"Error handling search_transactions: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def handle_get_weekly_summary(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle get_weekly_summary tool call with security validation

        Args:
            arguments: Tool arguments

        Returns:
            Result dictionary
        """
        try:
            # Rate limiting
            is_allowed, error_msg = check_rate_limit('mcp_get_weekly_summary')
            if not is_allowed:
                return {
                    "success": False,
                    "error": error_msg
                }

            # Validate dates
            is_valid, error_msg = validate_date(arguments['week_start'], 'week_start')
            if not is_valid:
                return {
                    "success": False,
                    "error": error_msg
                }

            is_valid, error_msg = validate_date(arguments['week_end'], 'week_end')
            if not is_valid:
                return {
                    "success": False,
                    "error": error_msg
                }

            # Connect to Odoo
            client = OdooClient()
            client.authenticate()

            # Get weekly summary
            summary = get_weekly_summary(
                client,
                week_start=arguments['week_start'],
                week_end=arguments['week_end']
            )

            client.close()

            return {
                "success": True,
                "summary": summary
            }

        except Exception as e:
            logger.error(f"Error handling get_weekly_summary: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def handle_get_pending_approvals(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle get_pending_approvals tool call

        Args:
            arguments: Tool arguments (empty)

        Returns:
            Result dictionary
        """
        try:
            pending = get_pending_approvals(str(self.vault_path))

            # Parse each pending file to get details
            pending_details = []
            for task_file in pending:
                from src.utils.file_utils import parse_task_file
                frontmatter, body = parse_task_file(task_file)

                pending_details.append({
                    'task_file': task_file,
                    'amount': frontmatter.get('transaction_amount', 0),
                    'party': frontmatter.get('transaction_party', 'Unknown'),
                    'action': frontmatter.get('action', 'unknown'),
                    'reason': frontmatter.get('approval_reason', ''),
                    'requested_at': frontmatter.get('approval_requested_at', '')
                })

            return {
                "success": True,
                "count": len(pending_details),
                "pending_approvals": pending_details
            }

        except Exception as e:
            logger.error(f"Error handling get_pending_approvals: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def handle_approve_transaction(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle approve_transaction tool call with security validation

        Args:
            arguments: Tool arguments

        Returns:
            Result dictionary
        """
        try:
            # Rate limiting
            is_allowed, error_msg = check_rate_limit('mcp_approve_transaction')
            if not is_allowed:
                return {
                    "success": False,
                    "error": error_msg
                }

            # Sanitize file path
            task_file = arguments['task_file']
            is_valid, error_msg, sanitized_path = sanitize_file_path(task_file, str(self.vault_path))
            if not is_valid:
                return {
                    "success": False,
                    "error": f"Invalid file path: {error_msg}"
                }
            task_file = sanitized_path

            # Validate approved_by
            from src.utils.security_utils import sanitize_text
            is_valid, error_msg, approved_by = sanitize_text(arguments['approved_by'], 'approved_by', 100)
            if not is_valid:
                return {
                    "success": False,
                    "error": error_msg
                }

            # Update task with approval
            from src.utils.file_utils import update_task_frontmatter, move_task_file
            update_task_frontmatter(
                task_file,
                {
                    'status': 'approved',
                    'approved_by': approved_by,
                    'approved_at': datetime.now().isoformat()
                }
            )

            # Move to Approved folder
            approved_path = move_task_file(task_file, 'Approved')

            # Process approved transaction
            status = process_approved_transaction(approved_path)

            if status == 'done':
                return {
                    "success": True,
                    "status": "completed",
                    "message": f"Transaction approved and executed successfully",
                    "task_file": approved_path
                }
            else:
                return {
                    "success": False,
                    "status": "error",
                    "message": "Failed to execute approved transaction",
                    "task_file": approved_path
                }

        except Exception as e:
            logger.error(f"Error handling approve_transaction: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _create_task_file(
        self,
        action: str,
        party: str,
        amount: float,
        description: str,
        date: str,
        party_id: Optional[int] = None,
        category: Optional[str] = None
    ) -> str:
        """
        Create task file in Needs_Action folder

        Args:
            action: Action type (invoice, payment, expense)
            party: Customer/vendor name
            amount: Transaction amount
            description: Transaction description
            date: Transaction date (YYYY-MM-DD)
            party_id: Odoo partner ID (optional)
            category: Expense category (optional)

        Returns:
            Path to created task file
        """
        import yaml

        # Create Needs_Action folder if not exists
        needs_action = self.vault_path / 'Needs_Action'
        needs_action.mkdir(parents=True, exist_ok=True)

        # Generate task filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{action}_{party.replace(' ', '_')}_{timestamp}.md"
        task_file = needs_action / filename

        # Create frontmatter
        frontmatter = {
            'title': f"{action.capitalize()} - {party}",
            'type': 'accounting',
            'action': action,
            'party': party,
            'amount': amount,
            'date': date,
            'description': description,
            'status': 'needs_action',
            'created': datetime.now().isoformat(),
            'priority': 'medium'
        }

        if party_id:
            frontmatter['party_id'] = party_id
        if category:
            frontmatter['category'] = category

        # Create task file content
        content = "---\n"
        content += yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)
        content += "---\n\n"
        content += f"# {action.capitalize()} Request\n\n"
        content += f"**Party**: {party}\n"
        content += f"**Amount**: ${amount:.2f}\n"
        content += f"**Date**: {date}\n"
        content += f"**Description**: {description}\n"
        if category:
            content += f"**Category**: {category}\n"

        # Write task file
        with open(task_file, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"Created task file: {task_file}")
        return str(task_file)

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a tool by name

        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments

        Returns:
            Tool result
        """
        handlers = {
            'create_invoice': self.handle_create_invoice,
            'record_payment': self.handle_record_payment,
            'create_expense': self.handle_create_expense,
            'search_transactions': self.handle_search_transactions,
            'get_weekly_summary': self.handle_get_weekly_summary,
            'get_pending_approvals': self.handle_get_pending_approvals,
            'approve_transaction': self.handle_approve_transaction
        }

        handler = handlers.get(tool_name)
        if not handler:
            return {
                "success": False,
                "error": f"Unknown tool: {tool_name}"
            }

        return handler(arguments)


def main():
    """Main entry point for MCP server"""
    server = AccountingMCPServer()

    # Print available tools
    print("Accounting MCP Server")
    print("=" * 50)
    print(f"Vault Path: {server.vault_path}")
    print(f"\nAvailable Tools ({len(server.get_tools())}):")
    for tool in server.get_tools():
        print(f"  - {tool['name']}: {tool['description']}")
    print("\nServer ready.")


if __name__ == '__main__':
    main()

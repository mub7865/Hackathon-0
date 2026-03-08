"""
Integration tests for Accounting Workflow
Tests end-to-end accounting task processing with approval workflow
"""

import unittest
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, Mock
from datetime import datetime
import yaml

from src.actions.accounting_actions import (
    process_invoice_request,
    process_payment_request,
    process_expense_request,
    process_approved_transaction,
    get_pending_approvals
)
from src.models.transaction import BusinessTransaction, TransactionType, TransactionStatus
from src.orchestrator.accounting_orchestrator import AccountingOrchestrator


class TestAccountingWorkflow(unittest.TestCase):
    """Integration tests for accounting workflow"""

    def setUp(self):
        """Set up test fixtures"""
        # Create temporary vault directory
        self.test_vault = tempfile.mkdtemp()
        self.vault_path = Path(self.test_vault)

        # Create vault structure
        (self.vault_path / 'Needs_Action').mkdir(parents=True)
        (self.vault_path / 'Pending_Approval').mkdir(parents=True)
        (self.vault_path / 'Approved').mkdir(parents=True)
        (self.vault_path / 'Done').mkdir(parents=True)
        (self.vault_path / 'Logs').mkdir(parents=True)

        # Mock environment
        self.env_patcher = patch.dict('os.environ', {
            'VAULT_PATH': str(self.vault_path),
            'ODOO_URL': 'http://localhost:8069',
            'ODOO_DB': 'test_db',
            'ODOO_USERNAME': 'admin',
            'ODOO_PASSWORD': 'admin'
        })
        self.env_patcher.start()

    def tearDown(self):
        """Clean up after tests"""
        self.env_patcher.stop()
        # Remove temporary vault
        shutil.rmtree(self.test_vault)

    def _create_test_task(
        self,
        action: str,
        party: str,
        amount: float,
        description: str,
        folder: str = 'Needs_Action'
    ) -> str:
        """
        Create a test task file

        Args:
            action: Action type (invoice, payment, expense)
            party: Customer/vendor name
            amount: Transaction amount
            description: Transaction description
            folder: Folder to create task in

        Returns:
            Path to created task file
        """
        # Create task file
        task_folder = self.vault_path / folder
        task_file = task_folder / f"{action}_{party.replace(' ', '_')}_test.md"

        # Create frontmatter
        frontmatter = {
            'title': f"{action.capitalize()} - {party}",
            'type': 'accounting',
            'action': action,
            'party': party,
            'amount': amount,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'description': description,
            'status': 'needs_action',
            'created': datetime.now().isoformat(),
            'priority': 'medium'
        }

        # Create task file content
        content = "---\n"
        content += yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)
        content += "---\n\n"
        content += f"# {action.capitalize()} Request\n\n"
        content += f"**Party**: {party}\n"
        content += f"**Amount**: ${amount:.2f}\n"
        content += f"**Description**: {description}\n"

        # Write task file
        with open(task_file, 'w', encoding='utf-8') as f:
            f.write(content)

        return str(task_file)

    @patch('src.utils.odoo_client.OdooClient')
    def test_invoice_under_threshold(self, mock_client_class):
        """Test invoice creation under approval threshold ($100)"""
        # Mock Odoo client
        mock_client = Mock()
        mock_client.authenticate.return_value = 2
        mock_client_class.return_value = mock_client

        # Mock create_invoice to return success
        with patch('src.actions.accounting_actions._execute_transaction') as mock_execute:
            mock_execute.return_value = {
                'invoice_id': 42,
                'invoice_name': 'INV/2026/0042',
                'odoo_url': 'http://localhost:8069/web#id=42'
            }

            # Create test task (under threshold)
            task_file = self._create_test_task(
                action='invoice',
                party='Test Customer',
                amount=50.00,
                description='Test invoice under threshold'
            )

            # Process invoice
            status = process_invoice_request(task_file)

            # Verify
            self.assertEqual(status, 'done')

            # Verify task moved to Done folder
            done_files = list((self.vault_path / 'Done').glob('*.md'))
            self.assertEqual(len(done_files), 1)

            # Verify no files in Pending_Approval
            pending_files = list((self.vault_path / 'Pending_Approval').glob('*.md'))
            self.assertEqual(len(pending_files), 0)

    def test_invoice_over_threshold(self):
        """Test invoice creation over approval threshold ($100)"""
        # Create test task (over threshold)
        task_file = self._create_test_task(
            action='invoice',
            party='Big Customer',
            amount=500.00,
            description='Test invoice over threshold'
        )

        # Process invoice
        status = process_invoice_request(task_file)

        # Verify
        self.assertEqual(status, 'pending_approval')

        # Verify task moved to Pending_Approval folder
        pending_files = list((self.vault_path / 'Pending_Approval').glob('*.md'))
        self.assertEqual(len(pending_files), 1)

        # Verify no files in Done
        done_files = list((self.vault_path / 'Done').glob('*.md'))
        self.assertEqual(len(done_files), 0)

    @patch('src.utils.odoo_client.OdooClient')
    def test_payment_under_threshold(self, mock_client_class):
        """Test payment recording under approval threshold"""
        # Mock Odoo client
        mock_client = Mock()
        mock_client.authenticate.return_value = 2
        mock_client_class.return_value = mock_client

        # Mock record_payment to return success
        with patch('src.actions.accounting_actions._execute_transaction') as mock_execute:
            mock_execute.return_value = {
                'payment_id': 15,
                'payment_name': 'PAY/2026/0015',
                'odoo_url': 'http://localhost:8069/web#id=15'
            }

            # Create test task (under threshold)
            task_file = self._create_test_task(
                action='payment',
                party='Test Customer',
                amount=75.00,
                description='Test payment under threshold'
            )

            # Process payment
            status = process_payment_request(task_file)

            # Verify
            self.assertEqual(status, 'done')

            # Verify task moved to Done folder
            done_files = list((self.vault_path / 'Done').glob('*.md'))
            self.assertEqual(len(done_files), 1)

    @patch('src.utils.odoo_client.OdooClient')
    def test_expense_under_threshold(self, mock_client_class):
        """Test expense creation under approval threshold"""
        # Mock Odoo client
        mock_client = Mock()
        mock_client.authenticate.return_value = 2
        mock_client_class.return_value = mock_client

        # Mock create_expense to return success
        with patch('src.actions.accounting_actions._execute_transaction') as mock_execute:
            mock_execute.return_value = {
                'expense_id': 43,
                'expense_name': 'BILL/2026/0043',
                'odoo_url': 'http://localhost:8069/web#id=43'
            }

            # Create test task (under threshold)
            task_file = self._create_test_task(
                action='expense',
                party='Software Vendor',
                amount=49.99,
                description='Monthly subscription'
            )

            # Process expense
            status = process_expense_request(task_file)

            # Verify
            self.assertEqual(status, 'done')

            # Verify task moved to Done folder
            done_files = list((self.vault_path / 'Done').glob('*.md'))
            self.assertEqual(len(done_files), 1)

    @patch('src.utils.odoo_client.OdooClient')
    def test_approved_transaction_workflow(self, mock_client_class):
        """Test processing of approved transaction"""
        # Mock Odoo client
        mock_client = Mock()
        mock_client.authenticate.return_value = 2
        mock_client_class.return_value = mock_client

        # Mock execute_transaction to return success
        with patch('src.actions.accounting_actions._execute_transaction') as mock_execute:
            mock_execute.return_value = {
                'invoice_id': 44,
                'invoice_name': 'INV/2026/0044',
                'odoo_url': 'http://localhost:8069/web#id=44'
            }

            # Create test task in Approved folder
            task_file = self._create_test_task(
                action='invoice',
                party='Approved Customer',
                amount=1000.00,
                description='Approved large invoice',
                folder='Approved'
            )

            # Add approval metadata
            from src.utils.file_utils import update_task_frontmatter
            update_task_frontmatter(
                task_file,
                {
                    'status': 'approved',
                    'approved_by': 'CEO',
                    'approved_at': datetime.now().isoformat()
                }
            )

            # Process approved transaction
            status = process_approved_transaction(task_file)

            # Verify
            self.assertEqual(status, 'done')

            # Verify task moved to Done folder
            done_files = list((self.vault_path / 'Done').glob('*.md'))
            self.assertEqual(len(done_files), 1)

    def test_get_pending_approvals(self):
        """Test getting list of pending approvals"""
        # Create multiple pending approval tasks
        for i in range(3):
            self._create_test_task(
                action='invoice',
                party=f'Customer {i}',
                amount=200.00 + (i * 100),
                description=f'Invoice {i}',
                folder='Pending_Approval'
            )

        # Get pending approvals
        pending = get_pending_approvals(str(self.vault_path))

        # Verify
        self.assertEqual(len(pending), 3)

    @patch('src.utils.odoo_client.OdooClient')
    def test_orchestrator_cycle(self, mock_client_class):
        """Test full orchestrator cycle"""
        # Mock Odoo client
        mock_client = Mock()
        mock_client.authenticate.return_value = 2
        mock_client_class.return_value = mock_client

        # Mock execute_transaction to return success
        with patch('src.actions.accounting_actions._execute_transaction') as mock_execute:
            mock_execute.return_value = {
                'invoice_id': 45,
                'invoice_name': 'INV/2026/0045',
                'odoo_url': 'http://localhost:8069/web#id=45'
            }

            # Create test tasks
            # 1. Invoice under threshold (should complete)
            self._create_test_task(
                action='invoice',
                party='Small Customer',
                amount=50.00,
                description='Small invoice'
            )

            # 2. Invoice over threshold (should go to pending approval)
            self._create_test_task(
                action='invoice',
                party='Large Customer',
                amount=500.00,
                description='Large invoice'
            )

            # 3. Approved transaction
            approved_task = self._create_test_task(
                action='payment',
                party='Approved Customer',
                amount=300.00,
                description='Approved payment',
                folder='Approved'
            )

            # Add approval metadata
            from src.utils.file_utils import update_task_frontmatter
            update_task_frontmatter(
                approved_task,
                {
                    'status': 'approved',
                    'approved_by': 'Manager',
                    'approved_at': datetime.now().isoformat()
                }
            )

            # Create orchestrator
            orchestrator = AccountingOrchestrator(str(self.vault_path))

            # Run cycle
            results = orchestrator.run_cycle()

            # Verify results
            self.assertEqual(results['tasks_processed'], 2)  # 2 from Needs_Action
            self.assertEqual(results['tasks_approved'], 1)   # 1 from Approved
            self.assertEqual(results['tasks_completed'], 2)  # 1 under threshold + 1 approved
            self.assertEqual(results['tasks_pending_approval'], 1)  # 1 over threshold
            self.assertEqual(results['tasks_failed'], 0)

            # Verify folder states
            needs_action_files = list((self.vault_path / 'Needs_Action').glob('*.md'))
            self.assertEqual(len(needs_action_files), 0)

            pending_files = list((self.vault_path / 'Pending_Approval').glob('*.md'))
            self.assertEqual(len(pending_files), 1)

            approved_files = list((self.vault_path / 'Approved').glob('*.md'))
            self.assertEqual(len(approved_files), 0)

            done_files = list((self.vault_path / 'Done').glob('*.md'))
            self.assertEqual(len(done_files), 2)

    @patch('src.utils.odoo_client.OdooClient')
    def test_error_handling(self, mock_client_class):
        """Test error handling in workflow"""
        # Mock Odoo client to raise error
        mock_client = Mock()
        mock_client.authenticate.side_effect = Exception('Connection failed')
        mock_client_class.return_value = mock_client

        # Create test task
        task_file = self._create_test_task(
            action='invoice',
            party='Test Customer',
            amount=50.00,
            description='Test invoice'
        )

        # Process invoice (should handle error)
        status = process_invoice_request(task_file)

        # Verify error status
        self.assertEqual(status, 'error')

        # Verify error logged
        error_log = self.vault_path / 'Logs' / 'errors.json'
        self.assertTrue(error_log.exists())

    def test_transaction_validation(self):
        """Test transaction validation"""
        from src.models.transaction import validate_transaction

        # Valid transaction
        valid_txn = BusinessTransaction(
            transaction_type=TransactionType.INVOICE,
            amount=100.00,
            party='Test Customer',
            description='Test invoice'
        )
        is_valid, error = validate_transaction(valid_txn)
        self.assertTrue(is_valid)
        self.assertIsNone(error)

        # Invalid: zero amount
        invalid_amount = BusinessTransaction(
            transaction_type=TransactionType.INVOICE,
            amount=0.00,
            party='Test Customer',
            description='Test invoice'
        )
        is_valid, error = validate_transaction(invalid_amount)
        self.assertFalse(is_valid)
        self.assertIn('Amount', error)

        # Invalid: missing party
        invalid_party = BusinessTransaction(
            transaction_type=TransactionType.INVOICE,
            amount=100.00,
            party='',
            description='Test invoice'
        )
        is_valid, error = validate_transaction(invalid_party)
        self.assertFalse(is_valid)
        self.assertIn('Party', error)

        # Invalid: missing description
        invalid_desc = BusinessTransaction(
            transaction_type=TransactionType.INVOICE,
            amount=100.00,
            party='Test Customer',
            description=''
        )
        is_valid, error = validate_transaction(invalid_desc)
        self.assertFalse(is_valid)
        self.assertIn('Description', error)

    def test_approval_threshold_check(self):
        """Test approval threshold logic"""
        from src.actions.accounting_actions import _check_approval_threshold

        # Under threshold
        under = BusinessTransaction(
            transaction_type=TransactionType.INVOICE,
            amount=99.99,
            approval_threshold=100.00
        )
        self.assertFalse(_check_approval_threshold(under))

        # At threshold
        at = BusinessTransaction(
            transaction_type=TransactionType.INVOICE,
            amount=100.00,
            approval_threshold=100.00
        )
        self.assertFalse(_check_approval_threshold(at))

        # Over threshold
        over = BusinessTransaction(
            transaction_type=TransactionType.INVOICE,
            amount=100.01,
            approval_threshold=100.00
        )
        self.assertTrue(_check_approval_threshold(over))


class TestAccountingWorkflowEndToEnd(unittest.TestCase):
    """End-to-end tests for accounting workflow (requires Odoo)"""

    @unittest.skip("Requires running Odoo instance")
    def test_full_invoice_workflow(self):
        """Test complete invoice workflow with real Odoo"""
        # This test requires a running Odoo instance
        # Uncomment and configure when testing against real Odoo

        # Create temporary vault
        test_vault = tempfile.mkdtemp()
        vault_path = Path(test_vault)

        try:
            # Create vault structure
            (vault_path / 'Needs_Action').mkdir(parents=True)
            (vault_path / 'Pending_Approval').mkdir(parents=True)
            (vault_path / 'Done').mkdir(parents=True)

            # Set environment
            os.environ['VAULT_PATH'] = str(vault_path)

            # Create test task
            task_file = vault_path / 'Needs_Action' / 'test_invoice.md'
            frontmatter = {
                'title': 'Test Invoice',
                'type': 'accounting',
                'action': 'invoice',
                'party': 'Test Customer',
                'party_id': 1,
                'amount': 50.00,
                'date': datetime.now().strftime('%Y-%m-%d'),
                'description': 'Test invoice',
                'status': 'needs_action',
                'created': datetime.now().isoformat()
            }

            content = "---\n"
            content += yaml.dump(frontmatter, default_flow_style=False)
            content += "---\n\n# Test Invoice\n"

            with open(task_file, 'w') as f:
                f.write(content)

            # Process invoice
            status = process_invoice_request(str(task_file))

            # Verify
            self.assertEqual(status, 'done')

            # Verify task moved to Done
            done_files = list((vault_path / 'Done').glob('*.md'))
            self.assertEqual(len(done_files), 1)

        finally:
            # Clean up
            shutil.rmtree(test_vault)


if __name__ == '__main__':
    unittest.main()

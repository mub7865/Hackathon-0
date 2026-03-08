"""
Accounting Orchestrator Integration
Detects and processes accounting tasks from vault/Needs_Action folder
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.actions.accounting_actions import (
    process_invoice_request,
    process_payment_request,
    process_expense_request,
    process_approved_transaction,
    get_pending_approvals
)
from src.utils.file_utils import parse_task_file
from src.utils.dashboard_utils import update_dashboard, get_task_counts
from src.utils.error_utils import should_alert_human, create_error_alert, get_recent_errors

logger = logging.getLogger(__name__)


class AccountingOrchestrator:
    """
    Orchestrator for accounting task processing

    Responsibilities:
    - Scan vault/Needs_Action for accounting tasks
    - Route tasks to appropriate handlers (invoice, payment, expense)
    - Process approved transactions from vault/Approved
    - Update dashboard with accounting metrics
    - Alert human for errors or pending approvals
    """

    def __init__(self, vault_path: Optional[str] = None):
        """
        Initialize Accounting Orchestrator

        Args:
            vault_path: Path to vault directory (optional)
        """
        self.vault_path = vault_path or os.getenv('VAULT_PATH', str(Path(__file__).parent.parent.parent / 'vault'))
        self.vault_path = Path(self.vault_path)

        # Ensure vault folders exist
        self._ensure_vault_structure()

        logger.info(f"Initialized Accounting Orchestrator with vault: {self.vault_path}")

    def _ensure_vault_structure(self) -> None:
        """Ensure required vault folders exist"""
        folders = ['Needs_Action', 'Pending_Approval', 'Approved', 'Done', 'Logs']
        for folder in folders:
            (self.vault_path / folder).mkdir(parents=True, exist_ok=True)

    def scan_needs_action(self) -> List[str]:
        """
        Scan Needs_Action folder for accounting tasks

        Returns:
            List of accounting task file paths
        """
        needs_action = self.vault_path / 'Needs_Action'

        if not needs_action.exists():
            return []

        # Get all .md files
        all_tasks = list(needs_action.glob('*.md'))

        # Filter for accounting tasks
        accounting_tasks = []
        for task_file in all_tasks:
            try:
                frontmatter, _ = parse_task_file(str(task_file))

                # Check if it's an accounting task
                task_type = frontmatter.get('type', '')
                action = frontmatter.get('action', '')

                if task_type == 'accounting' or action in ['invoice', 'payment', 'expense']:
                    accounting_tasks.append(str(task_file))

            except Exception as e:
                logger.warning(f"Failed to parse task file {task_file}: {e}")
                continue

        logger.info(f"Found {len(accounting_tasks)} accounting tasks in Needs_Action")
        return accounting_tasks

    def scan_approved(self) -> List[str]:
        """
        Scan Approved folder for accounting tasks

        Returns:
            List of approved accounting task file paths
        """
        approved = self.vault_path / 'Approved'

        if not approved.exists():
            return []

        # Get all .md files
        all_tasks = list(approved.glob('*.md'))

        # Filter for accounting tasks
        accounting_tasks = []
        for task_file in all_tasks:
            try:
                frontmatter, _ = parse_task_file(str(task_file))

                # Check if it's an accounting task
                task_type = frontmatter.get('type', '')
                action = frontmatter.get('action', '')

                if task_type == 'accounting' or action in ['invoice', 'payment', 'expense']:
                    accounting_tasks.append(str(task_file))

            except Exception as e:
                logger.warning(f"Failed to parse approved task file {task_file}: {e}")
                continue

        logger.info(f"Found {len(accounting_tasks)} approved accounting tasks")
        return accounting_tasks

    def process_task(self, task_file: str) -> Dict[str, Any]:
        """
        Process a single accounting task

        Args:
            task_file: Path to task file

        Returns:
            Processing result dictionary
        """
        try:
            logger.info(f"Processing accounting task: {task_file}")

            # Parse task file
            frontmatter, _ = parse_task_file(task_file)
            action = frontmatter.get('action', '')

            # Route to appropriate handler
            if action == 'invoice':
                status = process_invoice_request(task_file)
            elif action == 'payment':
                status = process_payment_request(task_file)
            elif action == 'expense':
                status = process_expense_request(task_file)
            else:
                logger.error(f"Unknown action type: {action}")
                return {
                    'success': False,
                    'task_file': task_file,
                    'error': f"Unknown action type: {action}"
                }

            return {
                'success': True,
                'task_file': task_file,
                'action': action,
                'status': status
            }

        except Exception as e:
            logger.error(f"Failed to process task {task_file}: {e}")
            return {
                'success': False,
                'task_file': task_file,
                'error': str(e)
            }

    def process_approved_task(self, task_file: str) -> Dict[str, Any]:
        """
        Process an approved accounting task

        Args:
            task_file: Path to approved task file

        Returns:
            Processing result dictionary
        """
        try:
            logger.info(f"Processing approved accounting task: {task_file}")

            status = process_approved_transaction(task_file)

            return {
                'success': True,
                'task_file': task_file,
                'status': status
            }

        except Exception as e:
            logger.error(f"Failed to process approved task {task_file}: {e}")
            return {
                'success': False,
                'task_file': task_file,
                'error': str(e)
            }

    def run_cycle(self) -> Dict[str, Any]:
        """
        Run one orchestrator cycle

        Workflow:
        1. Scan Needs_Action for accounting tasks
        2. Process each task (with approval workflow)
        3. Scan Approved for approved tasks
        4. Process approved tasks
        5. Update dashboard with metrics
        6. Check for errors and alert if needed

        Returns:
            Cycle summary dictionary
        """
        cycle_start = datetime.now()
        logger.info("=" * 60)
        logger.info(f"Starting accounting orchestrator cycle at {cycle_start.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60)

        results = {
            'cycle_start': cycle_start.isoformat(),
            'tasks_processed': 0,
            'tasks_approved': 0,
            'tasks_completed': 0,
            'tasks_pending_approval': 0,
            'tasks_failed': 0,
            'errors': []
        }

        # 1. Process Needs_Action tasks
        needs_action_tasks = self.scan_needs_action()
        logger.info(f"Processing {len(needs_action_tasks)} tasks from Needs_Action")

        for task_file in needs_action_tasks:
            result = self.process_task(task_file)
            results['tasks_processed'] += 1

            if result['success']:
                status = result.get('status', '')
                if status == 'done':
                    results['tasks_completed'] += 1
                elif status == 'pending_approval':
                    results['tasks_pending_approval'] += 1
            else:
                results['tasks_failed'] += 1
                results['errors'].append({
                    'task_file': task_file,
                    'error': result.get('error', 'Unknown error')
                })

        # 2. Process Approved tasks
        approved_tasks = self.scan_approved()
        logger.info(f"Processing {len(approved_tasks)} approved tasks")

        for task_file in approved_tasks:
            result = self.process_approved_task(task_file)
            results['tasks_approved'] += 1

            if result['success']:
                if result.get('status') == 'done':
                    results['tasks_completed'] += 1
            else:
                results['tasks_failed'] += 1
                results['errors'].append({
                    'task_file': task_file,
                    'error': result.get('error', 'Unknown error')
                })

        # 3. Update dashboard
        self._update_dashboard(results)

        # 4. Check for errors and alert
        self._check_errors()

        cycle_end = datetime.now()
        cycle_duration = (cycle_end - cycle_start).total_seconds()
        results['cycle_end'] = cycle_end.isoformat()
        results['cycle_duration_seconds'] = cycle_duration

        logger.info("=" * 60)
        logger.info(f"Cycle completed in {cycle_duration:.2f}s")
        logger.info(f"  Processed: {results['tasks_processed']}")
        logger.info(f"  Completed: {results['tasks_completed']}")
        logger.info(f"  Pending Approval: {results['tasks_pending_approval']}")
        logger.info(f"  Failed: {results['tasks_failed']}")
        logger.info("=" * 60)

        return results

    def _update_dashboard(self, cycle_results: Dict[str, Any]) -> None:
        """
        Update dashboard with accounting metrics

        Args:
            cycle_results: Results from current cycle
        """
        try:
            # Get task counts
            task_counts = get_task_counts(str(self.vault_path))

            # Get pending approvals
            pending_approvals = get_pending_approvals(str(self.vault_path))

            # Update dashboard
            update_dashboard(
                str(self.vault_path),
                {
                    'task_statistics': task_counts,
                    'orchestrator_status': {
                        'current_cycle': 1,  # Would be tracked in persistent state
                        'last_run': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'status': 'Running',
                        'today_stats': {
                            'tasks_processed': cycle_results['tasks_processed'],
                            'tasks_approved': cycle_results['tasks_approved'],
                            'tasks_rejected': 0,  # Not implemented yet
                            'errors': cycle_results['tasks_failed']
                        }
                    },
                    'recent_activity': [
                        {
                            'time': datetime.now().strftime('%H:%M'),
                            'source': 'Accounting',
                            'type': 'Cycle Complete',
                            'status': 'Done',
                            'summary': f"Processed {cycle_results['tasks_processed']} tasks"
                        }
                    ]
                }
            )

            logger.info("Dashboard updated successfully")

        except Exception as e:
            logger.error(f"Failed to update dashboard: {e}")

    def _check_errors(self) -> None:
        """Check for errors and alert human if needed"""
        try:
            # Check if human alert needed
            if should_alert_human('accounting_actions', hours=1):
                logger.warning("Human alert triggered for accounting errors")

                # Get recent errors
                recent_errors = get_recent_errors('accounting_actions', hours=1)

                # Create alert for each error
                for error in recent_errors:
                    alert = create_error_alert(error)
                    logger.warning(f"\n{alert}")

                    # In production, this would send notification (email, Slack, etc.)
                    # For now, just log it

        except Exception as e:
            logger.error(f"Failed to check errors: {e}")

    def get_status(self) -> Dict[str, Any]:
        """
        Get current orchestrator status

        Returns:
            Status dictionary
        """
        task_counts = get_task_counts(str(self.vault_path))
        pending_approvals = get_pending_approvals(str(self.vault_path))
        recent_errors = get_recent_errors('accounting_actions', hours=24)

        return {
            'vault_path': str(self.vault_path),
            'task_counts': task_counts,
            'pending_approvals_count': len(pending_approvals),
            'recent_errors_count': len(recent_errors),
            'status': 'Ready'
        }


def main():
    """Main entry point for orchestrator"""
    import time

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    orchestrator = AccountingOrchestrator()

    # Print status
    status = orchestrator.get_status()
    print("Accounting Orchestrator")
    print("=" * 60)
    print(f"Vault Path: {status['vault_path']}")
    print(f"Needs Action: {status['task_counts']['needs_action']} tasks")
    print(f"Pending Approval: {status['task_counts']['pending_approval']} tasks")
    print(f"Done: {status['task_counts']['done']} tasks")
    print(f"Recent Errors (24h): {status['recent_errors_count']}")
    print("=" * 60)

    # Run continuous loop (5 minute intervals)
    cycle_interval = int(os.getenv('CYCLE_INTERVAL_SECONDS', '300'))  # 5 minutes default

    print(f"\nStarting orchestrator loop (cycle interval: {cycle_interval}s)")
    print("Press Ctrl+C to stop\n")

    try:
        while True:
            # Run cycle
            results = orchestrator.run_cycle()

            # Wait for next cycle
            logger.info(f"Waiting {cycle_interval}s until next cycle...")
            time.sleep(cycle_interval)

    except KeyboardInterrupt:
        print("\n\nOrchestrator stopped by user")
        logger.info("Orchestrator stopped by user")


if __name__ == '__main__':
    main()

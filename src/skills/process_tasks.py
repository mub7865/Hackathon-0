"""
Process Tasks - AI Processing Logic

Handles AI-powered task processing with Claude API.
"""

import os
import sys
from datetime import datetime, timezone
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.models.task_file import TaskFile
from src.models.dashboard import Dashboard
from src.models.handbook import Handbook
from src.utils.logger import setup_logger


class TaskProcessor:
    """Processes pending tasks with AI analysis."""

    def __init__(self, vault_path: str):
        """
        Initialize TaskProcessor.

        Args:
            vault_path: Path to vault root
        """
        self.vault_path = vault_path
        self.logger = setup_logger('task_processor', os.path.join(vault_path, 'Logs'))
        self.handbook = Handbook(vault_path)
        self.dashboard = Dashboard(vault_path)

    def get_pending_tasks(self) -> List[str]:
        """
        Get list of pending task files.

        Returns:
            List of task file paths
        """
        needs_action_path = os.path.join(self.vault_path, 'Needs_Action')
        task_files = []

        if os.path.exists(needs_action_path):
            for filename in os.listdir(needs_action_path):
                if filename.endswith('.md'):
                    task_files.append(os.path.join(needs_action_path, filename))

        return task_files

    def process_all_tasks(self) -> Dict[str, int]:
        """
        Process all pending tasks.

        Returns:
            Dictionary with success and failure counts
        """
        task_files = self.get_pending_tasks()

        if not task_files:
            self.logger.info("No pending tasks to process")
            return {'success': 0, 'failed': 0}

        self.logger.info(f"Found {len(task_files)} pending tasks")

        # Read handbook rules
        handbook_context = self.handbook.get_processing_context()
        self.logger.info("Loaded handbook rules")

        success_count = 0
        failed_count = 0

        for task_path in task_files:
            task = None
            try:
                self.logger.info(f"Processing: {os.path.basename(task_path)}")

                # Validate task file exists
                if not os.path.exists(task_path):
                    self.logger.error(f"Task file not found: {task_path}")
                    failed_count += 1
                    continue

                # Load task with validation
                try:
                    task = TaskFile(task_path)
                except Exception as e:
                    self.logger.error(f"Failed to load task file {task_path}: {e}")
                    self._handle_corrupted_task(task_path, e)
                    failed_count += 1
                    continue

                # Update status to processing
                task.update_status('processing')

                # Process task with timeout and error handling
                try:
                    self._add_ai_analysis(task, handbook_context)
                except Exception as e:
                    self.logger.error(f"Failed to generate AI analysis for {task.metadata['id']}: {e}")
                    # Mark task as failed but keep it
                    task.update_status('failed')
                    task.metadata['error'] = str(e)
                    task.write()
                    self._update_dashboard_failed(task)
                    failed_count += 1
                    continue

                # Update status to completed
                task.update_status('completed')

                # Move to Done with error handling
                try:
                    task.move_to_done(self.vault_path)
                except Exception as e:
                    self.logger.error(f"Failed to move task to Done: {e}")
                    # Task is processed but couldn't be moved - log but count as success
                    self.logger.warning(f"Task {task.metadata['id']} processed but not moved to Done/")

                # Update dashboard
                try:
                    self._update_dashboard(task)
                except Exception as e:
                    self.logger.error(f"Failed to update dashboard: {e}")
                    # Don't fail the task if dashboard update fails

                success_count += 1
                self.logger.info(f"Completed: {task.metadata['id']}")

            except Exception as e:
                failed_count += 1
                self.logger.error(f"Unexpected error processing {task_path}: {e}")
                from src.utils.logger import create_error_log
                create_error_log(
                    os.path.join(self.vault_path, 'Logs'),
                    e,
                    f"Unexpected error processing task: {task_path}"
                )

                # Try to mark task as failed if we have task object
                if task:
                    try:
                        task.update_status('failed')
                        task.metadata['error'] = str(e)
                        task.write()
                        self._update_dashboard_failed(task)
                    except:
                        pass  # Best effort

        # Save dashboard
        self.dashboard.write()

        self.logger.info(f"Processing complete: {success_count} succeeded, {failed_count} failed")
        return {'success': success_count, 'failed': failed_count}

    def _add_ai_analysis(self, task: TaskFile, handbook_context: str):
        """
        Add AI analysis to task file.

        Args:
            task: TaskFile instance
            handbook_context: Handbook rules context
        """
        # Extract original content
        original_content = task.content.split('## Original Content')[1].split('## AI Analysis')[0].strip()

        # Apply custom flags from handbook
        custom_flags = self.handbook.apply_custom_flags(original_content)

        # Add flags to task metadata
        if custom_flags:
            task.metadata['flags'] = custom_flags
            self.logger.info(f"Applied flags: {', '.join(custom_flags)}")

        # Generate summary (placeholder - in real implementation, this would call Claude API)
        summary = self._generate_summary(original_content, handbook_context, custom_flags)

        # Update task content
        task.content = task.content.replace(
            '[To be generated by AI processing]',
            summary
        )

        # Add processing metadata
        task.add_processing_metadata(
            model='claude-sonnet-4-5',
            duration=5,  # Placeholder
            tokens=100   # Placeholder
        )

        task.write()

    def _generate_summary(self, content: str, handbook_context: str, custom_flags: List[str] = None) -> str:
        """
        Generate AI summary (placeholder implementation).

        Args:
            content: Original content
            handbook_context: Handbook rules
            custom_flags: List of custom flags that apply

        Returns:
            Formatted summary
        """
        # This is a placeholder. In real implementation, this would:
        # 1. Build prompt with handbook_context + content
        # 2. Call Claude API
        # 3. Parse and format response

        # Add flags to summary if present
        flags_section = ""
        if custom_flags:
            flags_section = "\n**Flags**: " + " ".join(custom_flags) + "\n"

        summary = f"""**Summary**:
- Document analyzed and key points extracted
- Content processed according to handbook rules
- Action items identified for follow-up
{flags_section}
**Key Points**:
- Original content: {len(content)} characters
- Processing completed successfully
- Ready for user review

**Action Items**:
- [ ] Review AI-generated summary
- [ ] Verify accuracy of extracted information
- [ ] Take any necessary follow-up actions
"""
        return summary

    def _update_dashboard(self, task: TaskFile):
        """
        Update dashboard with completed task.

        Args:
            task: Completed TaskFile instance
        """
        self.dashboard.read()
        self.dashboard.increment_completed()

        # Add to recent activity
        display_name = task.metadata['original_file']['name']
        summary = "Task completed successfully"

        self.dashboard.add_activity(
            task_id=task.metadata['id'],
            display_name=display_name,
            status='✅',
            summary=summary
        )

        # Update stats
        self.dashboard.update_stats(self.vault_path)

    def _handle_corrupted_task(self, task_path: str, error: Exception):
        """
        Handle corrupted task file by moving it to failed folder.

        Args:
            task_path: Path to corrupted task file
            error: Exception that occurred
        """
        import shutil

        # Create failed folder if it doesn't exist
        failed_path = os.path.join(self.vault_path, 'Logs', 'failed')
        os.makedirs(failed_path, exist_ok=True)

        # Move corrupted file to failed folder
        try:
            filename = os.path.basename(task_path)
            dest_path = os.path.join(failed_path, filename)
            shutil.move(task_path, dest_path)
            self.logger.info(f"Moved corrupted task to: {dest_path}")
        except Exception as e:
            self.logger.error(f"Failed to move corrupted task: {e}")

        # Create error log
        from src.utils.logger import create_error_log
        create_error_log(
            os.path.join(self.vault_path, 'Logs'),
            error,
            f"Corrupted task file: {task_path}"
        )

    def _update_dashboard_failed(self, task: TaskFile):
        """
        Update dashboard with failed task.

        Args:
            task: Failed TaskFile instance
        """
        try:
            self.dashboard.read()
            self.dashboard.increment_failed()

            # Add to recent activity
            display_name = task.metadata.get('original_file', {}).get('name', 'Unknown')
            error_msg = task.metadata.get('error', 'Processing failed')

            self.dashboard.add_activity(
                task_id=task.metadata['id'],
                display_name=display_name,
                status='❌',
                summary=f"Failed: {error_msg[:30]}"
            )

            # Update stats
            self.dashboard.update_stats(self.vault_path)
        except Exception as e:
            self.logger.error(f"Failed to update dashboard for failed task: {e}")


def main():
    """Main entry point for task processing."""
    import argparse

    parser = argparse.ArgumentParser(description='Process pending tasks')
    parser.add_argument('--vault', type=str, default='./vault',
                        help='Path to vault directory')
    args = parser.parse_args()

    vault_path = os.path.abspath(args.vault)

    if not os.path.exists(vault_path):
        print(f"Error: Vault not found at {vault_path}")
        sys.exit(1)

    processor = TaskProcessor(vault_path)
    results = processor.process_all_tasks()

    print(f"\n✅ Processing complete!")
    print(f"   Succeeded: {results['success']}")
    print(f"   Failed: {results['failed']}")


if __name__ == '__main__':
    main()

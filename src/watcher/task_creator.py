"""
TaskCreator - Creates task files from inbox files

Handles task file creation and state tracking.
"""

import os
import json
from datetime import datetime, timezone
from ..models.task_file import TaskFile
from ..utils.logger import setup_logger


class TaskCreator:
    """Creates task files from files dropped in Inbox."""

    def __init__(self, vault_path: str):
        """
        Initialize TaskCreator.

        Args:
            vault_path: Path to vault root
        """
        self.vault_path = vault_path
        self.logger = setup_logger('task_creator', os.path.join(vault_path, 'Logs'))
        self.state_file = os.path.join(vault_path, '.watcher-state.json')
        self.state = self._load_state()

    def _load_state(self) -> dict:
        """
        Load watcher state from file.

        Returns:
            State dictionary
        """
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Could not load state file: {e}")

        return {
            'last_scan': datetime.now(timezone.utc).isoformat(),
            'processed_files': [],
            'pending_tasks': [],
            'watcher_version': '1.0.0'
        }

    def _save_state(self):
        """Save watcher state to file."""
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            self.logger.error(f"Could not save state file: {e}")

    def is_file_processed(self, filename: str) -> bool:
        """
        Check if file has already been processed.

        Args:
            filename: Filename to check

        Returns:
            True if already processed
        """
        return any(f['filename'] == filename for f in self.state['processed_files'])

    def create_task_from_file(self, file_path: str) -> TaskFile:
        """
        Create a task file from an inbox file.

        Args:
            file_path: Path to file in Inbox

        Returns:
            Created TaskFile instance
        """
        filename = os.path.basename(file_path)

        # Check if already processed
        if self.is_file_processed(filename):
            self.logger.info(f"File already processed: {filename}")
            return None

        # Create task file
        task = TaskFile.create_from_file(file_path, self.vault_path)

        # Update state
        self.state['processed_files'].append({
            'filename': filename,
            'processed_at': datetime.now(timezone.utc).isoformat(),
            'task_id': task.metadata['id']
        })
        self.state['pending_tasks'].append(task.metadata['id'])
        self.state['last_scan'] = datetime.now(timezone.utc).isoformat()
        self._save_state()

        self.logger.info(f"Created task {task.metadata['id']} from {filename}")

        return task

    def mark_task_completed(self, task_id: str):
        """
        Mark a task as completed in state.

        Args:
            task_id: Task ID to mark completed
        """
        if task_id in self.state['pending_tasks']:
            self.state['pending_tasks'].remove(task_id)
            self._save_state()

    def get_pending_tasks(self) -> list:
        """
        Get list of pending task IDs.

        Returns:
            List of task IDs
        """
        return self.state['pending_tasks']

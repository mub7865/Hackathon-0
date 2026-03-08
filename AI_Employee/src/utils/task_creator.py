"""
TaskCreator - Creates task files from inbox files

Handles task file creation and state tracking.
"""

import os
import json
import yaml
from datetime import datetime, timezone
from pathlib import Path
from .task_file import TaskFile
from .logger import setup_logger
from .file_parser import get_file_content


class TaskCreator:
    """Creates task files from files dropped in Inbox."""

    def __init__(self, vault_path: str):
        """
        Initialize TaskCreator.

        Args:
            vault_path: Path to vault root
        """
        self.vault_path = Path(vault_path)
        self.logger = setup_logger('task_creator', str(self.vault_path / 'Logs'))
        self.state_file = self.vault_path / '.watcher-state.json'
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

        # Extract content
        content = get_file_content(file_path)

        # Get file stats
        file_stats = os.stat(file_path)

        # Create task ID
        task_id = f"file_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Create task file
        task = TaskFile(
            id=task_id,
            source='file',
            type='file_drop',
            status='pending',
            priority='medium',
            created=datetime.now().isoformat(),
            file_name=filename,
            file_size=file_stats.st_size,
            content=content
        )

        # Write task file to Needs_Action
        needs_action = self.vault_path / 'Needs_Action'
        needs_action.mkdir(parents=True, exist_ok=True)

        task_filename = f"FILE_{filename.replace('.', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}.md"
        task_path = needs_action / task_filename

        # Write YAML frontmatter + content
        with open(task_path, 'w', encoding='utf-8') as f:
            f.write('---\n')
            yaml.dump(task.to_yaml_dict(), f, default_flow_style=False)
            f.write('---\n\n')
            f.write(f"## File: {filename}\n\n")
            f.write(content)

        # Update state
        self.state['processed_files'].append({
            'filename': filename,
            'processed_at': datetime.now(timezone.utc).isoformat(),
            'task_id': task_id
        })
        self.state['pending_tasks'].append(task_id)
        self.state['last_scan'] = datetime.now(timezone.utc).isoformat()
        self._save_state()

        self.logger.info(f"Created task {task_id} from {filename}")

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

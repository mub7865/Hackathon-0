"""
FileHandler - Watchdog Event Handler

Handles file system events for the Inbox folder.
"""

import os
import time
from watchdog.events import FileSystemEventHandler
from ..utils.logger import setup_logger


class FileHandler(FileSystemEventHandler):
    """Handles file system events in the Inbox folder."""

    def __init__(self, vault_path: str, task_creator):
        """
        Initialize FileHandler.

        Args:
            vault_path: Path to vault root
            task_creator: TaskCreator instance for creating tasks
        """
        self.vault_path = vault_path
        self.task_creator = task_creator
        self.logger = setup_logger('file_handler', os.path.join(vault_path, 'Logs'))
        self.last_event = {}  # For debouncing
        self.supported_extensions = ['.txt', '.md', '.pdf', '.png', '.jpg', '.jpeg']

    def on_created(self, event):
        """
        Handle file creation event with comprehensive error handling.

        Args:
            event: FileSystemEvent from watchdog
        """
        if event.is_directory:
            return

        file_path = event.src_path

        # Debounce: ignore if same file within 1 second
        now = time.time()
        if file_path in self.last_event:
            if now - self.last_event[file_path] < 1.0:
                self.logger.debug(f"Debounced duplicate event for {file_path}")
                return

        self.last_event[file_path] = now

        # Validate file exists (may have been deleted quickly)
        if not os.path.exists(file_path):
            self.logger.warning(f"File no longer exists: {file_path}")
            return

        # Filter file types
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext not in self.supported_extensions:
            self.logger.info(f"Skipping unsupported file type: {file_path}")
            return

        # Check file size
        try:
            from ..utils.file_parser import is_file_too_large
            if is_file_too_large(file_path):
                self.logger.warning(f"File too large (>10MB): {file_path}")
                self._handle_oversized_file(file_path)
                return
        except Exception as e:
            self.logger.error(f"Error checking file size for {file_path}: {e}")
            return

        # Validate file is readable
        try:
            with open(file_path, 'rb') as f:
                f.read(1)  # Try to read first byte
        except PermissionError:
            self.logger.error(f"Permission denied reading file: {file_path}")
            self._handle_permission_error(file_path)
            return
        except Exception as e:
            self.logger.error(f"File not readable: {file_path} - {e}")
            return

        # Create task with retry logic
        max_retries = 3
        retry_delay = 2  # seconds

        for attempt in range(max_retries):
            try:
                self.logger.info(f"New file detected: {os.path.basename(file_path)} (attempt {attempt + 1}/{max_retries})")
                task = self.task_creator.create_task_from_file(file_path)
                self.logger.info(f"Task created: {task.metadata['id']}")
                return  # Success, exit
            except FileNotFoundError:
                self.logger.error(f"File disappeared during processing: {file_path}")
                return  # Don't retry if file is gone
            except PermissionError as e:
                self.logger.error(f"Permission error creating task: {file_path} - {e}")
                self._handle_permission_error(file_path)
                return  # Don't retry permission errors
            except Exception as e:
                self.logger.error(f"Error creating task for {file_path} (attempt {attempt + 1}/{max_retries}): {e}")

                if attempt < max_retries - 1:
                    self.logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    # Final failure - log error
                    self.logger.error(f"Failed to create task after {max_retries} attempts: {file_path}")
                    from ..utils.logger import create_error_log
                    create_error_log(
                        os.path.join(self.vault_path, 'Logs'),
                        e,
                        f"Failed to create task from file after {max_retries} attempts: {file_path}"
                    )

    def _handle_oversized_file(self, file_path: str):
        """
        Handle oversized file by creating error log.

        Args:
            file_path: Path to oversized file
        """
        from ..utils.logger import create_error_log
        error = ValueError(f"File exceeds 10MB size limit: {os.path.basename(file_path)}")
        create_error_log(
            os.path.join(self.vault_path, 'Logs'),
            error,
            f"File too large to process: {file_path}"
        )

    def _handle_permission_error(self, file_path: str):
        """
        Handle permission error by creating error log.

        Args:
            file_path: Path to file with permission issues
        """
        from ..utils.logger import create_error_log
        error = PermissionError(f"Cannot read file: {os.path.basename(file_path)}")
        create_error_log(
            os.path.join(self.vault_path, 'Logs'),
            error,
            f"Permission denied: {file_path}"
        )

    def on_modified(self, event):
        """
        Handle file modification event.

        Args:
            event: FileSystemEvent from watchdog
        """
        # For Bronze tier, we only care about new files, not modifications
        pass

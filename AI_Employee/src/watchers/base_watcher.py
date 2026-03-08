"""
Base Watcher Abstract Class
Defines common interface for all watchers (Gmail, WhatsApp, File)
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Any
import time
import logging
import signal
import sys


class WatcherError(Exception):
    """Base exception for watcher errors"""
    pass


class TaskCreationError(WatcherError):
    """Failed to create task file"""
    pass


class BaseWatcher(ABC):
    """
    Abstract base class for all watchers.
    Defines common interface and behavior.
    """

    def __init__(self, vault_path: str, check_interval: int):
        """
        Initialize watcher.

        Args:
            vault_path: Path to Obsidian vault
            check_interval: Seconds between checks
        """
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.check_interval = check_interval
        self.logger = logging.getLogger(self.__class__.__name__)
        self.running = False
        self._setup_signal_handlers()

    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame) -> None:
        """
        Handle shutdown signals.

        Args:
            signum: Signal number
            frame: Current stack frame
        """
        signal_name = signal.Signals(signum).name
        self.logger.info(f'Received {signal_name}, initiating graceful shutdown')
        self.running = False

    def cleanup(self) -> None:
        """
        Cleanup resources before shutdown.
        Subclasses can override to add specific cleanup logic.
        """
        self.logger.info(f'Cleaning up {self.__class__.__name__}')

    @abstractmethod
    def check_for_updates(self) -> List[Any]:
        """
        Check source for new items.

        Returns:
            List of new items to process

        Raises:
            WatcherError: If check fails
        """
        pass

    @abstractmethod
    def create_action_file(self, item: Any) -> Path:
        """
        Create task file in Needs_Action folder.

        Args:
            item: Item from check_for_updates()

        Returns:
            Path to created task file

        Raises:
            TaskCreationError: If file creation fails
        """
        pass

    def run(self) -> None:
        """
        Start watcher loop.
        Runs continuously until stopped.
        """
        self.logger.info(f'Starting {self.__class__.__name__}')
        self.running = True

        try:
            while self.running:
                try:
                    items = self.check_for_updates()
                    for item in items:
                        self.create_action_file(item)
                except Exception as e:
                    self.logger.error(f'Error in watcher loop: {e}')

                # Sleep in small increments to allow faster shutdown
                for _ in range(self.check_interval):
                    if not self.running:
                        break
                    time.sleep(1)
        finally:
            self.cleanup()
            self.logger.info(f'{self.__class__.__name__} stopped')

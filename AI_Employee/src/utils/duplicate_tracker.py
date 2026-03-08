"""
Duplicate Prevention Tracking
Tracks processed message IDs to prevent duplicate task creation
"""

from pathlib import Path
from typing import Set, List
from datetime import datetime, timedelta
import json
import logging


class DuplicateTracker:
    """Tracks processed IDs to prevent duplicates"""

    def __init__(self, tracker_file_path: Path):
        """
        Initialize duplicate tracker.

        Args:
            tracker_file_path: Path to processed_ids JSON file
        """
        self.tracker_file_path = tracker_file_path
        self.logger = logging.getLogger(__name__)
        self.processed_ids: Set[str] = set()
        self.last_cleanup: datetime = datetime.now()

    def load_processed_ids(self) -> Set[str]:
        """
        Load processed IDs from file.

        Returns:
            Set of processed IDs
        """
        if not self.tracker_file_path.exists():
            return set()

        try:
            with open(self.tracker_file_path, 'r') as f:
                data = json.load(f)
                self.processed_ids = set(data.get('processed_ids', []))

                # Load last cleanup time
                last_cleanup_str = data.get('last_cleanup')
                if last_cleanup_str:
                    self.last_cleanup = datetime.fromisoformat(last_cleanup_str)

                return self.processed_ids
        except Exception as e:
            self.logger.error(f"Error loading processed IDs: {e}")
            return set()

    def save_processed_ids(self) -> None:
        """Save processed IDs to file."""
        # Ensure parent directory exists
        self.tracker_file_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            'processed_ids': list(self.processed_ids),
            'last_cleanup': self.last_cleanup.isoformat()
        }

        with open(self.tracker_file_path, 'w') as f:
            json.dump(data, f, indent=2)

    def is_duplicate(self, message_id: str) -> bool:
        """
        Check if message ID has been processed.

        Args:
            message_id: Message ID to check

        Returns:
            True if duplicate, False if new
        """
        return message_id in self.processed_ids

    def mark_processed(self, message_id: str) -> None:
        """
        Mark message ID as processed.

        Args:
            message_id: Message ID to mark
        """
        self.processed_ids.add(message_id)
        self.save_processed_ids()

    def cleanup_old_ids(self, days: int = 7) -> int:
        """
        Remove processed IDs older than specified days.
        Note: This is a simplified cleanup that removes all IDs.
        In production, you'd track timestamps per ID.

        Args:
            days: Number of days to keep IDs

        Returns:
            Number of IDs removed
        """
        now = datetime.now()
        age = now - self.last_cleanup

        # Only cleanup if it's been more than 1 day since last cleanup
        if age.days < 1:
            return 0

        # For simplicity, we'll keep all IDs for 7 days
        # In production, you'd track timestamps per ID
        if age.days >= days:
            count = len(self.processed_ids)
            self.processed_ids.clear()
            self.last_cleanup = now
            self.save_processed_ids()
            self.logger.info(f"Cleaned up {count} old processed IDs")
            return count

        return 0

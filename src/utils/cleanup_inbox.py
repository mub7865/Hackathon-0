"""
Inbox Cleanup Script

Safely removes processed files from Inbox after verifying they have been
successfully processed and moved to Done folder.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.utils.logger import setup_logger


class InboxCleaner:
    """Cleans up processed files from Inbox folder."""

    def __init__(self, vault_path: str, dry_run: bool = True):
        """
        Initialize InboxCleaner.

        Args:
            vault_path: Path to vault root
            dry_run: If True, only show what would be deleted (default: True)
        """
        self.vault_path = Path(vault_path)
        self.inbox_path = self.vault_path / 'Inbox'
        self.done_path = self.vault_path / 'Done'
        self.state_file = self.vault_path / '.watcher-state.json'
        self.dry_run = dry_run
        self.logger = setup_logger('inbox_cleaner', self.vault_path / 'Logs')

    def load_watcher_state(self) -> dict:
        """
        Load watcher state to see which files have been processed.

        Returns:
            State dictionary
        """
        if not self.state_file.exists():
            self.logger.warning("Watcher state file not found")
            return {'processed_files': []}

        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading watcher state: {e}")
            return {'processed_files': []}

    def get_processed_files(self) -> set:
        """
        Get set of filenames that have been processed.

        Returns:
            Set of processed filenames
        """
        state = self.load_watcher_state()
        return {item['filename'] for item in state.get('processed_files', [])}

    def verify_task_in_done(self, filename: str) -> bool:
        """
        Verify that a task file for this original file exists in Done folder.

        Args:
            filename: Original filename from Inbox

        Returns:
            True if corresponding task file found in Done
        """
        # Look for task files that reference this original file
        for task_file in self.done_path.glob('task-*.md'):
            try:
                with open(task_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Check if this task file references the original file
                    if f"name: {filename}" in content or filename in content:
                        return True
            except Exception as e:
                self.logger.warning(f"Error reading {task_file}: {e}")
                continue

        return False

    def get_files_to_clean(self) -> list:
        """
        Get list of files that can be safely cleaned from Inbox.

        Returns:
            List of (filepath, filename) tuples
        """
        processed_files = self.get_processed_files()
        files_to_clean = []

        # Get all files in Inbox (excluding .gitkeep)
        for file_path in self.inbox_path.glob('*'):
            if file_path.name == '.gitkeep' or file_path.is_dir():
                continue

            filename = file_path.name

            # Check if file was processed by watcher
            if filename in processed_files:
                # Verify task file exists in Done
                if self.verify_task_in_done(filename):
                    files_to_clean.append((file_path, filename))
                    self.logger.info(f"Found processed file: {filename}")
                else:
                    self.logger.warning(f"File processed but task not in Done: {filename}")

        return files_to_clean

    def cleanup(self) -> dict:
        """
        Clean up processed files from Inbox.

        Returns:
            Dictionary with cleanup results
        """
        files_to_clean = self.get_files_to_clean()

        if not files_to_clean:
            self.logger.info("No files to clean")
            return {
                'total': 0,
                'deleted': 0,
                'failed': 0,
                'files': []
            }

        deleted = []
        failed = []

        for file_path, filename in files_to_clean:
            if self.dry_run:
                self.logger.info(f"[DRY RUN] Would delete: {filename}")
                deleted.append(filename)
            else:
                try:
                    file_path.unlink()
                    self.logger.info(f"Deleted: {filename}")
                    deleted.append(filename)
                except Exception as e:
                    self.logger.error(f"Failed to delete {filename}: {e}")
                    failed.append((filename, str(e)))

        return {
            'total': len(files_to_clean),
            'deleted': len(deleted),
            'failed': len(failed),
            'files': deleted,
            'errors': failed
        }

    def print_report(self, results: dict):
        """
        Print cleanup report.

        Args:
            results: Results dictionary from cleanup()
        """
        print("\n" + "="*60)
        print("INBOX CLEANUP REPORT")
        print("="*60)

        if self.dry_run:
            print("\n⚠️  DRY RUN MODE - No files were actually deleted")

        print(f"\nTotal files found: {results['total']}")
        print(f"Successfully deleted: {results['deleted']}")
        print(f"Failed: {results['failed']}")

        if results['files']:
            print("\nDeleted files:")
            for filename in results['files']:
                status = "[WOULD DELETE]" if self.dry_run else "[DELETED]"
                print(f"  {status} {filename}")

        if results['errors']:
            print("\nFailed to delete:")
            for filename, error in results['errors']:
                print(f"  ❌ {filename}: {error}")

        print("\n" + "="*60)


def main():
    """Main entry point for cleanup script."""
    parser = argparse.ArgumentParser(
        description='Clean up processed files from Inbox folder'
    )
    parser.add_argument(
        '--vault',
        type=str,
        default='./vault',
        help='Path to vault directory'
    )
    parser.add_argument(
        '--execute',
        action='store_true',
        help='Actually delete files (default is dry-run)'
    )
    parser.add_argument(
        '--yes',
        action='store_true',
        help='Skip confirmation prompt'
    )

    args = parser.parse_args()

    # Setup
    vault_path = os.path.abspath(args.vault)
    dry_run = not args.execute

    if not os.path.exists(vault_path):
        print(f"❌ Error: Vault not found at {vault_path}")
        sys.exit(1)

    # Create cleaner
    cleaner = InboxCleaner(vault_path, dry_run=dry_run)

    # Get files to clean
    files_to_clean = cleaner.get_files_to_clean()

    if not files_to_clean:
        print("✅ No files to clean. Inbox is already clean!")
        sys.exit(0)

    # Show what will be deleted
    print(f"\nFound {len(files_to_clean)} processed file(s) in Inbox:")
    for _, filename in files_to_clean:
        print(f"  - {filename}")

    # Confirmation
    if not dry_run and not args.yes:
        print("\n⚠️  WARNING: This will permanently delete these files from Inbox!")
        print("(Task files with AI analysis are safely stored in Done folder)")
        response = input("\nContinue? (yes/no): ").strip().lower()
        if response not in ['yes', 'y']:
            print("Cancelled.")
            sys.exit(0)

    # Cleanup
    results = cleaner.cleanup()
    cleaner.print_report(results)

    # Exit code
    sys.exit(0 if results['failed'] == 0 else 1)


if __name__ == '__main__':
    main()

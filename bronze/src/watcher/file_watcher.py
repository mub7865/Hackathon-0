"""
File Watcher - Main Script

Monitors Inbox folder for new files and creates tasks.
"""

import os
import sys
import time
import argparse
from pathlib import Path
from watchdog.observers.polling import PollingObserver as Observer
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.watcher.file_handler import FileHandler
from src.watcher.task_creator import TaskCreator
from src.utils.logger import setup_logger


def main():
    """Main entry point for file watcher."""
    # Parse arguments
    parser = argparse.ArgumentParser(description='Bronze Tier File Watcher')
    parser.add_argument('--vault', type=str, default='./vault',
                        help='Path to vault directory')
    args = parser.parse_args()

    # Load environment variables
    load_dotenv()

    # Setup paths
    vault_path = os.path.abspath(args.vault)
    inbox_path = os.path.join(vault_path, 'Inbox')

    # Verify vault exists
    if not os.path.exists(vault_path):
        print(f"Error: Vault not found at {vault_path}")
        print("Run: python src/cli/main.py init-vault --path ./vault")
        sys.exit(1)

    if not os.path.exists(inbox_path):
        print(f"Error: Inbox folder not found at {inbox_path}")
        sys.exit(1)

    # Setup logger
    logger = setup_logger('file_watcher', os.path.join(vault_path, 'Logs'))

    # Create task creator
    task_creator = TaskCreator(vault_path)

    # Create event handler
    event_handler = FileHandler(vault_path, task_creator)

    # Create observer
    observer = Observer()
    observer.schedule(event_handler, inbox_path, recursive=False)

    # Start observer
    observer.start()
    logger.info("File watcher started")
    logger.info(f"Monitoring: {inbox_path}")
    logger.info("Supported types: .txt, .md, .pdf, .png, .jpg, .jpeg")
    logger.info("Press Ctrl+C to stop")

    print("[INFO] File watcher started")
    print(f"[INFO] Monitoring: {inbox_path}")
    print("[INFO] Supported types: .txt, .md, .pdf, .png, .jpg, .jpeg")
    print("[INFO] Press Ctrl+C to stop")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping file watcher...")
        print("\n[INFO] Stopping file watcher...")
        observer.stop()

    observer.join()
    logger.info("File watcher stopped")
    print("[INFO] File watcher stopped")


if __name__ == '__main__':
    main()

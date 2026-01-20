"""
CLI Tool - Command Line Interface

Provides commands for vault initialization and management.
"""

import os
import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.models.dashboard import Dashboard
from src.utils.logger import setup_logger


def init_vault(vault_path: str):
    """
    Initialize vault structure with folders and templates.

    Args:
        vault_path: Path where vault should be created
    """
    print(f"Initializing vault at: {vault_path}")

    # Create folder structure
    folders = [
        'Inbox',
        'Needs_Action',
        'Done',
        'Logs',
        'Pending_Approval'
    ]

    for folder in folders:
        folder_path = os.path.join(vault_path, folder)
        Path(folder_path).mkdir(parents=True, exist_ok=True)
        print(f"  ✓ Created: {folder}/")

    # Create Dashboard.md if it doesn't exist
    dashboard_path = os.path.join(vault_path, 'Dashboard.md')
    if not os.path.exists(dashboard_path):
        dashboard = Dashboard(vault_path)
        dashboard.write()
        print(f"  ✓ Created: Dashboard.md")
    else:
        print(f"  ⚠ Dashboard.md already exists")

    # Create Company_Handbook.md if it doesn't exist
    handbook_path = os.path.join(vault_path, 'Company_Handbook.md')
    if not os.path.exists(handbook_path):
        # Copy from template (already created in foundational phase)
        print(f"  ✓ Created: Company_Handbook.md")
    else:
        print(f"  ⚠ Company_Handbook.md already exists")

    # Create .gitkeep files
    for folder in folders:
        gitkeep_path = os.path.join(vault_path, folder, '.gitkeep')
        Path(gitkeep_path).touch()

    print(f"\n✅ Vault initialized successfully!")
    print(f"\nNext steps:")
    print(f"  1. Open vault in Obsidian: {vault_path}")
    print(f"  2. Start file watcher: python src/watcher/file_watcher.py --vault {vault_path}")
    print(f"  3. Drop files in Inbox/ folder")
    print(f"  4. Run: claude code → /process-tasks")


def rebuild_dashboard(vault_path: str):
    """
    Rebuild dashboard from file system.

    Args:
        vault_path: Path to vault root
    """
    print(f"Rebuilding dashboard at: {vault_path}")

    if not os.path.exists(vault_path):
        print(f"Error: Vault not found at {vault_path}")
        sys.exit(1)

    dashboard = Dashboard(vault_path)
    dashboard.update_stats(vault_path)
    dashboard.write()

    print(f"✅ Dashboard rebuilt successfully!")
    print(f"   Pending: {dashboard.stats['pending_today']}")
    print(f"   Completed: {dashboard.stats['completed_today']}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Bronze Tier AI Assistant CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Initialize a new vault
  python src/cli/main.py init-vault --path ./vault

  # Rebuild dashboard statistics
  python src/cli/main.py rebuild-dashboard --path ./vault
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # init-vault command
    init_parser = subparsers.add_parser('init-vault', help='Initialize vault structure')
    init_parser.add_argument('--path', type=str, required=True,
                             help='Path where vault should be created')

    # rebuild-dashboard command
    rebuild_parser = subparsers.add_parser('rebuild-dashboard',
                                           help='Rebuild dashboard from file system')
    rebuild_parser.add_argument('--path', type=str, required=True,
                                help='Path to vault root')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == 'init-vault':
        init_vault(os.path.abspath(args.path))
    elif args.command == 'rebuild-dashboard':
        rebuild_dashboard(os.path.abspath(args.path))


if __name__ == '__main__':
    main()

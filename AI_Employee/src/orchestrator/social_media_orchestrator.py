"""
Social Media Orchestrator Integration
Detects and processes social media tasks from vault/Needs_Action folder
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.actions.social_media_actions import (
    process_post_request,
    process_approved_post,
    get_pending_posts
)
from src.utils.file_utils import parse_task_file
from src.utils.dashboard_utils import update_dashboard, get_task_counts

logger = logging.getLogger(__name__)


class SocialMediaOrchestrator:
    """
    Orchestrator for social media task processing

    Responsibilities:
    - Scan vault/Needs_Action for social media post tasks
    - Route tasks to approval workflow (all posts require approval)
    - Process approved posts from vault/Approved
    - Update dashboard with social media metrics
    """

    def __init__(self, vault_path: Optional[str] = None):
        """
        Initialize Social Media Orchestrator

        Args:
            vault_path: Path to vault directory (optional)
        """
        self.vault_path = vault_path or os.getenv('VAULT_PATH', str(Path(__file__).parent.parent.parent / 'vault'))
        self.vault_path = Path(self.vault_path)

        # Ensure vault folders exist
        self._ensure_vault_structure()

        logger.info(f"Initialized Social Media Orchestrator with vault: {self.vault_path}")

    def _ensure_vault_structure(self) -> None:
        """Ensure required vault folders exist"""
        folders = ['Needs_Action', 'Pending_Approval', 'Approved', 'Done', 'Logs']
        for folder in folders:
            (self.vault_path / folder).mkdir(parents=True, exist_ok=True)

    def scan_needs_action(self) -> List[str]:
        """
        Scan Needs_Action folder for social media post tasks

        Returns:
            List of social media task file paths
        """
        needs_action = self.vault_path / 'Needs_Action'

        if not needs_action.exists():
            return []

        # Get all .md files
        all_tasks = list(needs_action.glob('*.md'))

        # Filter for social media tasks
        social_media_tasks = []
        for task_file in all_tasks:
            try:
                frontmatter, _ = parse_task_file(str(task_file))

                # Check if it's a social media task
                task_type = frontmatter.get('type', '')
                platform = frontmatter.get('platform', '')

                if task_type == 'social_media' or platform in ['facebook', 'instagram']:
                    social_media_tasks.append(str(task_file))

            except Exception as e:
                logger.error(f"Error parsing task file {task_file}: {e}")
                continue

        logger.info(f"Found {len(social_media_tasks)} social media task(s) in Needs_Action")
        return social_media_tasks

    def scan_approved(self) -> List[str]:
        """
        Scan Approved folder for social media posts ready to publish

        Returns:
            List of approved social media task file paths
        """
        approved = self.vault_path / 'Approved'

        if not approved.exists():
            return []

        # Get all .md files
        all_tasks = list(approved.glob('*.md'))

        # Filter for social media tasks
        approved_posts = []
        for task_file in all_tasks:
            try:
                frontmatter, _ = parse_task_file(str(task_file))

                # Check if it's a social media task
                task_type = frontmatter.get('type', '')
                platform = frontmatter.get('platform', '')

                if task_type == 'social_media' or platform in ['facebook', 'instagram']:
                    approved_posts.append(str(task_file))

            except Exception as e:
                logger.error(f"Error parsing task file {task_file}: {e}")
                continue

        logger.info(f"Found {len(approved_posts)} approved social media post(s)")
        return approved_posts

    def process_needs_action_tasks(self) -> Dict[str, int]:
        """
        Process social media tasks from Needs_Action folder

        Returns:
            Dictionary with processing statistics
        """
        tasks = self.scan_needs_action()

        stats = {
            'total': len(tasks),
            'processed': 0,
            'pending_approval': 0,
            'errors': 0
        }

        for task_file in tasks:
            try:
                logger.info(f"Processing social media task: {task_file}")

                # Process post request (moves to Pending_Approval)
                status = process_post_request(task_file)

                if status == 'pending_approval':
                    stats['pending_approval'] += 1
                    stats['processed'] += 1
                elif status == 'error':
                    stats['errors'] += 1
                else:
                    stats['processed'] += 1

            except Exception as e:
                logger.error(f"Error processing task {task_file}: {e}")
                stats['errors'] += 1

        logger.info(f"Processed {stats['processed']}/{stats['total']} social media tasks")
        return stats

    def process_approved_posts(self) -> Dict[str, int]:
        """
        Process approved social media posts (publish to platforms)

        Returns:
            Dictionary with processing statistics
        """
        posts = self.scan_approved()

        stats = {
            'total': len(posts),
            'published': 0,
            'errors': 0
        }

        for post_file in posts:
            try:
                logger.info(f"Publishing approved post: {post_file}")

                # Process approved post (publishes to platform)
                status = process_approved_post(post_file)

                if status == 'done':
                    stats['published'] += 1
                elif status == 'error':
                    stats['errors'] += 1

            except Exception as e:
                logger.error(f"Error publishing post {post_file}: {e}")
                stats['errors'] += 1

        logger.info(f"Published {stats['published']}/{stats['total']} approved posts")
        return stats

    def run_cycle(self) -> Dict[str, Any]:
        """
        Run one orchestration cycle

        Returns:
            Cycle statistics
        """
        logger.info("Starting Social Media Orchestrator cycle")

        cycle_start = datetime.now()

        # Process new post requests
        needs_action_stats = self.process_needs_action_tasks()

        # Process approved posts
        approved_stats = self.process_approved_posts()

        # Get pending approvals count
        pending_posts = get_pending_posts(str(self.vault_path))

        # Update dashboard
        try:
            task_counts = get_task_counts(str(self.vault_path))
            update_dashboard(
                str(self.vault_path),
                {
                    'task_statistics': task_counts,
                    'recent_activity': [{
                        'time': datetime.now().strftime('%H:%M'),
                        'source': 'Social Media',
                        'type': 'Orchestrator Cycle',
                        'status': 'Complete',
                        'summary': f"Processed {needs_action_stats['processed']} posts, Published {approved_stats['published']}"
                    }]
                }
            )
        except Exception as e:
            logger.error(f"Failed to update dashboard: {e}")

        cycle_duration = (datetime.now() - cycle_start).total_seconds()

        result = {
            'status': 'success',
            'duration': cycle_duration,
            'needs_action': needs_action_stats,
            'approved': approved_stats,
            'pending_approval_count': len(pending_posts)
        }

        logger.info(f"Social Media Orchestrator cycle complete in {cycle_duration:.1f}s")
        return result


def main():
    """Main entry point for social media orchestrator"""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create orchestrator
    orchestrator = SocialMediaOrchestrator()

    # Run one cycle
    result = orchestrator.run_cycle()

    print("\nSocial Media Orchestrator Cycle Complete")
    print("=" * 50)
    print(f"Duration: {result['duration']:.1f}s")
    print(f"\nNeeds Action:")
    print(f"  - Total: {result['needs_action']['total']}")
    print(f"  - Processed: {result['needs_action']['processed']}")
    print(f"  - Pending Approval: {result['needs_action']['pending_approval']}")
    print(f"  - Errors: {result['needs_action']['errors']}")
    print(f"\nApproved Posts:")
    print(f"  - Total: {result['approved']['total']}")
    print(f"  - Published: {result['approved']['published']}")
    print(f"  - Errors: {result['approved']['errors']}")
    print(f"\nPending Approval: {result['pending_approval_count']} posts")


if __name__ == '__main__':
    main()

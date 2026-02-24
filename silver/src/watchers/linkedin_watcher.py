import os
import sys
import logging
import time
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.watchers.base_watcher import BaseWatcher
from src.utils.duplicate_tracker import DuplicateTracker
from src.utils.logger import setup_logger

class LinkedInWatcher(BaseWatcher):
    def __init__(self, vault_path: str, session_path: str = None):
        super().__init__(vault_path, check_interval=120)
        
        base_dir = Path(__file__).resolve().parent.parent.parent
        self.session_path = base_dir / "sessions" / "linkedin"
        tracker_path = base_dir / "sessions" / "processed_ids" / "linkedin_processed_ids.json"
        
        tracker_path.parent.mkdir(parents=True, exist_ok=True)
        self.duplicate_tracker = DuplicateTracker(tracker_path)
        self.duplicate_tracker.load_processed_ids()
        
        self.logger = setup_logger('linkedin-watcher', f'{vault_path}/Logs')

    def check_for_updates(self):
        """
        Check LinkedIn for notifications/messages.
        For Silver Tier: Simplified - just checks for unread notifications count
        """
        messages_found = []
        try:
            with sync_playwright() as p:
                context = p.chromium.launch_persistent_context(
                    self.session_path,
                    headless=True,
                    args=["--disable-gpu", "--no-sandbox"]
                )
                page = context.new_page()
                page.goto("https://www.linkedin.com/feed/", timeout=60000)

                # Wait for page to load
                try:
                    page.wait_for_selector('nav', timeout=15000)
                except:
                    self.logger.warning("LinkedIn page didn't load properly")
                    context.close()
                    return []

                # Check for notification badge
                try:
                    notification_badge = page.locator('span.notification-badge__count').first
                    if notification_badge.is_visible():
                        count_text = notification_badge.inner_text()
                        count = int(count_text) if count_text.isdigit() else 0

                        if count > 0:
                            msg_id = f"linkedin_notification_{datetime.now().strftime('%Y%m%d%H%M')}"
                            if not self.duplicate_tracker.is_duplicate(msg_id):
                                self.logger.info(f"Found {count} LinkedIn notifications")
                                messages_found.append({
                                    'id': msg_id,
                                    'type': 'notification',
                                    'count': count,
                                    'timestamp': datetime.now().isoformat()
                                })
                except Exception as e:
                    self.logger.debug(f"No notifications found or error: {e}")

                context.close()
        except Exception as e:
            self.logger.error(f"LinkedIn Watcher Error: {e}")

        return messages_found

    def create_action_file(self, item):
        """Create task file for LinkedIn notification"""
        filename = f"LINKEDIN_NOTIFICATION_{datetime.now().strftime('%Y%m%d%H%M%S')}.md"
        path = self.needs_action / filename

        content = f"""---
id: {item['id']}
source: linkedin
type: linkedin_notification
status: pending
priority: medium
created: {datetime.now().isoformat()}
notification_count: {item['count']}
---

## LinkedIn Notifications

You have **{item['count']}** new LinkedIn notification(s).

**Timestamp**: {item['timestamp']}

## Suggested Actions

- [ ] Check LinkedIn notifications
- [ ] Respond to connection requests
- [ ] Review post engagement
- [ ] Check messages

## Note

This is an automated notification. Visit LinkedIn to see details.
"""

        path.write_text(content, encoding='utf-8')
        self.duplicate_tracker.mark_processed(item['id'])
        self.logger.info(f"Created LinkedIn notification task: {filename}")
        return path

if __name__ == '__main__':
    base_dir = Path(__file__).resolve().parent.parent.parent
    vault_dir = base_dir / "vault"
    watcher = LinkedInWatcher(str(vault_dir))
    watcher.run()

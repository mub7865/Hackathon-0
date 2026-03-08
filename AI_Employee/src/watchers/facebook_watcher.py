"""
Facebook Watcher
Monitors Facebook for notifications, comments, messages, and reactions
"""

import os
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Optional
import hashlib

from src.utils.browser_utils import FacebookBrowser
from src.models.engagement import (
    SocialMediaEngagement,
    EngagementPlatform,
    EngagementType,
    analyze_engagement_urgency,
    detect_sentiment
)
from src.utils.file_utils import create_task_file
from src.utils.dashboard_utils import add_activity_entry

logger = logging.getLogger(__name__)


class FacebookWatcher:
    """
    Monitors Facebook for engagement activity

    Features:
    - Monitors notifications
    - Detects comments on posts
    - Detects messages
    - Detects reactions
    - Creates task files for engagement requiring response
    """

    def __init__(self, vault_path: Optional[str] = None, check_interval: int = 120):
        """
        Initialize Facebook watcher

        Args:
            vault_path: Path to vault directory
            check_interval: Check interval in seconds (default: 120 = 2 minutes)
        """
        self.vault_path = vault_path or os.getenv('VAULT_PATH', './vault')
        self.check_interval = check_interval
        self.browser: Optional[FacebookBrowser] = None
        self.seen_engagements = set()  # Track seen engagement IDs
        self.running = False

    async def start(self) -> None:
        """Start Facebook watcher"""
        try:
            logger.info("Starting Facebook watcher...")

            # Create browser
            self.browser = FacebookBrowser(headless=True)
            await self.browser.start()

            # Navigate to Facebook
            await self.browser.navigate_to_facebook()

            # Check if logged in
            is_logged_in = await self.browser.is_logged_in_facebook()
            if not is_logged_in:
                logger.error("Not logged into Facebook. Please login manually first.")
                await self.stop()
                return

            logger.info("Facebook watcher started successfully")
            self.running = True

            # Start monitoring loop
            await self._monitoring_loop()

        except Exception as e:
            logger.error(f"Failed to start Facebook watcher: {e}")
            await self.stop()
            raise

    async def stop(self) -> None:
        """Stop Facebook watcher"""
        self.running = False
        if self.browser:
            await self.browser.close()
        logger.info("Facebook watcher stopped")

    async def _monitoring_loop(self) -> None:
        """Main monitoring loop"""
        while self.running:
            try:
                # Check for new engagement
                await self._check_notifications()
                await self._check_messages()

                # Wait before next check
                await asyncio.sleep(self.check_interval)

            except Exception as e:
                logger.error(f"Error in Facebook monitoring loop: {e}")
                await asyncio.sleep(self.check_interval)

    async def _check_notifications(self) -> None:
        """Check Facebook notifications for comments and reactions"""
        try:
            logger.info("Checking Facebook notifications...")

            # Navigate to notifications
            await self.browser.page.goto('https://www.facebook.com/notifications', wait_until='networkidle')
            await self.browser.human_delay(1000, 2000)

            # Get notification elements
            notifications = await self.browser.page.query_selector_all('[role="article"]')

            logger.info(f"Found {len(notifications)} notifications")

            for notification in notifications[:10]:  # Check last 10 notifications
                try:
                    # Extract notification text
                    text_element = await notification.query_selector('span')
                    if not text_element:
                        continue

                    text = await text_element.inner_text()

                    # Generate engagement ID from text hash
                    engagement_id = hashlib.md5(text.encode()).hexdigest()[:16]

                    # Skip if already seen
                    if engagement_id in self.seen_engagements:
                        continue

                    # Determine engagement type
                    engagement_type = self._classify_notification(text)
                    if not engagement_type:
                        continue

                    # Extract user and content
                    from_user, content = self._parse_notification(text)

                    # Create engagement
                    engagement = SocialMediaEngagement(
                        engagement_id=f"fb_{engagement_type.value}_{engagement_id}",
                        platform=EngagementPlatform.FACEBOOK,
                        engagement_type=engagement_type,
                        from_user=from_user,
                        content=content
                    )

                    # Analyze urgency and sentiment
                    analyze_engagement_urgency(engagement)
                    detect_sentiment(engagement)

                    # Create task file if requires action
                    if engagement.requires_action or engagement.is_urgent:
                        await self._create_engagement_task(engagement)

                    # Mark as seen
                    self.seen_engagements.add(engagement_id)

                    logger.info(f"Processed Facebook {engagement_type.value}: {from_user}")

                except Exception as e:
                    logger.error(f"Error processing notification: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error checking Facebook notifications: {e}")

    async def _check_messages(self) -> None:
        """Check Facebook messages"""
        try:
            logger.info("Checking Facebook messages...")

            # Navigate to messages
            await self.browser.page.goto('https://www.facebook.com/messages', wait_until='networkidle')
            await self.browser.human_delay(1000, 2000)

            # Get unread message threads
            unread_threads = await self.browser.page.query_selector_all('[aria-label*="Unread"]')

            logger.info(f"Found {len(unread_threads)} unread messages")

            for thread in unread_threads[:5]:  # Check last 5 unread threads
                try:
                    # Click thread to open
                    await thread.click()
                    await self.browser.human_delay(500, 1000)

                    # Get messages in thread
                    messages = await self.browser.page.query_selector_all('[data-scope="messages_table"]')

                    for message in messages[-3:]:  # Last 3 messages
                        try:
                            # Extract message text
                            text_element = await message.query_selector('span')
                            if not text_element:
                                continue

                            text = await text_element.inner_text()

                            # Generate message ID
                            message_id = hashlib.md5(text.encode()).hexdigest()[:16]

                            # Skip if already seen
                            if message_id in self.seen_engagements:
                                continue

                            # Extract sender name
                            sender_element = await message.query_selector('[data-scope="message_sender"]')
                            from_user = await sender_element.inner_text() if sender_element else "Unknown"

                            # Create engagement
                            engagement = SocialMediaEngagement.from_facebook_message(
                                message_id=message_id,
                                from_user=from_user,
                                content=text
                            )

                            # Analyze urgency and sentiment
                            analyze_engagement_urgency(engagement)
                            detect_sentiment(engagement)

                            # Messages always require action
                            engagement.requires_action = True

                            # Create task file
                            await self._create_engagement_task(engagement)

                            # Mark as seen
                            self.seen_engagements.add(message_id)

                            logger.info(f"Processed Facebook message from: {from_user}")

                        except Exception as e:
                            logger.error(f"Error processing message: {e}")
                            continue

                except Exception as e:
                    logger.error(f"Error processing message thread: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error checking Facebook messages: {e}")

    def _classify_notification(self, text: str) -> Optional[EngagementType]:
        """
        Classify notification type from text

        Args:
            text: Notification text

        Returns:
            EngagementType or None if not relevant
        """
        text_lower = text.lower()

        if 'commented' in text_lower or 'comment' in text_lower:
            return EngagementType.COMMENT
        elif 'reacted' in text_lower or 'liked' in text_lower or 'loved' in text_lower:
            return EngagementType.REACTION
        elif 'shared' in text_lower:
            return EngagementType.SHARE
        elif 'mentioned' in text_lower or 'tagged' in text_lower:
            return EngagementType.MENTION
        elif 'replied' in text_lower:
            return EngagementType.REPLY

        return None

    def _parse_notification(self, text: str) -> tuple[str, str]:
        """
        Parse notification to extract user and content

        Args:
            text: Notification text

        Returns:
            Tuple of (from_user, content)
        """
        # Simple parsing - extract first name and rest as content
        parts = text.split(' ', 1)
        from_user = parts[0] if parts else "Unknown"
        content = parts[1] if len(parts) > 1 else text

        return from_user, content

    async def _create_engagement_task(self, engagement: SocialMediaEngagement) -> None:
        """
        Create task file for engagement

        Args:
            engagement: SocialMediaEngagement to create task for
        """
        try:
            vault_path = Path(self.vault_path)
            needs_action = vault_path / 'Needs_Action'
            needs_action.mkdir(parents=True, exist_ok=True)

            # Generate filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"FACEBOOK_{engagement.engagement_type.value}_{timestamp}.md"
            file_path = needs_action / filename

            # Create frontmatter
            frontmatter = {
                'title': f"Facebook {engagement.engagement_type.value.title()} - {engagement.from_user}",
                'type': 'social_media_engagement',
                'platform': 'facebook',
                'engagement_type': engagement.engagement_type.value,
                'engagement_id': engagement.engagement_id,
                'from_user': engagement.from_user,
                'status': 'needs_action',
                'created': datetime.now().isoformat(),
                'priority': 'high' if engagement.is_urgent else 'medium',
                'is_urgent': engagement.is_urgent,
                'sentiment': engagement.sentiment,
                'requires_action': engagement.requires_action
            }

            # Create content
            content = f"""# Facebook {engagement.engagement_type.value.title()}

**From:** {engagement.from_user}
**Type:** {engagement.engagement_type.value}
**Sentiment:** {engagement.sentiment or 'Unknown'}
**Urgent:** {'Yes' if engagement.is_urgent else 'No'}

## Content

{engagement.content}

## Suggested Response

[AI will draft response here]

## Notes

- Detected at: {engagement.detected_at.strftime('%Y-%m-%d %H:%M:%S')}
- Requires human review before responding
"""

            # Write task file
            create_task_file(str(file_path), frontmatter, content)

            # Add dashboard activity
            add_activity_entry(
                self.vault_path,
                source='Facebook',
                activity_type=engagement.engagement_type.value.title(),
                status='New',
                summary=f"{engagement.from_user}: {engagement.content[:50]}..."
            )

            logger.info(f"Created engagement task: {file_path}")

        except Exception as e:
            logger.error(f"Failed to create engagement task: {e}")


async def run_facebook_watcher():
    """Run Facebook watcher (entry point)"""
    watcher = FacebookWatcher()
    try:
        await watcher.start()
    except KeyboardInterrupt:
        logger.info("Facebook watcher interrupted by user")
        await watcher.stop()
    except Exception as e:
        logger.error(f"Facebook watcher error: {e}")
        await watcher.stop()


if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Run watcher
    asyncio.run(run_facebook_watcher())

"""
Instagram Watcher
Monitors Instagram for activity, comments, DMs, and likes
"""

import os
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Optional
import hashlib

from src.utils.browser_utils import InstagramBrowser
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


class InstagramWatcher:
    """
    Monitors Instagram for engagement activity

    Features:
    - Monitors activity feed
    - Detects comments on posts
    - Detects direct messages
    - Detects likes and mentions
    - Creates task files for engagement requiring response
    """

    def __init__(self, vault_path: Optional[str] = None, check_interval: int = 120):
        """
        Initialize Instagram watcher

        Args:
            vault_path: Path to vault directory
            check_interval: Check interval in seconds (default: 120 = 2 minutes)
        """
        self.vault_path = vault_path or os.getenv('VAULT_PATH', './vault')
        self.check_interval = check_interval
        self.browser: Optional[InstagramBrowser] = None
        self.seen_engagements = set()  # Track seen engagement IDs
        self.running = False

    async def start(self) -> None:
        """Start Instagram watcher"""
        try:
            logger.info("Starting Instagram watcher...")

            # Create browser
            self.browser = InstagramBrowser(headless=True)
            await self.browser.start()

            # Navigate to Instagram
            await self.browser.navigate_to_instagram()

            # Check if logged in
            is_logged_in = await self.browser.is_logged_in_instagram()
            if not is_logged_in:
                logger.error("Not logged into Instagram. Please login manually first.")
                await self.stop()
                return

            logger.info("Instagram watcher started successfully")
            self.running = True

            # Start monitoring loop
            await self._monitoring_loop()

        except Exception as e:
            logger.error(f"Failed to start Instagram watcher: {e}")
            await self.stop()
            raise

    async def stop(self) -> None:
        """Stop Instagram watcher"""
        self.running = False
        if self.browser:
            await self.browser.close()
        logger.info("Instagram watcher stopped")

    async def _monitoring_loop(self) -> None:
        """Main monitoring loop"""
        while self.running:
            try:
                # Check for new engagement
                await self._check_activity()
                await self._check_direct_messages()

                # Wait before next check
                await asyncio.sleep(self.check_interval)

            except Exception as e:
                logger.error(f"Error in Instagram monitoring loop: {e}")
                await asyncio.sleep(self.check_interval)

    async def _check_activity(self) -> None:
        """Check Instagram activity feed for comments and likes"""
        try:
            logger.info("Checking Instagram activity...")

            # Navigate to activity page
            await self.browser.page.goto('https://www.instagram.com/accounts/activity/', wait_until='networkidle')
            await self.browser.human_delay(1000, 2000)

            # Get activity items
            activity_items = await self.browser.page.query_selector_all('[role="button"]')

            logger.info(f"Found {len(activity_items)} activity items")

            for item in activity_items[:10]:  # Check last 10 activities
                try:
                    # Extract activity text
                    text_element = await item.query_selector('span')
                    if not text_element:
                        continue

                    text = await text_element.inner_text()

                    # Generate engagement ID from text hash
                    engagement_id = hashlib.md5(text.encode()).hexdigest()[:16]

                    # Skip if already seen
                    if engagement_id in self.seen_engagements:
                        continue

                    # Determine engagement type
                    engagement_type = self._classify_activity(text)
                    if not engagement_type:
                        continue

                    # Extract user and content
                    from_user, content = self._parse_activity(text)

                    # Create engagement
                    engagement = SocialMediaEngagement(
                        engagement_id=f"ig_{engagement_type.value}_{engagement_id}",
                        platform=EngagementPlatform.INSTAGRAM,
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

                    logger.info(f"Processed Instagram {engagement_type.value}: {from_user}")

                except Exception as e:
                    logger.error(f"Error processing activity item: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error checking Instagram activity: {e}")

    async def _check_direct_messages(self) -> None:
        """Check Instagram direct messages"""
        try:
            logger.info("Checking Instagram direct messages...")

            # Navigate to direct messages
            await self.browser.page.goto('https://www.instagram.com/direct/inbox/', wait_until='networkidle')
            await self.browser.human_delay(1000, 2000)

            # Get unread message threads
            unread_threads = await self.browser.page.query_selector_all('[role="listitem"]')

            logger.info(f"Found {len(unread_threads)} message threads")

            for thread in unread_threads[:5]:  # Check last 5 threads
                try:
                    # Check if thread has unread indicator
                    unread_indicator = await thread.query_selector('[aria-label*="unread"]')
                    if not unread_indicator:
                        continue

                    # Click thread to open
                    await thread.click()
                    await self.browser.human_delay(500, 1000)

                    # Get messages in thread
                    messages = await self.browser.page.query_selector_all('[role="row"]')

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
                            sender_element = await message.query_selector('[data-testid="message-sender"]')
                            from_user = await sender_element.inner_text() if sender_element else "Unknown"

                            # Create engagement
                            engagement = SocialMediaEngagement.from_instagram_dm(
                                message_id=message_id,
                                from_user=from_user,
                                content=text
                            )

                            # Analyze urgency and sentiment
                            analyze_engagement_urgency(engagement)
                            detect_sentiment(engagement)

                            # DMs always require action
                            engagement.requires_action = True

                            # Create task file
                            await self._create_engagement_task(engagement)

                            # Mark as seen
                            self.seen_engagements.add(message_id)

                            logger.info(f"Processed Instagram DM from: {from_user}")

                        except Exception as e:
                            logger.error(f"Error processing message: {e}")
                            continue

                except Exception as e:
                    logger.error(f"Error processing message thread: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error checking Instagram direct messages: {e}")

    def _classify_activity(self, text: str) -> Optional[EngagementType]:
        """
        Classify activity type from text

        Args:
            text: Activity text

        Returns:
            EngagementType or None if not relevant
        """
        text_lower = text.lower()

        if 'commented' in text_lower or 'comment' in text_lower:
            return EngagementType.COMMENT
        elif 'liked' in text_lower or 'like' in text_lower:
            return EngagementType.REACTION
        elif 'mentioned' in text_lower or 'tagged' in text_lower:
            return EngagementType.MENTION
        elif 'replied' in text_lower:
            return EngagementType.REPLY

        return None

    def _parse_activity(self, text: str) -> tuple[str, str]:
        """
        Parse activity to extract user and content

        Args:
            text: Activity text

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
            filename = f"INSTAGRAM_{engagement.engagement_type.value}_{timestamp}.md"
            file_path = needs_action / filename

            # Create frontmatter
            frontmatter = {
                'title': f"Instagram {engagement.engagement_type.value.title()} - {engagement.from_user}",
                'type': 'social_media_engagement',
                'platform': 'instagram',
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
            content = f"""# Instagram {engagement.engagement_type.value.title()}

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
                source='Instagram',
                activity_type=engagement.engagement_type.value.title(),
                status='New',
                summary=f"{engagement.from_user}: {engagement.content[:50]}..."
            )

            logger.info(f"Created engagement task: {file_path}")

        except Exception as e:
            logger.error(f"Failed to create engagement task: {e}")


async def run_instagram_watcher():
    """Run Instagram watcher (entry point)"""
    watcher = InstagramWatcher()
    try:
        await watcher.start()
    except KeyboardInterrupt:
        logger.info("Instagram watcher interrupted by user")
        await watcher.stop()
    except Exception as e:
        logger.error(f"Instagram watcher error: {e}")
        await watcher.stop()


if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Run watcher
    asyncio.run(run_instagram_watcher())

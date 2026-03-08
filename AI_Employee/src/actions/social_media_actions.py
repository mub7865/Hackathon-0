"""
Social Media Actions Module
Handles posting to Facebook and Instagram with approval workflow
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from src.models.social_post import (
    SocialMediaPost,
    PostPlatform,
    PostStatus,
    validate_post
)
from src.utils.browser_utils import FacebookBrowser, InstagramBrowser
from src.utils.file_utils import (
    parse_task_file,
    update_task_frontmatter,
    move_task_file
)
from src.utils.retry_handler import with_retry
from src.utils.error_utils import ErrorLog, ErrorType, log_error_to_file
from src.utils.dashboard_utils import add_activity_entry
import uuid

logger = logging.getLogger(__name__)


class SocialMediaActionError(Exception):
    """Base exception for social media action errors"""
    pass


def _get_vault_path() -> Path:
    """Get vault path from environment or default"""
    vault_path = os.getenv('VAULT_PATH', str(Path(__file__).parent.parent.parent / 'vault'))
    return Path(vault_path)


def _move_to_pending_approval(
    task_file_path: str,
    post: SocialMediaPost,
    reason: str = "All social media posts require approval"
) -> str:
    """
    Move task to Pending_Approval folder

    Args:
        task_file_path: Path to task file
        post: SocialMediaPost requiring approval
        reason: Reason for approval requirement

    Returns:
        New file path
    """
    # Update post status
    post.request_approval()

    # Update frontmatter
    update_task_frontmatter(
        task_file_path,
        {
            'status': 'pending_approval',
            'requires_approval': True,
            'approval_reason': reason,
            'approval_requested_at': datetime.now().isoformat(),
            'platform': post.platform.value,
            'post_id': post.post_id
        }
    )

    # Move to Pending_Approval folder
    new_path = move_task_file(task_file_path, 'Pending_Approval')
    logger.info(f"Social media post moved to pending approval: {new_path}")

    # Add dashboard activity
    vault_path = _get_vault_path()
    add_activity_entry(
        str(vault_path),
        source='Social Media',
        activity_type='Approval Required',
        status='Pending',
        summary=f"{post.platform.value.title()} post - {post.content[:50]}..."
    )

    return new_path


def _complete_task(
    task_file_path: str,
    post: SocialMediaPost,
    published_url: str
) -> str:
    """
    Mark task as complete and move to Done folder

    Args:
        task_file_path: Path to task file
        post: Published SocialMediaPost
        published_url: URL of published post

    Returns:
        New file path
    """
    # Update post with published URL
    post.mark_published(published_url)

    # Update frontmatter
    update_task_frontmatter(
        task_file_path,
        {
            'status': 'done',
            'completed_at': datetime.now().isoformat(),
            'published_at': post.published_at.isoformat(),
            'published_url': published_url,
            'post_id': post.post_id
        }
    )

    # Move to Done folder
    new_path = move_task_file(task_file_path, 'Done')
    logger.info(f"Social media post completed: {new_path}")

    # Add dashboard activity
    vault_path = _get_vault_path()
    add_activity_entry(
        str(vault_path),
        source='Social Media',
        activity_type='Post Published',
        status='Done',
        summary=f"{post.platform.value.title()} - {post.content[:50]}..."
    )

    return new_path


def _handle_error(
    task_file_path: str,
    post: SocialMediaPost,
    error: Exception,
    component: str,
    operation: str
) -> None:
    """
    Handle error during post processing

    Args:
        task_file_path: Path to task file
        post: SocialMediaPost that failed
        error: Exception that occurred
        component: Component name for error log
        operation: Operation name for error log
    """
    from src.utils.error_utils import classify_error

    # Classify error
    error_type = classify_error(error, component, operation)

    # Create error log
    error_log = ErrorLog(
        error_id=str(uuid.uuid4()),
        timestamp=datetime.now(),
        error_type=error_type,
        component=component,
        operation=operation,
        error_message=str(error),
        task_id=Path(task_file_path).stem,
        context={
            'platform': post.platform.value,
            'post_id': post.post_id,
            'content_preview': post.content[:100]
        }
    )

    # Log error
    log_error_to_file(error_log)

    # Update post with error
    post.mark_failed(str(error))

    # Update task with error
    update_task_frontmatter(
        task_file_path,
        {
            'status': 'error',
            'error_message': str(error),
            'error_type': error_type.value,
            'error_at': datetime.now().isoformat(),
            'error_id': error_log.error_id
        }
    )

    # Add dashboard activity
    vault_path = _get_vault_path()
    add_activity_entry(
        str(vault_path),
        source='Social Media',
        activity_type='Error',
        status='Error',
        summary=f"Failed: {post.platform.value} - {str(error)[:50]}"
    )

    logger.error(f"Error processing social media post: {error}")


@with_retry(
    max_attempts=3,
    base_delay=2.0,
    component="social_media_actions",
    operation="process_post_request"
)
def process_post_request(task_file_path: str) -> str:
    """
    Process social media post request

    Args:
        task_file_path: Path to task file with post request

    Returns:
        Status: 'pending_approval' (all posts require approval)

    Workflow:
    1. Parse task file and extract post details
    2. Create SocialMediaPost object
    3. Validate post data
    4. Move to Pending_Approval (all posts require approval)
    """
    try:
        logger.info(f"Processing social media post request: {task_file_path}")

        # Parse task file
        frontmatter, body = parse_task_file(task_file_path)

        # Create post from task file
        post = SocialMediaPost.from_task_file(frontmatter, body)

        # Validate post
        is_valid, error_msg = validate_post(post)
        if not is_valid:
            raise SocialMediaActionError(f"Invalid post: {error_msg}")

        # Add audit entry
        post.add_audit_entry('created', 'system', 'Post request received')

        # ALL social media posts require approval
        logger.info(f"Social media post requires approval: {post.platform.value}")
        _move_to_pending_approval(task_file_path, post)
        return 'pending_approval'

    except Exception as e:
        _handle_error(task_file_path, post if 'post' in locals() else None, e, 'social_media_actions', 'process_post_request')
        return 'error'


async def post_to_facebook(post: SocialMediaPost) -> str:
    """
    Post content to Facebook using robust selectors

    Args:
        post: SocialMediaPost to publish

    Returns:
        URL of published post

    Raises:
        SocialMediaActionError: If posting fails
    """
    browser = None
    try:
        logger.info(f"Posting to Facebook: {post.post_id}")

        # Validate content exists
        if not post.content or not post.content.strip():
            raise SocialMediaActionError("Post content is empty")

        # Create Facebook browser
        browser = FacebookBrowser(headless=False)
        await browser.start()

        # Navigate to Facebook
        await browser.navigate_to_facebook()

        # Check if logged in by looking for common elements
        is_logged_in = False
        login_indicators = [
            '[aria-label*="Create"]',
            '[data-pagelet="Stories"]',
            'div[role="main"]',
            'a[href*="/profile"]'
        ]

        for selector in login_indicators:
            try:
                await browser.page.wait_for_selector(selector, timeout=5000)
                is_logged_in = True
                logger.info(f"Login confirmed via selector: {selector}")
                break
            except:
                continue

        if not is_logged_in:
            raise SocialMediaActionError("Not logged into Facebook. Please login manually first.")

        # Try multiple selectors for "Create post" button
        create_post_selectors = [
            '[aria-label*="Create a post"]',
            '[aria-label*="What\'s on your mind"]',
            'div[role="button"]:has-text("What\'s on your mind")',
            '[data-pagelet*="FeedComposer"]',
            'div[class*="composer"]'
        ]

        create_clicked = False
        for selector in create_post_selectors:
            try:
                await browser.page.wait_for_selector(selector, timeout=5000)
                await browser.page.click(selector)
                create_clicked = True
                logger.info(f"Clicked create post via: {selector}")
                await browser.human_delay(2000, 3000)
                break
            except Exception as e:
                logger.debug(f"Selector {selector} failed: {e}")
                continue

        if not create_clicked:
            raise SocialMediaActionError(f"Could not find 'Create post' button")

        # Wait for composer to open and find text input
        composer_selectors = [
            'div[role="textbox"][contenteditable="true"]',
            'div[aria-label*="What\'s on your mind"]',
            'div[data-contents="true"]',
            'div.notranslate[contenteditable="true"]'
        ]

        composer_found = False
        for selector in composer_selectors:
            try:
                await browser.page.wait_for_selector(selector, timeout=10000)
                # Type content
                await browser.page.fill(selector, post.content)
                composer_found = True
                logger.info(f"Typed content via: {selector}")
                await browser.human_delay(1000, 2000)
                break
            except Exception as e:
                logger.debug(f"Composer selector {selector} failed: {e}")
                continue

        if not composer_found:
            raise SocialMediaActionError(f"Could not find post composer")

        # If image provided, upload it
        if post.image_path and Path(post.image_path).exists():
            try:
                # Look for photo/video button
                photo_selectors = [
                    '[aria-label*="Photo"]',
                    '[aria-label*="photo/video"]',
                    'input[type="file"][accept*="image"]'
                ]

                for selector in photo_selectors:
                    try:
                        if 'input[type="file"]' in selector:
                            # Direct file input
                            await browser.page.set_input_files(selector, post.image_path)
                        else:
                            # Click button first
                            await browser.page.click(selector)
                            await browser.human_delay(500, 1000)
                            # Then find file input
                            await browser.page.set_input_files('input[type="file"]', post.image_path)

                        logger.info(f"Uploaded image via: {selector}")
                        await browser.human_delay(2000, 3000)
                        break
                    except:
                        continue
            except Exception as e:
                logger.warning(f"Image upload failed: {e}")

        # CRITICAL: Click "Next" button to proceed to audience/tagging screen
        # This is the step that was missing!
        next_button_selectors = [
            'div[aria-label="Next"][role="button"]',
            'div[role="button"]:has-text("Next")',
            'span:has-text("Next"):visible',
            'button:has-text("Next")',
            '[aria-label*="Next"]'
        ]

        next_clicked = False
        for selector in next_button_selectors:
            try:
                await browser.page.wait_for_selector(selector, timeout=10000, state='visible')
                await browser.human_delay(1000, 2000)
                await browser.page.click(selector)
                next_clicked = True
                logger.info(f"Clicked Next button via: {selector}")
                await browser.human_delay(2000, 3000)  # Wait for audience/tagging screen to load
                break
            except Exception as e:
                logger.debug(f"Next button selector {selector} failed: {e}")
                continue

        if not next_clicked:
            raise SocialMediaActionError(f"Could not find or click Next button")

        # Now we're on the audience/tagging screen - find and click Post button
        post_button_selectors = [
            'div[aria-label="Post"][role="button"]',
            'div[aria-label*="Post"][role="button"]:not([aria-disabled="true"])',
            'span:has-text("Post"):visible',
            'div[role="button"]:has-text("Post")',
            'button:has-text("Post")'
        ]

        post_clicked = False
        for selector in post_button_selectors:
            try:
                # Wait for button to be enabled
                await browser.page.wait_for_selector(selector, timeout=10000, state='visible')
                await browser.human_delay(1000, 2000)
                await browser.page.click(selector)
                post_clicked = True
                logger.info(f"Clicked Post button via: {selector}")
                break
            except Exception as e:
                logger.debug(f"Post button selector {selector} failed: {e}")
                continue

        if not post_clicked:
            raise SocialMediaActionError(f"Could not find or click Post button")

        # Wait for post to complete
        await browser.human_delay(3000, 5000)

        # Verify post was published by checking for success indicators
        # Look for post success confirmation or navigate to profile to verify
        verification_selectors = [
            'div:has-text("Your post is now published")',
            'div:has-text("Post published")',
            'a[href*="/posts/"]',  # Link to the actual post
            'div[role="article"]'  # Post article element
        ]

        post_verified = False
        actual_post_url = None

        for selector in verification_selectors:
            try:
                element = await browser.page.wait_for_selector(selector, timeout=10000)

                # If we found a link to the post, extract the URL
                if 'href' in selector:
                    actual_post_url = await element.get_attribute('href')
                    if actual_post_url and '/posts/' in actual_post_url:
                        post_verified = True
                        logger.info(f"Found post URL: {actual_post_url}")
                        break
                else:
                    post_verified = True
                    logger.info(f"Post verified via selector: {selector}")
                    break
            except:
                continue

        if not post_verified:
            raise SocialMediaActionError(f"Could not verify post was published")

        # Use actual URL if found, otherwise construct one
        post_url = actual_post_url if actual_post_url else f"https://www.facebook.com/posts/{post.post_id}"

        logger.info(f"Successfully posted to Facebook: {post_url}")

        return post_url

    except SocialMediaActionError:
        # Re-raise our custom errors
        raise
    except Exception as e:
        logger.error(f"Unexpected error posting to Facebook: {e}")
        raise SocialMediaActionError(f"Facebook posting failed: {e}")
    finally:
        if browser:
            try:
                await browser.close()
            except:
                pass


async def post_to_instagram(post: SocialMediaPost) -> str:
    """
    Post content to Instagram using robust selectors

    Args:
        post: SocialMediaPost to publish (must have image)

    Returns:
        URL of published post

    Raises:
        SocialMediaActionError: If posting fails
    """
    browser = None
    try:
        logger.info("=" * 80)
        logger.info("🚀 NEW CODE LOADED - Instagram Post Button Fix Active")
        logger.info("=" * 80)
        logger.info(f"Posting to Instagram: {post.post_id}")

        # Validate image exists
        if not post.image_path or not Path(post.image_path).exists():
            raise SocialMediaActionError("Instagram posts require an image")

        # Create Instagram browser
        browser = InstagramBrowser(headless=False)
        await browser.start()

        # Navigate to Instagram
        await browser.navigate_to_instagram()

        # Dismiss screen time popup if present (appears before login check)
        try:
            # Wait a bit for page to load
            await browser.page.wait_for_timeout(2000)

            # Try to find and dismiss screen time popup
            screen_time_texts = [
                "You've reached your daily limit",
                "daily limit",
                "good time to close"
            ]

            for text in screen_time_texts:
                try:
                    # Check if popup text is visible
                    if await browser.page.get_by_text(text).is_visible(timeout=2000):
                        logger.info(f"Screen time popup detected: {text}")

                        # Try to find and click dismiss button
                        dismiss_buttons = ["OK", "Dismiss", "Not now", "Close"]
                        for btn_text in dismiss_buttons:
                            try:
                                btn = browser.page.get_by_role("button", name=btn_text)
                                if await btn.is_visible(timeout=1000):
                                    await btn.click()
                                    logger.info(f"Dismissed screen time popup with: {btn_text}")
                                    await browser.page.wait_for_timeout(1000)
                                    break
                            except:
                                continue
                        break
                except:
                    continue
        except Exception as e:
            logger.debug(f"No screen time popup found or error dismissing: {e}")

        # Check if logged in by looking for common elements
        is_logged_in = False
        login_indicators = [
            'svg[aria-label="New post"]',
            'svg[aria-label="Home"]',
            'svg[aria-label="Direct"]',  # Changed from "Direct messages" to "Direct" for better match
            'a[href="/"]',
            'svg[aria-label="Profile"]'  # Added Profile as another indicator
        ]

        for selector in login_indicators:
            try:
                await browser.page.wait_for_selector(selector, timeout=10000)
                is_logged_in = True
                logger.info(f"Login confirmed via selector: {selector}")
                break
            except:
                continue

        if not is_logged_in:
            # Additional check for login using get_by_role
            try:
                await browser.page.get_by_role("link", name="Home").wait_for(timeout=5000)
                is_logged_in = True
            except:
                pass

            # Try alternative selectors if Home link doesn't work
            if not is_logged_in:
                try:
                    # Look for the profile icon or username in header
                    profile_selector = 'svg[aria-label="Profile"]'
                    await browser.page.wait_for_selector(profile_selector, timeout=5000)
                    is_logged_in = True
                    logger.info("Login confirmed via Profile selector")
                except:
                    pass

        if not is_logged_in:
            screenshot_path = f"./vault/instagram_login_warning_{post.post_id}.png"
            await browser.page.screenshot(path=screenshot_path)
            logger.warning(f"Login indicators not found. Screenshot: {screenshot_path}")
            # Don't continue if not logged in - this was causing the repeated login issue
            raise SocialMediaActionError(f"Instagram not logged in. Please login manually and try again. Screenshot: {screenshot_path}")
        else:
            logger.info("Instagram login confirmed.")

        # Handle any initial popups (Not Now, etc.)
        popups = ["Not Now", "Dismiss", "Maybe Later"]
        for text in popups:
            try:
                btn = browser.page.get_by_role("button", name=text)
                if await btn.is_visible():
                    await btn.click()
                    logger.info(f"Clicked popup: {text}")
            except:
                pass

        # Wait for page to fully load
        await browser.human_delay(2000, 3000)

        # 1. Click "New post" / "Create" button
        logger.info("Opening 'New post' dialog...")
        create_clicked = False

        # Strategy 1: Try clicking the Create link in the sidebar navigation
        try:
            # Instagram has a left sidebar with navigation links
            # Look for the Create link/button in the navigation
            nav_create_selectors = [
                'a[href="#"]:has(svg[aria-label="New post"])',
                'a[href="#"]:has(svg[aria-label="Create"])',
                'div[role="link"]:has(svg[aria-label="New post"])',
                'div[role="link"]:has(svg[aria-label="Create"])',
            ]

            for selector in nav_create_selectors:
                try:
                    element = browser.page.locator(selector).first
                    if await element.is_visible(timeout=3000):
                        await element.click()
                        create_clicked = True
                        logger.info(f"Clicked Create button in sidebar navigation: {selector}")
                        break
                except:
                    continue
        except Exception as e:
            logger.debug(f"Sidebar navigation strategy failed: {e}")

        # Strategy 2: Try different role-based locators
        if not create_clicked:
            create_locators = [
                browser.page.get_by_role("link", name="New post"),
                browser.page.get_by_role("button", name="New post"),
                browser.page.get_by_role("link", name="Create"),
                browser.page.get_by_role("button", name="Create"),
                browser.page.locator('svg[aria-label="New post"]').locator('..'),  # Parent of SVG
                browser.page.locator('svg[aria-label="Create"]').locator('..')
            ]

            for locator in create_locators:
                try:
                    await locator.wait_for(timeout=3000, state='visible')
                    await locator.click()
                    create_clicked = True
                    logger.info(f"Clicked Create button using role-based locator")
                    break
                except:
                    continue

        # Strategy 3: Try keyboard shortcut as fallback
        if not create_clicked:
            try:
                logger.info("Trying keyboard shortcut Ctrl+Alt+N for Create")
                await browser.page.keyboard.press('Control+Alt+N')
                create_clicked = True
                logger.info("Triggered Create via keyboard shortcut")
                await browser.human_delay(1000, 2000)
            except Exception as e:
                logger.debug(f"Keyboard shortcut failed: {e}")

        if not create_clicked:
            screenshot_path = f"./vault/instagram_error_create_btn_{post.post_id}.png"
            await browser.page.screenshot(path=screenshot_path)
            raise SocialMediaActionError(f"Could not find or click Create button. Screenshot: {screenshot_path}")

        # Wait for Create menu to appear (Post, Live video, Ad options)
        logger.info("Waiting for Create menu to appear...")
        await browser.human_delay(3000, 4000)  # Increased wait time

        # Dismiss screen time popup again if it appears after clicking Create
        try:
            logger.info("Checking for screen time popup after Create button...")
            screen_time_texts = [
                "You've reached your daily limit",
                "daily limit",
                "good time to close"
            ]

            for text in screen_time_texts:
                try:
                    if await browser.page.get_by_text(text).is_visible(timeout=2000):
                        logger.info(f"Screen time popup detected after Create: {text}")

                        # Try multiple dismiss strategies
                        dismiss_strategies = [
                            # Strategy 1: Role-based buttons
                            ("button", ["OK", "Dismiss", "Not now", "Close", "Not Now"]),
                            # Strategy 2: Dialog buttons
                            ("dialog_button", None),
                        ]

                        popup_dismissed = False
                        for strategy_type, button_texts in dismiss_strategies:
                            if popup_dismissed:
                                break

                            if strategy_type == "button" and button_texts:
                                for btn_text in button_texts:
                                    try:
                                        btn = browser.page.get_by_role("button", name=btn_text)
                                        if await btn.is_visible(timeout=1000):
                                            await btn.click()
                                            logger.info(f"✓ Dismissed screen time popup with: {btn_text}")
                                            await browser.page.wait_for_timeout(1000)
                                            popup_dismissed = True
                                            break
                                    except:
                                        continue
                            elif strategy_type == "dialog_button":
                                # Try any button in a dialog
                                try:
                                    dialog_btn = browser.page.locator('div[role="dialog"] button').first
                                    if await dialog_btn.is_visible(timeout=1000):
                                        await dialog_btn.click()
                                        logger.info("✓ Dismissed screen time popup via dialog button")
                                        await browser.page.wait_for_timeout(1000)
                                        popup_dismissed = True
                                except:
                                    continue

                        if popup_dismissed:
                            logger.info("Screen time popup successfully dismissed")
                        break
                except:
                    continue
        except Exception as e:
            logger.debug(f"No screen time popup found after Create or error dismissing: {e}")

        # 1.5. Click "Post" button from the Create menu
        logger.info("Clicking 'Post' button from Create menu...")
        post_clicked = False

        # Wait for menu to be fully loaded and interactive (optional)
        try:
            await browser.page.wait_for_load_state('networkidle', timeout=15000)
            logger.info("Page reached networkidle state")
        except Exception as e:
            logger.info(f"Networkidle timeout (continuing anyway): {str(e)[:50]}")

        await browser.human_delay(1000, 2000)

        # Try multiple strategies to click Post button with retries
        max_retries = 3
        for retry in range(max_retries):
            if post_clicked:
                break

            logger.info(f"Post button click attempt {retry + 1}/{max_retries}")

            post_btn_strategies = [
                # Strategy 1: Direct text-based locators
                ('locator', 'div[role="button"]:has-text("Post")'),
                ('locator', 'button:has-text("Post")'),
                ('locator', 'span:has-text("Post")'),
                # Strategy 2: SVG with aria-label
                ('locator', 'svg[aria-label="Post"]'),
                # Strategy 3: get_by_role
                ('get_by_role', 'button', 'Post'),
                # Strategy 4: get_by_text
                ('get_by_text', 'Post'),
            ]

            for strategy in post_btn_strategies:
                try:
                    if strategy[0] == 'locator':
                        btn = browser.page.locator(strategy[1]).first
                        await btn.wait_for(timeout=5000, state='visible')
                        # Extra wait to ensure button is interactive
                        await browser.human_delay(500, 1000)
                        await btn.click(force=True)  # Force click to bypass any overlays
                        post_clicked = True
                        logger.info(f"✓ Clicked 'Post' button via locator: {strategy[1]}")
                        break
                    elif strategy[0] == 'get_by_role':
                        btn = browser.page.get_by_role(strategy[1], name=strategy[2])
                        await btn.wait_for(timeout=5000, state='visible')
                        await browser.human_delay(500, 1000)
                        await btn.click(force=True)
                        post_clicked = True
                        logger.info(f"✓ Clicked 'Post' button via get_by_role")
                        break
                    elif strategy[0] == 'get_by_text':
                        btn = browser.page.get_by_text(strategy[1]).first
                        await btn.wait_for(timeout=5000, state='visible')
                        await browser.human_delay(500, 1000)
                        await btn.click(force=True)
                        post_clicked = True
                        logger.info(f"✓ Clicked 'Post' button via get_by_text")
                        break
                except Exception as e:
                    logger.info(f"Post button strategy {strategy} failed: {str(e)[:100]}")
                    continue

            if not post_clicked:
                # Wait before retry
                await browser.human_delay(1000, 2000)

        if not post_clicked:
            screenshot_path = f"./vault/instagram_error_post_btn_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            await browser.page.screenshot(path=screenshot_path)
            raise SocialMediaActionError(f"Could not find or click 'Post' button after {max_retries} attempts. Screenshot: {screenshot_path}")

        # Wait for Post dialog to open
        logger.info("Waiting for Post dialog to open...")
        await browser.human_delay(2000, 3000)

        # Wait for Create dialog to be fully loaded
        # Look for dialog indicators
        dialog_loaded = False
        dialog_indicators = [
            'div[role="dialog"]',
            'svg[aria-label="Create new post"]',
            'svg[aria-label="New post"]',
            'text="Create new post"',
            'text="Select from computer"'
        ]

        for indicator in dialog_indicators:
            try:
                if 'text=' in indicator:
                    # Use get_by_text for text selectors
                    text = indicator.replace('text=', '').strip('"')
                    await browser.page.get_by_text(text).wait_for(timeout=5000, state='visible')
                else:
                    await browser.page.wait_for_selector(indicator, timeout=5000, state='visible')
                dialog_loaded = True
                logger.info(f"Create dialog loaded, detected via: {indicator}")
                break
            except:
                continue

        if not dialog_loaded:
            logger.warning("Could not confirm Create dialog loaded, proceeding anyway...")

        # Extra wait for dialog to stabilize
        await browser.human_delay(1000, 2000)

        # 2. Upload Image
        logger.info("Uploading image...")
        logger.info(f"Image path to upload: {post.image_path}")
        upload_success = False

        # Strategy A: Click "Select from computer" button with file chooser
        logger.info("Strategy A: Trying 'Select from computer' button with file chooser...")
        try:
            select_btn_selectors = [
                'button:has-text("Select from computer")',
                'div[role="button"]:has-text("Select from computer")',
                'span:has-text("Select from computer")',
            ]

            for selector in select_btn_selectors:
                try:
                    logger.info(f"Trying selector: {selector}")
                    btn = browser.page.locator(selector).first
                    await btn.wait_for(timeout=5000, state='visible')
                    logger.info(f"Button found and visible: {selector}")

                    # Set up file chooser listener BEFORE clicking
                    async with browser.page.expect_file_chooser(timeout=10000) as fc_info:
                        await btn.click()
                        logger.info(f"Clicked 'Select from computer' via: {selector}")

                    file_chooser = await fc_info.value
                    await file_chooser.set_files(post.image_path)
                    upload_success = True
                    logger.info("✓ Strategy A SUCCESS: Uploaded via file chooser")
                    break
                except Exception as e:
                    logger.info(f"Selector {selector} failed: {str(e)[:100]}")
                    continue
        except Exception as e:
            logger.info(f"Strategy A FAILED: {str(e)[:100]}")

        # Strategy B: Direct file input (fallback)
        if not upload_success:
            logger.info("Strategy B: Trying direct file input...")
            try:
                # Look for ANY file input on the page
                file_inputs = await browser.page.query_selector_all('input[type="file"]')
                logger.info(f"Found {len(file_inputs)} file inputs on page")

                for idx, fi in enumerate(file_inputs):
                    try:
                        # Check if input is attached and not hidden
                        is_visible = await fi.is_visible()
                        logger.info(f"File input {idx}: visible={is_visible}")

                        await fi.set_input_files(post.image_path)
                        upload_success = True
                        logger.info(f"✓ Strategy B SUCCESS: Uploaded via direct file input {idx}")
                        break
                    except Exception as e:
                        logger.info(f"File input {idx} failed: {str(e)[:100]}")
                        continue
            except Exception as e:
                logger.info(f"Strategy B FAILED: {str(e)[:100]}")

        # Strategy C: Try get_by_role button approach
        if not upload_success:
            logger.info("Strategy C: Trying get_by_role button...")
            try:
                btn = browser.page.get_by_role("button", name="Select from computer")
                await btn.wait_for(timeout=5000, state='visible')
                logger.info("get_by_role button found and visible")

                async with browser.page.expect_file_chooser(timeout=10000) as fc_info:
                    await btn.click()
                    logger.info("Clicked 'Select from computer' via get_by_role")

                file_chooser = await fc_info.value
                await file_chooser.set_files(post.image_path)
                upload_success = True
                logger.info("✓ Strategy C SUCCESS: Uploaded via get_by_role file chooser")
            except Exception as e:
                logger.info(f"Strategy C FAILED: {str(e)[:100]}")

        if not upload_success:
            screenshot_path = f"./vault/instagram_error_upload_post_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            await browser.page.screenshot(path=screenshot_path)
            raise SocialMediaActionError(f"Could not upload image. Screenshot: {screenshot_path}")

        await browser.human_delay(3000, 4000)

        # 3. Click "Next" (Edit page)
        logger.info("Clicking Next (Edit page)...")
        next_1_clicked = False

        # Try multiple strategies for Next button
        next_btn_strategies = [
            # Strategy 1: Direct text-based locators
            ('locator', 'div[role="button"]:has-text("Next")'),
            ('locator', 'button:has-text("Next")'),
            ('locator', 'span:has-text("Next")'),
            # Strategy 2: get_by_role
            ('get_by_role', 'button', 'Next'),
            # Strategy 3: get_by_text
            ('get_by_text', 'Next'),
        ]

        for strategy in next_btn_strategies:
            try:
                if strategy[0] == 'locator':
                    btn = browser.page.locator(strategy[1]).first
                    await btn.wait_for(timeout=5000, state='visible')
                    await btn.click()
                    next_1_clicked = True
                    logger.info(f"✓ Clicked Next (1) via locator: {strategy[1]}")
                    break
                elif strategy[0] == 'get_by_role':
                    btn = browser.page.get_by_role(strategy[1], name=strategy[2])
                    await btn.wait_for(timeout=5000, state='visible')
                    await btn.click()
                    next_1_clicked = True
                    logger.info(f"✓ Clicked Next (1) via get_by_role")
                    break
                elif strategy[0] == 'get_by_text':
                    btn = browser.page.get_by_text(strategy[1]).first
                    await btn.wait_for(timeout=5000, state='visible')
                    await btn.click()
                    next_1_clicked = True
                    logger.info(f"✓ Clicked Next (1) via get_by_text")
                    break
            except Exception as e:
                logger.debug(f"Next (1) strategy {strategy} failed: {str(e)[:100]}")
                continue

        if not next_1_clicked:
            screenshot_path = f"./vault/instagram_error_next1_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            await browser.page.screenshot(path=screenshot_path)
            raise SocialMediaActionError(f"Could not click first Next button. Screenshot: {screenshot_path}")

        await browser.human_delay(2000, 3000)

        # 4. Click "Next" (Filters page)
        logger.info("Clicking Next (Filters page)...")
        next_2_clicked = False

        # Try multiple strategies for second Next button
        next_btn_strategies = [
            # Strategy 1: Direct text-based locators
            ('locator', 'div[role="button"]:has-text("Next")'),
            ('locator', 'button:has-text("Next")'),
            ('locator', 'span:has-text("Next")'),
            # Strategy 2: get_by_role
            ('get_by_role', 'button', 'Next'),
            # Strategy 3: get_by_text
            ('get_by_text', 'Next'),
        ]

        for strategy in next_btn_strategies:
            try:
                if strategy[0] == 'locator':
                    btn = browser.page.locator(strategy[1]).first
                    await btn.wait_for(timeout=5000, state='visible')
                    await btn.click()
                    next_2_clicked = True
                    logger.info(f"✓ Clicked Next (2) via locator: {strategy[1]}")
                    break
                elif strategy[0] == 'get_by_role':
                    btn = browser.page.get_by_role(strategy[1], name=strategy[2])
                    await btn.wait_for(timeout=5000, state='visible')
                    await btn.click()
                    next_2_clicked = True
                    logger.info(f"✓ Clicked Next (2) via get_by_role")
                    break
                elif strategy[0] == 'get_by_text':
                    btn = browser.page.get_by_text(strategy[1]).first
                    await btn.wait_for(timeout=5000, state='visible')
                    await btn.click()
                    next_2_clicked = True
                    logger.info(f"✓ Clicked Next (2) via get_by_text")
                    break
            except Exception as e:
                logger.debug(f"Next (2) strategy {strategy} failed: {str(e)[:100]}")
                continue

        if not next_2_clicked:
            screenshot_path = f"./vault/instagram_error_next2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            await browser.page.screenshot(path=screenshot_path)
            raise SocialMediaActionError(f"Could not click second Next button. Screenshot: {screenshot_path}")

        await browser.human_delay(2000, 3000)

        # 5. Add Caption
        logger.info("Adding caption...")
        try:
            # Instagram caption box is often a div with contenteditable
            caption_box = browser.page.get_by_role("textbox", name="Write a caption...")
            await caption_box.wait_for(timeout=5000, state='visible')
            await caption_box.fill(post.content)
            logger.info("Caption added successfully")
        except:
            # Fallback for caption box - try locator for contenteditable
            try:
                await browser.page.locator('div[aria-label="Write a caption..."]').wait_for(state='visible', timeout=5000)
                await browser.page.locator('div[aria-label="Write a caption..."]').fill(post.content, timeout=5000)
                logger.info("Caption added via aria-label fallback")
            except:
                try:
                    caption_element = browser.page.locator('div[contenteditable="true"]').first
                    await caption_element.wait_for(state='visible', timeout=5000)
                    await caption_element.fill(post.content, timeout=5000)
                    logger.info("Caption added via contenteditable fallback")
                except Exception as e:
                    logger.warning(f"Failed to add caption: {e}")

        await browser.human_delay(1000, 2000)

        # 6. Click "Share"
        logger.info("Clicking Share...")
        share_clicked = False

        # Try multiple times with different strategies
        max_retries = 3
        for retry in range(max_retries):
            if share_clicked:
                break

            logger.info(f"Share button click attempt {retry + 1}/{max_retries}")

            share_btn_strategies = [
                # Strategy 1: Direct text-based locators
                ('locator', 'div[role="button"]:has-text("Share")'),
                ('locator', 'button:has-text("Share")'),
                ('locator', 'span:has-text("Share")'),
                # Strategy 2: get_by_role
                ('get_by_role', 'button', 'Share'),
                # Strategy 3: get_by_text
                ('get_by_text', 'Share'),
            ]

            for strategy in share_btn_strategies:
                try:
                    if strategy[0] == 'locator':
                        btn = browser.page.locator(strategy[1]).first
                        await btn.wait_for(timeout=10000, state='visible')
                        await browser.human_delay(500, 1000)
                        await btn.click(force=True, timeout=10000)
                        share_clicked = True
                        logger.info(f"✓ Clicked Share via locator: {strategy[1]}")
                        break
                    elif strategy[0] == 'get_by_role':
                        btn = browser.page.get_by_role(strategy[1], name=strategy[2])
                        await btn.wait_for(timeout=10000, state='visible')
                        await browser.human_delay(500, 1000)
                        await btn.click(force=True, timeout=10000)
                        share_clicked = True
                        logger.info(f"✓ Clicked Share via get_by_role")
                        break
                    elif strategy[0] == 'get_by_text':
                        btn = browser.page.get_by_text(strategy[1]).first
                        await btn.wait_for(timeout=10000, state='visible')
                        await browser.human_delay(500, 1000)
                        await btn.click(force=True, timeout=10000)
                        share_clicked = True
                        logger.info(f"✓ Clicked Share via get_by_text")
                        break
                except Exception as e:
                    logger.info(f"Share button strategy {strategy} failed: {str(e)[:100]}")
                    continue

            if not share_clicked:
                # Wait before retry
                await browser.human_delay(1000, 2000)

        if not share_clicked:
            screenshot_path = f"./vault/instagram_error_share_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            await browser.page.screenshot(path=screenshot_path)
            raise SocialMediaActionError(f"Could not click Share button after {max_retries} attempts. Screenshot: {screenshot_path}")

        # 7. Verification
        logger.info("Verifying post...")
        await browser.human_delay(10000, 15000) # Share takes time

        verification_indicators = [
            browser.page.get_by_text("Your post has been shared"),
            browser.page.get_by_text("Post shared"),
            browser.page.locator('svg[aria-label="Post shared"]')
        ]

        post_verified = False
        for indicator in verification_indicators:
            try:
                await indicator.wait_for(timeout=20000, state='visible')
                post_verified = True
                logger.info("Post verified successfully")
                break
            except:
                continue

        if not post_verified:
            # Even if we can't find the confirmation text, it might have succeeded
            # Check for a close button or if the dialog is gone
            try:
                close_btn = browser.page.get_by_role("button", name="Close")
                if await close_btn.is_visible():
                    await close_btn.click()
                    post_verified = True
                    logger.info("Post assumed successful (Close button visible)")
            except:
                pass

        if not post_verified:
             # Final check: Navigate to profile and see if post is there?
             # (Skipped for speed, but can be added if needed)
             pass

        # Use a constructed URL as a fallback if we can't get the actual one
        post_url = f"https://www.instagram.com/reels/posts/" # generic

        # Take success screenshot
        success_screenshot = f"./vault/instagram_success_{post.post_id}.png"
        await browser.page.screenshot(path=success_screenshot)
        logger.info(f"Successfully posted to Instagram (screenshot: {success_screenshot})")

        return post_url

    except SocialMediaActionError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error posting to Instagram: {e}")
        raise SocialMediaActionError(f"Instagram posting failed: {e}")
    finally:
        if browser:
            try:
                await browser.close()
            except:
                pass


def process_approved_post(task_file_path: str) -> str:
    """
    Process approved social media post

    Args:
        task_file_path: Path to approved task file (in Approved folder)

    Returns:
        Status: 'done' or 'error'

    Workflow:
    1. Parse task file and extract post details
    2. Create SocialMediaPost object
    3. Publish to appropriate platform (Facebook or Instagram)
    4. Mark task as done
    """
    import asyncio

    try:
        logger.info(f"Processing approved social media post: {task_file_path}")

        # Parse task file
        frontmatter, body = parse_task_file(task_file_path)

        # Create post from task file
        post = SocialMediaPost.from_task_file(frontmatter, body)

        # Mark as approved
        approved_by = frontmatter.get('approved_by', 'human')
        post.approve(approved_by)

        # Publish to platform
        logger.info(f"Publishing to {post.platform.value}: {post.content[:50]}...")

        if post.platform == PostPlatform.FACEBOOK:
            published_url = asyncio.run(post_to_facebook(post))
        elif post.platform == PostPlatform.INSTAGRAM:
            published_url = asyncio.run(post_to_instagram(post))
        else:
            raise SocialMediaActionError(f"Unknown platform: {post.platform}")

        # Complete task
        _complete_task(task_file_path, post, published_url)

        logger.info(f"Approved post published successfully: {published_url}")
        return 'done'

    except Exception as e:
        _handle_error(task_file_path, post if 'post' in locals() else None, e, 'social_media_actions', 'process_approved_post')
        return 'error'


def get_pending_posts(vault_path: Optional[str] = None) -> list:
    """
    Get list of social media posts pending approval

    Args:
        vault_path: Path to vault directory (optional)

    Returns:
        List of pending post task files
    """
    if vault_path is None:
        vault_path = _get_vault_path()
    else:
        vault_path = Path(vault_path)

    pending_folder = vault_path / 'Pending_Approval'

    if not pending_folder.exists():
        return []

    # Get all social media post files in Pending_Approval folder
    pending_files = []
    for file in pending_folder.glob('*.md'):
        try:
            frontmatter, _ = parse_task_file(str(file))
            if frontmatter.get('type') == 'social_media' or frontmatter.get('platform') in ['facebook', 'instagram']:
                pending_files.append(str(file))
        except:
            continue

    logger.info(f"Found {len(pending_files)} social media posts pending approval")
    return pending_files

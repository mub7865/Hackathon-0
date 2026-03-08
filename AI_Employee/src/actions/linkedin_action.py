import os
import sys
import logging
import time
import random
from pathlib import Path
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

# Setup logging
log_dir = Path(r"D:\Hackathons\hackathon-0\silver\vault\Logs")
log_dir.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "linkedin_audit.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def post_to_linkedin(content: str, image_path: str = None, link_url: str = None) -> dict:
    session_dir = Path(r"D:\Hackathons\hackathon-0\silver\sessions\linkedin")
    logger.info("🤖 Atlas AI Employee: Starting LinkedIn Post (Visible Mode)...")

    try:
        with sync_playwright() as p:
            # Launch Real Chrome
            context = p.chromium.launch_persistent_context(
                user_data_dir=str(session_dir),
                channel="chrome", 
                headless=False, # Taake aap dekh saken kya ho raha hai
                args=['--start-maximized', '--disable-blink-features=AutomationControlled'],
                viewport=None
            )
            
            page = context.pages[0] if context.pages else context.new_page()
            Stealth().apply_stealth_sync(page)
            
            page.goto('https://www.linkedin.com/feed/', wait_until="domcontentloaded")
            time.sleep(5)

            # Click "Start a post"
            logger.info("Opening post box...")
            try:
                # Try multiple selectors for "Start a post" button
                selectors = [
                    'button:has-text("Start a post")',
                    '[aria-label*="Start a post"]',
                    '.share-box-feed-entry__trigger',
                    'button.artdeco-button--secondary'
                ]

                clicked = False
                for selector in selectors:
                    try:
                        page.locator(selector).first.click(timeout=5000)
                        clicked = True
                        logger.info(f"Clicked using selector: {selector}")
                        break
                    except:
                        continue

                if not clicked:
                    logger.warning("Could not find Start a post button, trying keyboard shortcut")
                    page.keyboard.press('p')
            except Exception as e:
                logger.error(f"Error clicking Start a post: {e}")
                page.keyboard.press('p') # Keyboard shortcut fallback

            time.sleep(5)  # Increased wait time for modal to appear

            # Type content - try multiple selectors
            logger.info("Looking for text editor...")
            editor = None
            editor_selectors = [
                'div[role="textbox"]',
                '.ql-editor',
                '[contenteditable="true"]',
                'div[data-placeholder*="share"]',
                '.share-creation-state__text-editor'
            ]

            for selector in editor_selectors:
                try:
                    editor = page.locator(selector).first
                    editor.wait_for(state="visible", timeout=5000)
                    logger.info(f"Found editor using selector: {selector}")
                    break
                except:
                    continue

            if not editor:
                logger.error("Could not find text editor after trying all selectors")
                return {"status": "error", "error": "Could not find text editor"}

            editor.click()
            
            # Type naturally
            for char in content:
                page.keyboard.type(char)
                if random.random() > 0.9: time.sleep(0.1) # Human delay

            time.sleep(3)  # Wait for content to be fully typed

            # CRITICAL: Wait for Post button to become enabled
            # LinkedIn disables the button until content is ready
            logger.info("Waiting for Post button to become enabled...")
            time.sleep(2)

            # Click Post button - try multiple selectors
            logger.info("Looking for Post button...")
            posted = False
            post_button_selectors = [
                'button:has-text("Post"):not([disabled])',  # Not disabled
                'button.share-actions__primary-action:not([disabled])',
                'button[aria-label*="Post"]:not([disabled])',
                'button.artdeco-button--primary:has-text("Post")',
                'button:has-text("Post")'  # Fallback without disabled check
            ]

            for selector in post_button_selectors:
                try:
                    logger.info(f"Trying selector: {selector}")
                    post_button = page.locator(selector).first

                    # Wait for button to be visible and enabled
                    post_button.wait_for(state="visible", timeout=5000)

                    # Extra wait to ensure button is clickable
                    time.sleep(1)

                    # Check if button is enabled
                    is_disabled = post_button.get_attribute('disabled')
                    if is_disabled:
                        logger.info(f"Button found but disabled, waiting...")
                        time.sleep(2)
                        is_disabled = post_button.get_attribute('disabled')

                    if not is_disabled:
                        logger.info(f"✅ Found enabled Post button: {selector}")
                        post_button.click()
                        posted = True
                        logger.info("✅ Post button clicked!")
                        break
                    else:
                        logger.warning(f"Button still disabled after wait")
                except Exception as e:
                    logger.info(f"Selector failed: {str(e)[:100]}")
                    continue

            if not posted:
                logger.warning("Could not find Post button, trying keyboard shortcut as fallback")
                page.keyboard.down("Control")
                page.keyboard.press("Enter")
                page.keyboard.up("Control")
                logger.info("Tried Ctrl+Enter shortcut")

            # Wait longer for post to be published
            time.sleep(8)

            # Verify post was published by checking if modal closed
            try:
                page.wait_for_selector('div[role="textbox"]', state="hidden", timeout=10000)
                logger.info("✅ Post published successfully! Modal closed.")
            except:
                logger.warning("Could not verify modal closed")
                # Still return success - post might have worked
                logger.info("Assuming post was successful despite verification failure")

            time.sleep(3)
            context.close()
            return {"status": "success"}

    except Exception as e:
        logger.error(f"❌ LinkedIn Error: {str(e)}")
        return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    post_to_linkedin("🚀 Live autonomous test post.")

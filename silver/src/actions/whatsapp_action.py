import os
import sys
import logging
import time
import subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

# Add project root to path
project_root = Path(r"D:\Hackathons\hackathon-0\silver")
sys.path.insert(0, str(project_root))

from src.utils.logger import setup_logger

# Setup logging
log_dir = project_root / "vault" / "Logs"
log_dir.mkdir(parents=True, exist_ok=True)
logger = setup_logger('whatsapp-action', str(log_dir))

def send_whatsapp(to: str, message: str, media_url: str = None, retries: int = 2) -> dict:
    """
    Send WhatsApp message via WhatsApp Web automation

    Returns:
        dict: {"status": "success"} or {"status": "error", "error": "message"}
    """
    # Use same session as watcher (wa_fresh)
    # NOTE: Orchestrator handles stopping/restarting watcher to avoid session conflicts
    session_dir = Path(r"D:\Hackathons\hackathon-0\silver\sessions\wa_fresh")

    logger.info(f"Preparing to send WhatsApp message to {to}...")

    # Validate recipient
    if not to or to == "None":
        logger.error(f"Invalid recipient: {to}")
        return {"status": "error", "error": f"Invalid recipient: {to}"}

    # Ensure session directory exists
    session_dir.mkdir(parents=True, exist_ok=True)

    for attempt in range(retries):
        try:
            with sync_playwright() as p:
                    context = p.chromium.launch_persistent_context(
                        user_data_dir=str(session_dir),
                        channel="chrome",
                        headless=False,  # Non-headless - WhatsApp Web blocks headless browsers
                        args=['--disable-blink-features=AutomationControlled', '--no-sandbox', '--disable-gpu']
                    )

                    # Use existing page (same as watcher) - already logged in
                    page = context.pages[0] if context.pages else context.new_page()
                    Stealth().apply_stealth_sync(page)

                    try:
                        logger.info("Navigating to WhatsApp Web...")
                        page.goto('https://web.whatsapp.com', timeout=60000)

                        # Wait for chat pane to load
                        page.wait_for_selector('#pane-side', timeout=60000)
                        logger.info("WhatsApp Web loaded - chat pane visible")
                        time.sleep(5)

                        # Press Escape multiple times to dismiss any popups
                        logger.info("Dismissing any popups...")
                        for _ in range(3):
                            page.keyboard.press("Escape")
                            time.sleep(1)
                        time.sleep(2)

                        # Screenshot 1: Before search
                        page.screenshot(path=str(log_dir / f"step1_before_search_{attempt+1}.png"))

                        # Click on search box directly (avoid Ctrl+F which causes focus issues)
                        logger.info(f"Searching for contact: {to}")
                        search_box = None
                        search_selectors = [
                            'div[contenteditable="true"][data-tab="3"]',  # Main search box
                            'div[role="textbox"][title="Search input textbox"]',  # Alternative
                            'div[contenteditable="true"]._ak1l',  # Another variant
                        ]

                        for selector in search_selectors:
                            try:
                                search_box = page.wait_for_selector(selector, timeout=5000)
                                if search_box:
                                    logger.info(f"Found search box with selector: {selector}")
                                    search_box.click()
                                    time.sleep(1)
                                    break
                            except Exception as e:
                                logger.warning(f"Search selector {selector} failed: {e}")
                                continue

                        if not search_box:
                            logger.error("Could not find search box")
                            raise Exception("Search box not found")

                        # Screenshot 2: After clicking search box
                        page.screenshot(path=str(log_dir / f"step2_after_search_click_{attempt+1}.png"))

                        # Type the contact name/number
                        page.keyboard.type(to, delay=100)
                        time.sleep(3)

                        # Screenshot 3: After typing contact
                        page.screenshot(path=str(log_dir / f"step3_after_typing_{attempt+1}.png"))

                        # Press Enter to open first result
                        logger.info("Opening chat with Enter key...")
                        page.keyboard.press("Enter")
                        time.sleep(3)

                        # Screenshot 4: After opening chat
                        page.screenshot(path=str(log_dir / f"step4_after_opening_chat_{attempt+1}.png"))

                        # Wait for chat to fully load
                        logger.info("Waiting for chat to load...")
                        time.sleep(2)

                        # Click on compose box to ensure focus - use JavaScript for reliability
                        logger.info("Clicking compose box to ensure focus...")
                        compose_focused = False
                        try:
                            # Try multiple selectors for compose box
                            compose_selectors = [
                                'div[contenteditable="true"][data-tab="10"]',  # New WhatsApp
                                'div[contenteditable="true"]._ak1l',  # Alternative
                                'div[role="textbox"]',  # Generic
                                'div[contenteditable="true"]',  # Most generic
                            ]

                            compose_box = None
                            for selector in compose_selectors:
                                try:
                                    compose_box = page.wait_for_selector(selector, timeout=5000)
                                    if compose_box:
                                        logger.info(f"Found compose box with selector: {selector}")
                                        # Click using JavaScript for reliability
                                        page.evaluate('(element) => element.click()', compose_box)
                                        time.sleep(0.5)
                                        # Force focus using JavaScript
                                        page.evaluate('(element) => element.focus()', compose_box)
                                        time.sleep(0.5)
                                        compose_focused = True
                                        logger.info("Compose box clicked and focused via JavaScript")
                                        break
                                except Exception as e:
                                    logger.warning(f"Selector {selector} failed: {e}")
                                    continue

                            if not compose_focused:
                                logger.error("Could not find or focus compose box with any selector")
                                raise Exception("Compose box not found")
                        except Exception as e:
                            logger.error(f"Could not click compose box: {e}")
                            raise e

                        # Type message
                        logger.info("Typing message...")
                        for line in message.split('\n'):
                            page.keyboard.type(line, delay=50)  # Add delay between keystrokes
                            if line != message.split('\n')[-1]:  # Not last line
                                page.keyboard.press('Shift+Enter')
                                time.sleep(0.5)

                        # CRITICAL: Wait for send button to appear after typing
                        logger.info("Waiting for send button to appear...")
                        time.sleep(3)

                        # Screenshot before sending
                        page.screenshot(path=str(log_dir / f"step5_before_send_{attempt+1}.png"))

                        # Send the message - try multiple methods with proper waiting
                        logger.info("Attempting to send message...")
                        message_sent = False

                        # Method 1: Direct click on send button (most reliable)
                        try:
                            logger.info("Method 1: Trying direct button click...")
                            send_button = page.wait_for_selector(
                                '[data-testid="send"]',
                                state='visible',
                                timeout=10000
                            )
                            if send_button:
                                logger.info("Send button found and visible")
                                # Click multiple times to ensure it registers
                                send_button.click()
                                time.sleep(0.5)
                                send_button.click()
                                logger.info("✓ Clicked send button")
                                message_sent = True
                                time.sleep(3)
                        except Exception as e1:
                            logger.warning(f"Method 1 failed: {e1}")

                        # Method 2: JavaScript click (if Method 1 failed)
                        if not message_sent:
                            try:
                                logger.info("Method 2: Trying JavaScript click...")
                                page.evaluate('document.querySelector("[data-testid=send]").click()')
                                logger.info("✓ Sent via JavaScript click")
                                message_sent = True
                                time.sleep(3)
                            except Exception as e2:
                                logger.warning(f"Method 2 failed: {e2}")

                        # Method 3: Enter key as last resort
                        if not message_sent:
                            try:
                                logger.info("Method 3: Trying Enter key...")
                                # Re-focus compose box
                                compose_box = page.query_selector('div[contenteditable="true"][data-tab="10"]')
                                if compose_box:
                                    page.evaluate('(element) => element.focus()', compose_box)
                                    time.sleep(0.5)
                                page.keyboard.press("Enter")
                                logger.info("✓ Pressed Enter key")
                                message_sent = True
                                time.sleep(3)
                            except Exception as e3:
                                logger.error(f"Method 3 failed: {e3}")

                        if not message_sent:
                            logger.error("All send methods failed")
                            raise Exception("Could not send message with any method")

                        # Wait longer for message to actually send
                        logger.info("Waiting for message to send...")
                        time.sleep(5)

                        # Screenshot after sending
                        page.screenshot(path=str(log_dir / f"step6_after_send_{attempt+1}.png"))

                        # Verify message was sent by checking if compose box is empty
                        logger.info("Verifying message was sent...")
                        try:
                            # Check if compose box is empty (most reliable indicator)
                            compose_box = page.query_selector('div[contenteditable="true"][data-tab="10"]')
                            if not compose_box:
                                # Try alternative selector
                                compose_box = page.query_selector('div[role="textbox"]')

                            if compose_box:
                                text_content = compose_box.inner_text()
                                logger.info(f"Compose box content after send: '{text_content}'")

                                if not text_content or text_content.strip() == "":
                                    logger.info("✓ Compose box is empty - message SENT successfully")
                                    # Wait a bit more to ensure message is fully sent
                                    time.sleep(2)
                                    context.close()
                                    return {"status": "success"}
                                else:
                                    logger.error(f"✗ Compose box still has text: '{text_content}' - message NOT sent")
                                    page.screenshot(path=str(log_dir / f"verification_failed_{attempt+1}.png"))
                                    raise Exception("Message still in compose box - not sent")
                            else:
                                logger.error("Could not find compose box for verification")
                                raise Exception("Compose box not found for verification")

                        except Exception as verify_error:
                            logger.error(f"Verification failed: {verify_error}")
                            raise verify_error

                    except Exception as e:
                        logger.error(f"Action failed on attempt {attempt + 1}: {e}")
                        page.screenshot(path=str(log_dir / f"whatsapp_action_error_{attempt+1}.png"))
                        context.close()
                        if attempt < retries - 1:
                            logger.info("Retrying after a short delay...")
                            time.sleep(10)
                        else:
                            raise e # Raise final error

        except Exception as e:
            logger.error(f"A critical error occurred: {e}")
            if "Target page, context or browser has been closed" in str(e) or "session is already in use" in str(e).lower():
                logger.warning("Session may be locked by another process (watcher?). Waiting and retrying...")
                if attempt < retries - 1:
                    time.sleep(15) # Wait longer if it's a lock
                    continue
                else:
                    return {"status": "error", "error": f"Failed after multiple retries. Details: {e}"}
            else:
                # Always return a valid dict, never None
                return {"status": "error", "error": str(e)}

    # Always return a valid dict, never None
    return {"status": "error", "error": "Failed after all retries."}


if __name__ == "__main__":
    # Example usage for testing
    test_recipient = "+923212322687" # Replace with a valid number for testing
    test_message = "This is an automated test message from the AI Employee.\nPlease ignore."
    send_whatsapp(test_recipient, test_message)

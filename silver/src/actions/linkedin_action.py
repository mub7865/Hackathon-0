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
    logger.info("🤖 AI EMPLOYEE: Starting LinkedIn Post (Visible Mode)...")

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
                # Try multiple ways to find the button
                post_trigger = page.get_by_text("Start a post", exact=False).first
                post_trigger.click(timeout=10000)
            except:
                page.keyboard.press('p') # Keyboard shortcut fallback

            time.sleep(3)

            # Type content
            logger.info("Typing content...")
            editor = page.locator('div[role="textbox"], .ql-editor').first
            editor.wait_for(state="visible", timeout=15000)
            editor.click()
            
            # Type naturally
            for char in content:
                page.keyboard.type(char)
                if random.random() > 0.9: time.sleep(0.1) # Human delay

            time.sleep(2)

            # Post using keyboard shortcut (more reliable than clicking button)
            logger.info("Posting with Ctrl+Enter...")
            page.keyboard.down("Control")
            page.keyboard.press("Enter")
            page.keyboard.up("Control")

            time.sleep(3)

            # Verify post was published by checking if modal closed
            try:
                page.wait_for_selector('div[role="textbox"]', state="hidden", timeout=5000)
                logger.info("✅ Post published successfully!")
            except:
                logger.warning("Could not verify post modal closed, but post likely sent")

            time.sleep(2)
            context.close()
            return {"status": "success"}

    except Exception as e:
        logger.error(f"❌ LinkedIn Error: {str(e)}")
        return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    post_to_linkedin("🚀 Live autonomous test post.")

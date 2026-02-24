#!/usr/bin/env python3
"""
WhatsApp Action - Send messages via WhatsApp Web using Playwright
FREE method - no Twilio API needed!
"""

import os
import sys
import time
import logging
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def send_whatsapp_web(to: str, message: str) -> dict:
    """
    Send WhatsApp message via WhatsApp Web using Playwright

    Args:
        to: Phone number (format: +923212322687)
        message: Message text

    Returns:
        dict: Result with status
    """

    logger.info("=" * 60)
    logger.info("WHATSAPP WEB ACTION - REAL MODE (Playwright)")
    logger.info("=" * 60)
    logger.info(f"To: {to}")
    logger.info(f"Message: {message[:100]}..." if len(message) > 100 else f"Message: {message}")
    logger.info("=" * 60)

    # Use persistent session
    base_dir = Path(__file__).parent.parent.parent
    session_dir = base_dir / "sessions" / "whatsapp_fresh_final"

    if not session_dir.exists():
        raise ValueError(f"WhatsApp session not found at {session_dir}. Please run setup first.")

    try:
        with sync_playwright() as p:
            # Launch browser with persistent context
            context = p.chromium.launch_persistent_context(
                user_data_dir=str(session_dir),
                headless=False  # Keep visible for debugging
            )
            page = context.pages[0] if context.pages else context.new_page()

            # Set timeout
            page.set_default_timeout(60000)

            try:
                # Navigate to WhatsApp Web
                logger.info("Navigating to WhatsApp Web...")
                page.goto('https://web.whatsapp.com')

                # Wait for chat list to load (means we're logged in)
                logger.info("Waiting for WhatsApp to load...")
                page.wait_for_selector('[data-testid="chat-list"]', timeout=30000)

                # Search for contact
                logger.info(f"Searching for contact: {to}")
                search_box = page.wait_for_selector('[data-testid="chat-list-search"]')
                search_box.click()
                time.sleep(1)

                # Type phone number
                page.keyboard.type(to)
                time.sleep(2)

                # Click on first result
                logger.info("Opening chat...")
                first_result = page.wait_for_selector('[data-testid="cell-frame-container"]')
                first_result.click()
                time.sleep(2)

                # Type message
                logger.info("Typing message...")
                message_box = page.wait_for_selector('[data-testid="conversation-compose-box-input"]')
                message_box.click()

                # Type message line by line (to handle multiline)
                for line in message.split('\n'):
                    page.keyboard.type(line)
                    page.keyboard.press('Shift+Enter')

                time.sleep(1)

                # Send message
                logger.info("Sending message...")
                send_button = page.wait_for_selector('[data-testid="send"]')
                send_button.click()
                time.sleep(2)

                logger.info(f"✅ WhatsApp message sent successfully to {to}")
                logger.info("=" * 60)

                # Log to file
                log_dir = base_dir / "vault" / "Logs"
                log_dir.mkdir(parents=True, exist_ok=True)

                log_file = log_dir / f"whatsapp-actions-{datetime.now().strftime('%Y-%m-%d')}.log"
                with open(log_file, 'a') as f:
                    f.write(f"\n{'=' * 60}\n")
                    f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                    f.write(f"To: {to}\n")
                    f.write(f"Message: {message}\n")
                    f.write(f"Status: SUCCESS (sent via WhatsApp Web)\n")
                    f.write(f"{'=' * 60}\n")

                return {
                    "status": "success",
                    "to": to,
                    "mode": "whatsapp_web",
                    "logged_to": str(log_file)
                }

            finally:
                context.close()

    except Exception as e:
        logger.error(f"❌ Failed to send WhatsApp message: {e}")
        logger.error("=" * 60)

        # Log error to file
        log_dir = Path(__file__).parent.parent.parent / "vault" / "Logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / f"whatsapp-actions-{datetime.now().strftime('%Y-%m-%d')}.log"
        with open(log_file, 'a') as f:
            f.write(f"\n{'=' * 60}\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write(f"To: {to}\n")
            f.write(f"Status: FAILED\n")
            f.write(f"Error: {str(e)}\n")
            f.write(f"{'=' * 60}\n")

        return {
            "status": "error",
            "error": str(e),
            "mode": "whatsapp_web",
            "logged_to": str(log_file)
        }


if __name__ == "__main__":
    # Test
    result = send_whatsapp_web(
        to="+923212322687",
        message="Test message from Silver Tier AI Employee using WhatsApp Web automation!"
    )
    print(f"\nResult: {result}\n")

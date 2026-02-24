#!/usr/bin/env python3
"""
Test if manual WhatsApp session works with Playwright
"""

import os
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
from dotenv import load_dotenv

load_dotenv()

def test_manual_session():
    """Test if manual session works with Playwright"""

    session_path = Path(os.getenv('WHATSAPP_SESSION', 'sessions/wa_1770143130'))

    print("=" * 60)
    print("Testing Manual WhatsApp Session with Playwright")
    print("=" * 60)
    print(f"\nSession: {session_path}")
    print(f"Session exists: {session_path.exists()}")

    with sync_playwright() as p:
        print("\nLaunching browser with manual session...")

        # Launch with same config as watcher
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(session_path),
            headless=False,  # Visible to see what's happening
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-infobars',
                '--window-size=1920,1080',
            ],
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='America/New_York',
        )

        page = context.pages[0] if context.pages else context.new_page()

        # Apply stealth
        print("Applying stealth...")
        stealth = Stealth()
        stealth.apply_stealth_sync(page)

        print("Loading WhatsApp Web...")
        page.goto('https://web.whatsapp.com', wait_until='domcontentloaded')

        # Wait a bit for page to load
        import time
        time.sleep(5)

        # Take screenshot
        screenshot_path = 'whatsapp_manual_session_test.png'
        page.screenshot(path=screenshot_path)
        print(f"\nScreenshot saved: {screenshot_path}")

        # Check for various elements
        print("\n" + "=" * 60)
        print("Diagnostic Results:")
        print("=" * 60)

        # Check for QR code
        try:
            qr = page.locator('canvas[aria-label="Scan me!"]')
            if qr.is_visible(timeout=2000):
                print("QR Code: FOUND (Not logged in)")
            else:
                print("QR Code: NOT VISIBLE")
        except:
            print("QR Code: NOT FOUND")

        # Check for chat list (logged in)
        try:
            chat_list = page.locator('[data-testid="chat-list"]')
            if chat_list.is_visible(timeout=2000):
                print("Chat List: FOUND (Logged in successfully!)")
            else:
                print("Chat List: NOT VISIBLE")
        except:
            print("Chat List: NOT FOUND")

        # Check for database error
        try:
            page_text = page.inner_text('body')
            if 'database' in page_text.lower():
                print("Database Error: DETECTED")
                print(f"   Error text: {[line for line in page_text.split('\\n') if 'database' in line.lower()]}")
            else:
                print("Database Error: NOT DETECTED")
        except:
            print("Database Error: Could not check")

        # Get page title
        try:
            title = page.title()
            print(f"\nPage Title: {title}")
        except:
            pass

        print(f"Current URL: {page.url}")

        print("\n" + "=" * 60)
        print("Browser will stay open for 30 seconds...")
        print("Check the browser window to see what's displayed")
        print("=" * 60 + "\n")

        time.sleep(30)

        context.close()

    print("\nTest complete!")
    print(f"Check screenshot: {screenshot_path}\n")

if __name__ == "__main__":
    try:
        test_manual_session()
    except KeyboardInterrupt:
        print("\n\nCancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

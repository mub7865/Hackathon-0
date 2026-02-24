#!/usr/bin/env python3
"""
WhatsApp Login Helper
Opens WhatsApp Web for QR code scanning
"""
from playwright.sync_api import sync_playwright
import time
from pathlib import Path

def login_whatsapp():
    session_dir = Path(r"D:\Hackathons\hackathon-0\silver\sessions\wa_fresh")

    print("=" * 60)
    print("WhatsApp Login Helper")
    print("=" * 60)
    print("\nOpening WhatsApp Web...")
    print("Please scan the QR code with your phone")
    print("You have 90 seconds to scan\n")

    try:
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir=str(session_dir),
                channel="chrome",
                headless=False,
                args=['--disable-blink-features=AutomationControlled', '--no-sandbox']
            )

            page = context.new_page()
            page.goto('https://web.whatsapp.com', timeout=60000)

            print("Browser opened!")
            print("Waiting 90 seconds for you to scan QR code...\n")

            # Wait for login
            time.sleep(90)

            # Check if logged in
            try:
                page.wait_for_selector('[data-testid="chat-list-search"]', timeout=5000)
                print("\nSUCCESS! WhatsApp Web logged in!")
                print("Session saved. You can now send WhatsApp messages.\n")
            except:
                print("\nCould not detect login.")
                print("If you scanned the QR code, the session should still be saved.")
                print("Try sending a test message to verify.\n")

            print("Closing browser in 5 seconds...")
            time.sleep(5)
            context.close()

        print("\nDone! WhatsApp session is ready.")

    except Exception as e:
        print(f"\nError: {e}")
        print("Please try again or check your internet connection.")

if __name__ == "__main__":
    login_whatsapp()

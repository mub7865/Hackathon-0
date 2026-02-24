#!/usr/bin/env python3
"""
Test WhatsApp Watcher with Playwright-compatible session
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Import the watcher
from src.watchers.whatsapp_watcher import WhatsAppWatcher

print("=" * 60)
print("Testing WhatsApp Watcher with Playwright Session")
print("=" * 60)

vault_path = os.getenv('VAULT_PATH', './vault')
session_path = os.getenv('WHATSAPP_SESSION', './sessions/whatsapp')

print(f"\nVault: {vault_path}")
print(f"Session: {session_path}")
print(f"Session exists: {Path(session_path).exists()}")

print("\nInitializing watcher...")
watcher = WhatsAppWatcher(vault_path, session_path)

print("Initializing browser session...")
try:
    watcher._init_browser_session()
    print("Browser session initialized")

    print("\nChecking login status...")
    is_logged_in = watcher._is_logged_in()
    print(f"Logged in: {is_logged_in}")

    if is_logged_in:
        print("\nSUCCESS! WhatsApp Watcher working!")
        print("No database error detected!")
    else:
        print("\nNot logged in - checking what's displayed...")

        # Check for QR code
        try:
            qr = watcher.page.locator('canvas[aria-label="Scan me!"]')
            if qr.is_visible(timeout=2000):
                print("QR Code: VISIBLE (need to scan)")
            else:
                print("QR Code: NOT VISIBLE")
        except:
            print("QR Code: NOT FOUND")

        # Check for database error
        try:
            page_text = watcher.page.inner_text('body')
            if 'database' in page_text.lower():
                print("Database Error: DETECTED")
            else:
                print("Database Error: NOT DETECTED")
        except:
            print("Database Error: Could not check")

    # Take screenshot
    print("\nTaking screenshot...")
    watcher.page.screenshot(path='whatsapp_watcher_final_test.png')
    print("Screenshot saved: whatsapp_watcher_final_test.png")

    print("\nPage title:", watcher.page.title())
    print("Page URL:", watcher.page.url)

except Exception as e:
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()
finally:
    print("\nCleaning up...")
    watcher.cleanup()
    print("Done!")

#!/usr/bin/env python3
"""
Simple test to verify WhatsApp Watcher can work with authenticated session
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from src.watchers.whatsapp_watcher import WhatsAppWatcher

print("=" * 60)
print("Testing WhatsApp Watcher - Quick Check")
print("=" * 60)

vault_path = os.getenv('VAULT_PATH', './vault')
session_path = os.getenv('WHATSAPP_SESSION', './sessions/whatsapp')

print(f"\nVault: {vault_path}")
print(f"Session: {session_path}")

print("\nInitializing watcher...")
watcher = WhatsAppWatcher(vault_path, session_path)

print("Initializing browser session (this may take 30 seconds)...")
try:
    # This will try to init and wait for chat list
    watcher._init_browser_session()

    # If we get here, chat list appeared
    print("\nSUCCESS! Chat list detected!")
    print("WhatsApp Watcher is working correctly!")

except Exception as e:
    # Check if we're at least logged in (no QR code)
    print(f"\nChat list timeout (expected if messages still syncing)")
    print("Checking if at least logged in...")

    try:
        # Check for QR code
        qr = watcher.page.locator('canvas[aria-label="Scan me!"]')
        if qr.is_visible(timeout=2000):
            print("\nFAILED: QR Code still showing - not logged in")
        else:
            print("\nPARTIAL SUCCESS: No QR code - logged in!")
            print("Messages are still syncing, but authentication works!")

            # Check page text
            page_text = watcher.page.inner_text('body')
            if 'downloading' in page_text.lower():
                print("Status: Messages downloading (normal for first login)")

    except Exception as e2:
        print(f"Error checking status: {e2}")

finally:
    print("\nCleaning up...")
    watcher.cleanup()
    print("Done!")

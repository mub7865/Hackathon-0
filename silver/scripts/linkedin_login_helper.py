#!/usr/bin/env python3
"""
LinkedIn Login Helper - Opens LinkedIn in persistent browser for manual login
"""
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

session_dir = Path(r"D:\Hackathons\hackathon-0\silver\sessions\linkedin")

print("🔐 Opening LinkedIn for manual login...")
print("📋 Instructions:")
print("   1. Log in to LinkedIn if not already logged in")
print("   2. Verify you can see your feed")
print("   3. Close the browser window when done")
print("\n⏳ Opening browser in 3 seconds...")
time.sleep(3)

with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        user_data_dir=str(session_dir),
        channel="chrome",
        headless=False,
        args=['--start-maximized'],
        viewport=None
    )

    page = context.pages[0] if context.pages else context.new_page()
    page.goto('https://www.linkedin.com/feed/')

    print("\n✅ Browser opened. Please log in if needed.")
    print("⚠️  Press Ctrl+C when you're done to close this script...")

    try:
        # Keep the browser open until user closes it or presses Ctrl+C
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Closing browser...")
        context.close()
        print("✅ Session saved. You can now run the posting automation.")

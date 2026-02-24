#!/usr/bin/env python3
"""
LinkedIn Login Helper - Simple Version
Opens LinkedIn and waits for manual login (no time limit)
"""
from playwright.sync_api import sync_playwright
import time
from pathlib import Path

def login_linkedin():
    session_dir = Path(r"D:\Hackathons\hackathon-0\silver\sessions\linkedin")

    print("=" * 60)
    print("🔐 LinkedIn Login Helper (Simple)")
    print("=" * 60)
    print("\n💼 Opening LinkedIn...")
    print("👉 Login manually (use Email/Password, NOT Google)")
    print("⏰ Take your time - no rush!")
    print("\n💡 TIP: Use email/password instead of Google login")
    print("   Email: muhammadubaidansari145@gmail.com")
    print("   Password: ubaid7865\n")

    try:
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir=str(session_dir),
                channel="chrome",
                headless=False,
                args=['--start-maximized', '--disable-blink-features=AutomationControlled'],
                viewport=None
            )

            page = context.pages[0] if context.pages else context.new_page()
            
            # Go to LinkedIn login page
            print("✅ Browser opened!")
            page.goto('https://www.linkedin.com/login', timeout=60000)
            
            print("\n📝 Please login now:")
            print("   1. Enter email: muhammadubaidansari145@gmail.com")
            print("   2. Enter password: ubaid7865")
            print("   3. Click 'Sign in'")
            print("   4. Wait for feed to load")
            print("\n⚠️  Press Ctrl+C when you're done and logged in\n")

            try:
                # Keep browser open until user presses Ctrl+C
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n\n🔍 Checking if logged in...")
                
                # Try to verify login
                try:
                    page.goto('https://www.linkedin.com/feed/', timeout=10000)
                    page.wait_for_selector('[data-test-id="feed-tab"]', timeout=5000)
                    print("✅ SUCCESS! LinkedIn logged in!")
                except:
                    print("⚠️  Could not verify login, but session should be saved")
                
                print("🔒 Closing browser...")
                context.close()
                print("\n✅ Done! LinkedIn session is ready.\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Please try again.")

if __name__ == "__main__":
    login_linkedin()

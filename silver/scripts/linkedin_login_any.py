#!/usr/bin/env python3
"""
LinkedIn Login Helper - Works with ANY account
Supports Google login, Email/Password, or any other method
"""
from playwright.sync_api import sync_playwright
import time
from pathlib import Path

def login_linkedin():
    session_dir = Path(r"D:\Hackathons\hackathon-0\silver\sessions\linkedin")

    print("=" * 60)
    print("🔐 LinkedIn Login Helper")
    print("=" * 60)
    print("\n💼 Opening LinkedIn...")
    print("👉 Login with YOUR account")
    print("⏰ Take your time - no rush!")
    print("\n✅ Supported login methods:")
    print("   - Continue with Google")
    print("   - Email/Password")
    print("   - Any other method")
    print("\n📝 Instructions:")
    print("   1. Browser will open")
    print("   2. Choose your login method")
    print("   3. Complete the login")
    print("   4. Wait for feed to load")
    print("   5. Press Ctrl+C when done\n")

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
            
            print("\n🔓 Please login now with your preferred method...")
            print("⏳ Waiting for you to complete login...")
            print("\n⚠️  Press Ctrl+C when you see your LinkedIn feed\n")

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
                    print("🎉 Session saved successfully!")
                except:
                    print("⚠️  Could not verify login automatically")
                    print("💡 If you can see your feed, the session is saved")
                
                print("\n🔒 Closing browser...")
                context.close()
                print("\n✅ Done! LinkedIn session is ready.")
                print("🚀 You can now post to LinkedIn automatically!\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Please try again or check your internet connection.")

if __name__ == "__main__":
    login_linkedin()

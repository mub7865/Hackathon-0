#!/usr/bin/env python3
"""
Generate Gmail OAuth Token - Simplest Version

This script uses the simplest possible OAuth flow.
It will print the URL and wait for you to complete authentication.

Usage:
    python scripts/generate_gmail_token_simple.py
"""

import os
import json
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import socket

# Gmail API scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.compose'
]

def find_free_port():
    """Find a free port to use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port

def generate_token():
    """Generate Gmail OAuth token"""

    # Get paths
    base_dir = Path(__file__).parent.parent
    creds_file = base_dir / '.credentials' / 'gmail-credentials.json'
    token_file = base_dir / '.credentials' / 'gmail-token.json'

    print("\n" + "="*70)
    print("🔐 Gmail OAuth Token Generator - Simple Version")
    print("="*70)
    print(f"\nCredentials: {creds_file}")
    print(f"Token will be saved to: {token_file}\n")

    # Check if credentials exist
    if not creds_file.exists():
        print(f"❌ Error: Credentials file not found")
        return False

    creds = None

    # Check if token already exists and is valid
    if token_file.exists():
        print("📄 Checking existing token...")
        try:
            creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)

            if creds.valid:
                print("✅ Token is already valid!")
                return True

            if creds.expired and creds.refresh_token:
                print("🔄 Refreshing expired token...")
                try:
                    creds.refresh(Request())
                    with open(token_file, 'w') as f:
                        f.write(creds.to_json())
                    print("✅ Token refreshed successfully!")
                    return True
                except Exception as e:
                    print(f"⚠️  Refresh failed: {e}")
                    print("Will generate new token...\n")
        except Exception as e:
            print(f"⚠️  Token invalid: {e}\n")

    # Generate new token
    print("="*70)
    print("🌐 GENERATING NEW TOKEN")
    print("="*70)
    print()
    print("IMPORTANT INSTRUCTIONS:")
    print("1. A URL will appear below")
    print("2. Copy the ENTIRE URL")
    print("3. Open it in your Windows browser")
    print("4. Sign in and click 'Allow'")
    print("5. Browser will redirect to localhost")
    print("6. Wait here - token will save automatically")
    print()
    print("="*70)

    input("\nPress ENTER to start...")

    try:
        # Find a free port
        port = find_free_port()
        print(f"\n🔌 Using port: {port}")

        # Create flow
        flow = InstalledAppFlow.from_client_secrets_file(
            str(creds_file),
            SCOPES,
            redirect_uri=f'http://localhost:{port}/'
        )

        print("\n" + "="*70)
        print("🔗 COPY THIS URL AND OPEN IN BROWSER:")
        print("="*70)
        print()

        # This will print the URL and start the server
        # Setting open_browser=False prevents automatic browser opening
        creds = flow.run_local_server(
            port=port,
            open_browser=False,
            authorization_prompt_message='',
            success_message='✅ Success! You can close this window and return to terminal.'
        )

        print("\n✅ Authentication successful!")

        # Save token
        token_file.parent.mkdir(parents=True, exist_ok=True)
        with open(token_file, 'w') as f:
            f.write(creds.to_json())

        print(f"💾 Token saved to: {token_file}")

        # Verify
        if token_file.exists():
            size = token_file.stat().st_size
            print(f"✅ Verified: {size} bytes")

            if size > 100:
                print("\n" + "="*70)
                print("✅ SUCCESS! Gmail token is ready!")
                print("="*70)
                return True
            else:
                print("⚠️  Warning: Token file too small")
                return False
        else:
            print("❌ Token file not created")
            return False

    except Exception as e:
        print(f"\n❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = generate_token()
        if success:
            print("\n✅ Next steps:")
            print("1. Test: python src/watchers/gmail_watcher.py")
            print("2. Continue with STEP 2 in SETUP_GUIDE.md\n")
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelled")
        exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        exit(1)

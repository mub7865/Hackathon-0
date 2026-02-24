#!/usr/bin/env python3
"""
Generate Gmail OAuth Token - Manual Browser Version

This script generates the OAuth token for Gmail API access.
It prints the URL for you to open manually in your browser.

Usage:
    python scripts/generate_gmail_token_manual.py
"""

import os
import json
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Gmail API scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.compose'
]

def generate_token():
    """Generate Gmail OAuth token with manual browser step"""

    # Get paths
    base_dir = Path(__file__).parent.parent
    creds_file = base_dir / '.credentials' / 'gmail-credentials.json'
    token_file = base_dir / '.credentials' / 'gmail-token.json'

    print("\n" + "="*70)
    print("🔐 Gmail OAuth Token Generator (Manual Browser Version)")
    print("="*70)
    print(f"\nCredentials file: {creds_file}")
    print(f"Token will be saved to: {token_file}\n")

    # Check if credentials exist
    if not creds_file.exists():
        print(f"❌ Error: Credentials file not found at {creds_file}")
        print("\nPlease follow these steps:")
        print("1. Go to Google Cloud Console")
        print("2. Create OAuth credentials")
        print("3. Download and save to .credentials/gmail-credentials.json")
        return False

    creds = None

    # Check if token already exists
    if token_file.exists():
        print("📄 Found existing token file")
        try:
            creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)

            if creds.valid:
                print("✅ Token is already valid!")
                print("\n" + "="*70)
                print("✅ Gmail OAuth token is ready!")
                print("="*70)
                return True

            if creds.expired and creds.refresh_token:
                print("🔄 Attempting to refresh expired token...")
                try:
                    creds.refresh(Request())
                    print("✅ Token refreshed successfully!")

                    # Save refreshed token
                    with open(token_file, 'w') as f:
                        f.write(creds.to_json())
                    print(f"💾 Token saved to: {token_file}")

                    print("\n" + "="*70)
                    print("✅ Gmail OAuth token is ready!")
                    print("="*70)
                    return True
                except Exception as e:
                    print(f"⚠️  Failed to refresh token: {e}")
                    print("Will generate new token...\n")
                    creds = None
        except Exception as e:
            print(f"⚠️  Token file exists but couldn't be loaded: {e}")
            print("Will generate new token...\n")

    # Need to generate new token
    print("\n" + "="*70)
    print("🌐 MANUAL BROWSER AUTHENTICATION REQUIRED")
    print("="*70)
    print("\nFollow these steps:\n")
    print("1. Copy the FULL URL that will appear below")
    print("2. Open it in your Windows browser (Chrome/Edge/Firefox)")
    print("3. Sign in to your Google account")
    print("4. Click 'Allow' to grant permissions")
    print("5. Browser will redirect to localhost")
    print("6. Come back to this terminal - token will be saved automatically")
    print("\n" + "="*70)

    input("\nPress ENTER when ready to start...")

    try:
        # Create the flow
        flow = InstalledAppFlow.from_client_secrets_file(
            str(creds_file), SCOPES
        )

        # Start local server
        flow.run_local_server(
            port=8080,
            authorization_prompt_message='',
            success_message='Authentication successful! You can close this window.',
            open_browser=True  # This will try to open browser and also print URL
        )

        creds = flow.credentials

        print("\n✅ Authentication successful!")

        # Save the credentials
        token_file.parent.mkdir(parents=True, exist_ok=True)
        with open(token_file, 'w') as f:
            f.write(creds.to_json())
        print(f"💾 Token saved to: {token_file}")

        # Verify token was saved
        if token_file.exists():
            print(f"✅ Verified: Token file exists at {token_file}")

            # Check file size
            file_size = token_file.stat().st_size
            print(f"✅ Token file size: {file_size} bytes")

            if file_size > 100:
                print("✅ Token file looks good!")
            else:
                print("⚠️  Warning: Token file seems too small")

        print("\n" + "="*70)
        print("✅ Gmail OAuth token is ready!")
        print("="*70)
        print("\nYou can now use Gmail actions in your Silver Tier AI Employee.")
        print("\nNext steps:")
        print("1. Test Gmail watcher: python src/watchers/gmail_watcher.py")
        print("2. Test Gmail action: python src/actions/gmail_action.py --test")
        print("3. Continue with STEP 2 in SETUP_GUIDE.md\n")

        return True

    except Exception as e:
        print(f"\n❌ Authentication failed: {e}")
        print("\nTroubleshooting:")
        print("- Make sure you copied the FULL URL")
        print("- Try using a different browser")
        print("- Check if port 8080 is available")
        print("- Make sure you clicked 'Allow' in Google's permission page")
        return False

if __name__ == "__main__":
    try:
        success = generate_token()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelled by user")
        exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

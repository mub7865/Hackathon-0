#!/usr/bin/env python3
"""
Generate Gmail OAuth Token

This script generates the OAuth token needed for Gmail API access.
Run this once to authenticate and save the token.

Usage:
    python scripts/generate_gmail_token.py
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
    """Generate Gmail OAuth token"""

    # Get paths
    base_dir = Path(__file__).parent.parent
    creds_file = base_dir / '.credentials' / 'gmail-credentials.json'
    token_file = base_dir / '.credentials' / 'gmail-token.json'

    print(f"\n🔐 Gmail OAuth Token Generator\n")
    print(f"Credentials file: {creds_file}")
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
            print("✅ Token loaded successfully")
        except Exception as e:
            print(f"⚠️  Token file exists but couldn't be loaded: {e}")
            print("Will generate new token...")

    # If no valid credentials, run OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing expired token...")
            try:
                creds.refresh(Request())
                print("✅ Token refreshed successfully")
            except Exception as e:
                print(f"❌ Failed to refresh token: {e}")
                print("Will generate new token...")
                creds = None

        if not creds:
            print("\n🌐 Starting OAuth flow...")
            print("Your browser will open for authentication.")
            print("Please sign in and grant permissions.\n")

            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(creds_file), SCOPES
                )
                creds = flow.run_local_server(port=0)
                print("\n✅ Authentication successful!")
            except Exception as e:
                print(f"\n❌ Authentication failed: {e}")
                return False

        # Save the credentials
        token_file.parent.mkdir(parents=True, exist_ok=True)
        with open(token_file, 'w') as f:
            f.write(creds.to_json())
        print(f"\n💾 Token saved to: {token_file}")

    print("\n" + "="*60)
    print("✅ Gmail OAuth token is ready!")
    print("="*60)
    print("\nYou can now use Gmail actions in your Silver Tier AI Employee.")
    print("\nNext steps:")
    print("1. Test Gmail sending: python src/actions/gmail_action.py --test")
    print("2. Create a task that requires email sending")
    print("3. Approve it and watch it execute\n")

    return True

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

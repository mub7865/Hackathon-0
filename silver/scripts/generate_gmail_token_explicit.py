#!/usr/bin/env python3
"""
Generate Gmail OAuth Token - Manual URL Print Version

This script explicitly prints the URL before starting the server.

Usage:
    python scripts/generate_gmail_token_explicit.py
"""

import os
import json
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import socket
import webbrowser
from urllib.parse import urlencode

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
    """Generate Gmail OAuth token with explicit URL printing"""

    # Get paths
    base_dir = Path(__file__).parent.parent
    creds_file = base_dir / '.credentials' / 'gmail-credentials.json'
    token_file = base_dir / '.credentials' / 'gmail-token.json'

    print("\n" + "="*70)
    print("🔐 Gmail OAuth Token Generator - Explicit URL Version")
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
    print("INSTRUCTIONS:")
    print("1. I will print a URL below")
    print("2. Copy the ENTIRE URL (it's very long)")
    print("3. Paste it in your Windows browser")
    print("4. Sign in to Google and click 'Allow'")
    print("5. Browser will redirect to localhost")
    print("6. Come back here - I'll detect it automatically")
    print()
    print("="*70)

    input("\nPress ENTER to generate URL...")

    try:
        # Find a free port
        port = find_free_port()
        print(f"\n🔌 Using port: {port}")

        # Load client secrets
        with open(creds_file, 'r') as f:
            client_config = json.load(f)

        client_id = client_config['installed']['client_id']

        # Manually construct the authorization URL
        redirect_uri = f'http://localhost:{port}/'

        # Build the URL parameters
        params = {
            'response_type': 'code',
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'scope': ' '.join(SCOPES),
            'access_type': 'offline',
            'prompt': 'consent'
        }

        auth_url = 'https://accounts.google.com/o/oauth2/auth?' + urlencode(params)

        print("\n" + "="*70)
        print("📋 COPY THIS URL (ENTIRE LINE):")
        print("="*70)
        print()
        print(auth_url)
        print()
        print("="*70)
        print()

        input("Press ENTER after you've opened the URL in browser...")

        print("\n⏳ Starting local server...")
        print(f"⏳ Waiting for callback on http://localhost:{port}")
        print("⏳ Complete the authentication in your browser...")
        print()

        # Create flow with the same redirect URI
        flow = InstalledAppFlow.from_client_secrets_file(
            str(creds_file),
            SCOPES,
            redirect_uri=redirect_uri
        )

        # Start the local server and wait for callback
        # This will NOT open browser, just wait for the redirect
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
                print("\nNext steps:")
                print("1. Test: python src/watchers/gmail_watcher.py")
                print("2. Continue with STEP 2\n")
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
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelled")
        exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        exit(1)

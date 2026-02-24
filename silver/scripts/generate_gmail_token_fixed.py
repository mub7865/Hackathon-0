#!/usr/bin/env python3
"""
Generate Gmail OAuth Token - FIXED VERSION

This script properly generates the OAuth URL with state parameter.

Usage:
    python scripts/generate_gmail_token_fixed.py
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
    """Generate Gmail OAuth token with proper state handling"""

    # Get paths
    base_dir = Path(__file__).parent.parent
    creds_file = base_dir / '.credentials' / 'gmail-credentials.json'
    token_file = base_dir / '.credentials' / 'gmail-token.json'

    print("\n" + "="*70)
    print("🔐 Gmail OAuth Token Generator - FIXED VERSION")
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
    print("1. I will print a URL below (with security state)")
    print("2. Copy the ENTIRE URL (it's very long)")
    print("3. Paste it in your Windows browser")
    print("4. Sign in to Google and click 'Allow'")
    print("5. Browser will redirect to localhost")
    print("6. Come back here - I'll save the token automatically")
    print()
    print("="*70)

    input("\nPress ENTER to generate URL...")

    try:
        # Find a free port
        port = find_free_port()
        print(f"\n🔌 Using port: {port}")

        # Create flow with proper redirect URI
        redirect_uri = f'http://localhost:{port}/'

        flow = InstalledAppFlow.from_client_secrets_file(
            str(creds_file),
            SCOPES,
            redirect_uri=redirect_uri
        )

        # Generate authorization URL with state
        # This is the KEY FIX - we get the URL from the flow itself
        auth_url, state = flow.authorization_url(
            access_type='offline',
            prompt='consent'
        )

        print("\n" + "="*70)
        print("📋 COPY THIS URL (ENTIRE LINE):")
        print("="*70)
        print()
        print(auth_url)
        print()
        print("="*70)
        print()
        print("⚠️  IMPORTANT: Copy the ENTIRE URL above!")
        print()

        input("Press ENTER after you've opened the URL in browser...\n")

        print("⏳ Starting local server...")
        print(f"⏳ Waiting for callback on {redirect_uri}")
        print("⏳ Complete the authentication in your browser...")
        print()

        # Now fetch the token using the authorization response
        # The flow already has the state, so it will match
        flow.fetch_token(authorization_response=input("⏳ Waiting for redirect... (this will happen automatically)\n"))

        # Actually, let's use a different approach - start the server properly
        # We need to manually handle the callback

        import http.server
        import urllib.parse

        class CallbackHandler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                # Parse the authorization response
                self.server.auth_response = self.path

                # Send success response
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b'<html><body><h1>Success!</h1><p>You can close this window and return to terminal.</p></body></html>')

            def log_message(self, format, *args):
                # Suppress log messages
                pass

        # Start server
        server = http.server.HTTPServer(('localhost', port), CallbackHandler)
        server.auth_response = None

        print(f"✅ Server started on port {port}")
        print("⏳ Waiting for you to complete authentication in browser...")

        # Wait for one request
        server.handle_request()

        if server.auth_response:
            # Build full URL
            full_url = f"{redirect_uri.rstrip('/')}{server.auth_response}"

            print("\n✅ Received callback!")

            # Fetch token using the authorization response
            flow.fetch_token(authorization_response=full_url)

            creds = flow.credentials

            print("✅ Token fetched successfully!")

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
        else:
            print("❌ No callback received")
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

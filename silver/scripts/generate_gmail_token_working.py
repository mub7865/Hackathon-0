#!/usr/bin/env python3
"""
Generate Gmail OAuth Token - WORKING VERSION

This properly handles localhost HTTP for OAuth development.

Usage:
    python scripts/generate_gmail_token_working.py
"""

import os
import json
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import socket
import http.server

# CRITICAL: Allow HTTP for localhost OAuth (development only)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Gmail API scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.compose'
]

def find_free_port():
    """Find a free port"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port

def generate_token():
    """Generate Gmail OAuth token"""

    base_dir = Path(__file__).parent.parent
    creds_file = base_dir / '.credentials' / 'gmail-credentials.json'
    token_file = base_dir / '.credentials' / 'gmail-token.json'

    print("\n" + "="*70)
    print("🔐 Gmail OAuth Token Generator - WORKING VERSION")
    print("="*70)
    print(f"\nCredentials: {creds_file}")
    print(f"Token: {token_file}\n")

    if not creds_file.exists():
        print(f"❌ Credentials file not found")
        return False

    # Check existing token
    if token_file.exists():
        print("📄 Checking existing token...")
        try:
            creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)
            if creds.valid:
                print("✅ Token is already valid!")
                return True
            if creds.expired and creds.refresh_token:
                print("🔄 Refreshing...")
                try:
                    creds.refresh(Request())
                    with open(token_file, 'w') as f:
                        f.write(creds.to_json())
                    print("✅ Refreshed successfully!")
                    return True
                except:
                    print("⚠️  Refresh failed, generating new token...\n")
        except:
            print("⚠️  Token invalid, generating new...\n")

    print("="*70)
    print("🌐 GENERATING NEW TOKEN")
    print("="*70)
    print("\nINSTRUCTIONS:")
    print("1. Copy the URL that will appear below")
    print("2. Open it in your Windows browser")
    print("3. Sign in and click 'Allow'")
    print("4. Browser will redirect to localhost")
    print("5. Wait here - token will save automatically")
    print("\n" + "="*70)

    input("\nPress ENTER to start...")

    try:
        port = find_free_port()
        print(f"\n🔌 Port: {port}")

        # Create flow
        flow = InstalledAppFlow.from_client_secrets_file(
            str(creds_file),
            SCOPES,
            redirect_uri=f'http://localhost:{port}/'
        )

        # Generate auth URL (this includes state)
        auth_url, state = flow.authorization_url(
            access_type='offline',
            prompt='consent'
        )

        print("\n" + "="*70)
        print("📋 COPY THIS URL:")
        print("="*70)
        print()
        print(auth_url)
        print()
        print("="*70)
        print("\n⚠️  Copy the ENTIRE URL above!\n")

        # Custom HTTP server to handle callback
        class OAuthCallbackHandler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                # Store the full request path
                self.server.callback_url = f"http://localhost:{port}{self.path}"

                # Send success response
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                html = '''
                <html>
                <head><title>Success</title></head>
                <body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h1 style="color: green;">✅ Success!</h1>
                    <p>Authentication successful!</p>
                    <p>You can close this window and return to the terminal.</p>
                </body>
                </html>
                '''
                self.wfile.write(html.encode())

            def log_message(self, format, *args):
                pass  # Suppress logs

        # Start server
        server = http.server.HTTPServer(('localhost', port), OAuthCallbackHandler)
        server.callback_url = None

        print("⏳ Server started, waiting for authentication...")
        print("⏳ Complete the authentication in your browser...\n")

        # Handle one request
        server.handle_request()

        if server.callback_url:
            print("\n✅ Callback received!")

            # Fetch token using the callback URL
            flow.fetch_token(authorization_response=server.callback_url)

            creds = flow.credentials

            print("✅ Token fetched!")

            # Save token
            token_file.parent.mkdir(parents=True, exist_ok=True)
            with open(token_file, 'w') as f:
                f.write(creds.to_json())

            print(f"💾 Saved to: {token_file}")

            # Verify
            if token_file.exists():
                size = token_file.stat().st_size
                print(f"✅ Verified: {size} bytes")

                if size > 100:
                    print("\n" + "="*70)
                    print("✅ SUCCESS! Gmail token is ready!")
                    print("="*70)
                    print("\n✅ STEP 1 COMPLETE!")
                    print("\nNext: Continue with STEP 2 (LinkedIn credentials)\n")
                    return True
                else:
                    print("⚠️  Token file too small")
                    return False
            else:
                print("❌ Token not saved")
                return False
        else:
            print("❌ No callback received")
            return False

    except Exception as e:
        print(f"\n❌ Error: {e}")
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

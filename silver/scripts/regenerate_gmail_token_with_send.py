#!/usr/bin/env python3
"""
Regenerate Gmail OAuth Token with SEND permissions

This generates a token with gmail.send scope and saves as pickle format.

Usage:
    python scripts/regenerate_gmail_token_with_send.py
"""

import os
import pickle
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import socket
import http.server

# CRITICAL: Allow HTTP for localhost OAuth (development only)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Gmail API scopes - INCLUDING SEND
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
    """Generate Gmail OAuth token with SEND permissions"""

    base_dir = Path(__file__).parent.parent
    creds_file = base_dir / '.credentials' / 'gmail-credentials.json'
    token_file = base_dir / '.credentials' / 'gmail-token.pickle'

    print("\n" + "="*70)
    print("Gmail OAuth Token Generator - WITH SEND PERMISSIONS")
    print("="*70)
    print(f"\nCredentials: {creds_file}")
    print(f"Token: {token_file}")
    print(f"\nScopes: {', '.join(SCOPES)}\n")

    if not creds_file.exists():
        print(f"[ERROR] Credentials file not found at {creds_file}")
        return False

    # Delete old token to force regeneration
    if token_file.exists():
        print("Removing old token to regenerate with new scopes...")
        token_file.unlink()

    print("="*70)
    print("GENERATING NEW TOKEN WITH SEND PERMISSIONS")
    print("="*70)
    print("\nINSTRUCTIONS:")
    print("1. Copy the URL that will appear below")
    print("2. Open it in your browser")
    print("3. Sign in to your Gmail account")
    print("4. Click 'Allow' to grant permissions")
    print("5. Browser will redirect to localhost")
    print("6. Wait here - token will save automatically")
    print("\n" + "="*70)

    input("\nPress ENTER to start...")

    try:
        port = find_free_port()
        print(f"\nUsing port: {port}")

        # Create flow
        flow = InstalledAppFlow.from_client_secrets_file(
            str(creds_file),
            SCOPES,
            redirect_uri=f'http://localhost:{port}/'
        )

        # Generate auth URL
        auth_url, state = flow.authorization_url(
            access_type='offline',
            prompt='consent'
        )

        print("\n" + "="*70)
        print("COPY THIS URL AND OPEN IN BROWSER:")
        print("="*70)
        print()
        print(auth_url)
        print()
        print("="*70)
        print("\n[!] Copy the ENTIRE URL above and paste in your browser!\n")

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
                    <h1 style="color: green;">Success!</h1>
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

        print("Server started, waiting for authentication...")
        print("Complete the authentication in your browser...\n")

        # Handle one request
        server.handle_request()

        if server.callback_url:
            print("\n[OK] Callback received!")

            # Fetch token using the callback URL
            flow.fetch_token(authorization_response=server.callback_url)

            creds = flow.credentials

            print("[OK] Token fetched!")

            # Save token as PICKLE
            token_file.parent.mkdir(parents=True, exist_ok=True)
            with open(token_file, 'wb') as f:
                pickle.dump(creds, f)

            print(f"[OK] Saved to: {token_file}")

            # Verify
            if token_file.exists():
                size = token_file.stat().st_size
                print(f"[OK] Verified: {size} bytes")

                # Check scopes
                with open(token_file, 'rb') as f:
                    saved_creds = pickle.load(f)
                print(f"[OK] Scopes: {saved_creds.scopes}")

                if size > 100:
                    print("\n" + "="*70)
                    print("[SUCCESS] Gmail token with SEND permissions is ready!")
                    print("="*70)
                    print("\n[OK] You can now send emails via Gmail API!\n")
                    return True
                else:
                    print("[WARN] Token file too small")
                    return False
            else:
                print("[ERROR] Token not saved")
                return False
        else:
            print("[ERROR] No callback received")
            return False

    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = generate_token()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n[WARN] Cancelled")
        exit(1)

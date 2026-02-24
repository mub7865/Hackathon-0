#!/usr/bin/env python3
"""
Auto Gmail Token Regeneration - Non-Interactive

Automatically generates Gmail token with SEND permissions.
Just run and open the URL in browser.
"""

import os
import pickle
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import socket
import http.server
import webbrowser

# Allow HTTP for localhost OAuth
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
    print("Gmail Token Generator - AUTO MODE")
    print("="*70)
    print(f"\nCredentials: {creds_file}")
    print(f"Token: {token_file}")
    print(f"\nScopes:")
    for scope in SCOPES:
        print(f"  - {scope}")

    if not creds_file.exists():
        print(f"\n[ERROR] Credentials file not found at {creds_file}")
        return False

    # Delete old token to force regeneration
    if token_file.exists():
        print("\n[INFO] Removing old token to regenerate with new scopes...")
        token_file.unlink()

    print("\n" + "="*70)
    print("STARTING TOKEN GENERATION")
    print("="*70)

    try:
        port = find_free_port()
        print(f"\n[INFO] Using port: {port}")

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
        print("OPEN THIS URL IN YOUR BROWSER:")
        print("="*70)
        print()
        print(auth_url)
        print()
        print("="*70)
        print("\n[INFO] Attempting to open browser automatically...")
        print("[INFO] If browser doesn't open, copy the URL above manually")

        # Try to open browser automatically
        try:
            webbrowser.open(auth_url)
            print("[OK] Browser opened")
        except:
            print("[WARN] Could not open browser automatically")
            print("[ACTION] Please copy and paste the URL above into your browser")

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

        print("\n[INFO] Waiting for authentication...")
        print("[INFO] Complete the authentication in your browser...")
        print("[INFO] This may take a few moments...\n")

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
                    print("\n[NEXT STEP] Restart orchestrator:")
                    print("  pm2 restart silver-orchestrator")
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
        print("\n\n[WARN] Cancelled by user")
        exit(1)

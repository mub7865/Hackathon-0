#!/usr/bin/env python3
"""
Gmail Action Script - REAL Implementation

This script sends emails using the Gmail API.

Usage:
    python src/actions/gmail_action.py --test
"""

import os
import sys
import json
import logging
import base64
from datetime import datetime
from pathlib import Path
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def send_email(to: str, subject: str, body: str, cc: list = None, bcc: list = None) -> dict:
    """
    Send email using Gmail API - REAL IMPLEMENTATION

    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body (plain text or HTML)
        cc: List of CC recipients (optional)
        bcc: List of BCC recipients (optional)

    Returns:
        dict: Result with status and message_id

    Example:
        result = send_email(
            to="client@example.com",
            subject="Invoice #12345",
            body="Please find attached invoice...",
            cc=["manager@example.com"]
        )
    """

    logger.info("=" * 60)
    logger.info("GMAIL ACTION - REAL MODE")
    logger.info("=" * 60)
    logger.info(f"To: {to}")
    logger.info(f"Subject: {subject}")
    logger.info(f"Body: {body[:100]}..." if len(body) > 100 else f"Body: {body}")
    if cc:
        logger.info(f"CC: {', '.join(cc)}")
    if bcc:
        logger.info(f"BCC: {', '.join(bcc)}")
    logger.info("=" * 60)

    try:
        # Get token path - use .credentials folder (same as watcher)
        base_dir = Path(__file__).parent.parent.parent
        token_path = os.getenv('GMAIL_TOKEN_PATH', str(base_dir / '.credentials' / 'gmail-token.pickle'))

        if not os.path.exists(token_path):
            raise FileNotFoundError(f"Gmail token not found at {token_path}. Run OAuth flow first.")

        # Validate recipient
        if not to or to == "None":
            logger.error(f"Invalid recipient: {to}")
            return {"status": "error", "error": f"Invalid recipient: {to}"}

        # Load credentials from pickle file
        import pickle
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)

        # Refresh token if expired
        if creds.expired and creds.refresh_token:
            logger.info("Token expired, refreshing...")
            from google.auth.transport.requests import Request
            creds.refresh(Request())
            # Save refreshed token
            with open(token_path, 'wb') as token:
                pickle.dump(creds, token)
            logger.info("Token refreshed successfully")

        service = build('gmail', 'v1', credentials=creds)

        # Create message
        message = MIMEText(body)
        message['to'] = to
        message['subject'] = subject
        if cc:
            message['cc'] = ', '.join(cc)
        if bcc:
            message['bcc'] = ', '.join(bcc)

        # Encode message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        # Send
        result = service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()

        logger.info(f"✅ Email sent successfully: {result['id']}")
        logger.info("=" * 60)

        # Log to file
        log_dir = base_dir / "vault" / "Logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / f"gmail-actions-{datetime.now().strftime('%Y-%m-%d')}.log"
        with open(log_file, 'a') as f:
            f.write(f"\n{'=' * 60}\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write(f"To: {to}\n")
            f.write(f"Subject: {subject}\n")
            f.write(f"Body: {body}\n")
            if cc:
                f.write(f"CC: {', '.join(cc)}\n")
            if bcc:
                f.write(f"BCC: {', '.join(bcc)}\n")
            f.write(f"Status: SUCCESS\n")
            f.write(f"Message ID: {result['id']}\n")
            f.write(f"{'=' * 60}\n")

        return {
            "status": "success",
            "message_id": result['id'],
            "mode": "real",
            "logged_to": str(log_file)
        }

    except Exception as e:
        logger.error(f"❌ Failed to send email: {e}")
        logger.error("=" * 60)

        # Log error to file
        log_dir = Path(__file__).parent.parent.parent / "vault" / "Logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / f"gmail-actions-{datetime.now().strftime('%Y-%m-%d')}.log"
        with open(log_file, 'a') as f:
            f.write(f"\n{'=' * 60}\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write(f"To: {to}\n")
            f.write(f"Subject: {subject}\n")
            f.write(f"Status: FAILED\n")
            f.write(f"Error: {str(e)}\n")
            f.write(f"{'=' * 60}\n")

        return {
            "status": "error",
            "error": str(e),
            "mode": "real",
            "logged_to": str(log_file)
        }


def main():
    """Test the Gmail action script"""
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print("\n🧪 Testing Gmail Action Script (REAL MODE)\n")
        print("⚠️  This will send a REAL email!\n")

        # Get recipient email
        if len(sys.argv) > 2:
            recipient = sys.argv[2]
        else:
            recipient = input("Enter recipient email address: ").strip()

        if not recipient:
            print("❌ No recipient provided")
            return

        print(f"\n📧 Sending test email to: {recipient}\n")

        result = send_email(
            to=recipient,
            subject="Test Email from Silver Tier AI Employee",
            body="This is a test email to verify the Gmail action script is working.\n\nSent from Silver Tier AI Employee automation system."
        )

        print(f"\n✅ Result: {json.dumps(result, indent=2)}\n")
    else:
        print("Usage: python gmail_action.py --test [recipient_email]")
        print("Example: python gmail_action.py --test user@example.com")


if __name__ == "__main__":
    main()

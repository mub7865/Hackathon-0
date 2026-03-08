"""
Gmail Watcher - Monitors Gmail inbox for new unread emails
Uses Gmail API with OAuth2 authentication
"""

from pathlib import Path
from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass
import logging
import os

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle

from src.watchers.base_watcher import BaseWatcher, TaskCreationError
from src.utils.duplicate_tracker import DuplicateTracker
from src.utils.logger import setup_logger


# Gmail API scopes - include both readonly and send
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send'
]


@dataclass
class GmailMessage:
    """Gmail message metadata"""
    message_id: str
    thread_id: str
    from_email: str
    to_email: str
    subject: str
    snippet: str
    body: str
    received: datetime
    labels: List[str]


class GmailWatcher(BaseWatcher):
    """
    Monitors Gmail inbox for new unread emails.
    Uses Gmail API with OAuth2 authentication.
    """

    def __init__(self, vault_path: str, credentials_path: str):
        """
        Initialize Gmail watcher.

        Args:
            vault_path: Path to Obsidian vault
            credentials_path: Path to Gmail OAuth credentials
        """
        super().__init__(vault_path, check_interval=120)  # 2 minutes

        self.credentials_path = credentials_path
        # Use .credentials folder for token (same as credentials)
        self.token_path = Path('.credentials/gmail-token.pickle')
        self.service = None

        # Duplicate tracking
        tracker_path = Path('sessions/processed_ids/gmail_processed_ids.json')
        self.duplicate_tracker = DuplicateTracker(tracker_path)
        self.duplicate_tracker.load_processed_ids()

        # Setup logger
        self.logger = setup_logger('gmail-watcher', f'{vault_path}/Logs')

        # Initialize Gmail API
        self._init_gmail_service()

    def _init_gmail_service(self):
        """Initialize Gmail API service with OAuth2."""
        creds = None

        # Load token if exists
        if self.token_path.exists():
            with open(self.token_path, 'rb') as token:
                creds = pickle.load(token)

        # If no valid credentials, authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                self.logger.info("Refreshing Gmail token")
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    self.logger.error(f"Gmail credentials not found at {self.credentials_path}")
                    self.logger.error("Please download credentials from Google Cloud Console")
                    raise FileNotFoundError(f"Gmail credentials not found: {self.credentials_path}")

                self.logger.info("Starting Gmail OAuth flow")
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)

            # Save token
            self.token_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.token_path, 'wb') as token:
                pickle.dump(creds, token)

        self.service = build('gmail', 'v1', credentials=creds)
        self.logger.info("Gmail API service initialized")

    def check_for_updates(self) -> List[GmailMessage]:
        """
        Check Gmail for new unread important emails.

        Returns:
            List of GmailMessage objects

        Query: 'is:unread is:important'
        """
        if not self.service:
            self.logger.error("Gmail service not initialized")
            return []

        try:
            # Query for unread important emails
            results = self.service.users().messages().list(
                userId='me',
                q='is:unread is:important',
                maxResults=10
            ).execute()

            messages = results.get('messages', [])

            if not messages:
                return []

            # Fetch full message details
            gmail_messages = []
            for msg in messages:
                message_id = msg['id']

                # Skip if already processed
                if self.duplicate_tracker.is_duplicate(message_id):
                    continue

                # Get full message
                full_msg = self.service.users().messages().get(
                    userId='me',
                    id=message_id,
                    format='full'
                ).execute()

                gmail_msg = self._parse_message(full_msg)
                if gmail_msg:
                    gmail_messages.append(gmail_msg)

            return gmail_messages

        except Exception as e:
            self.logger.error(f"Error checking Gmail: {e}")
            return []

    def _parse_message(self, message: dict) -> Optional[GmailMessage]:
        """
        Parse Gmail API message into GmailMessage object.

        Args:
            message: Gmail API message dict

        Returns:
            GmailMessage object or None if parsing fails
        """
        try:
            headers = {h['name']: h['value'] for h in message['payload']['headers']}

            # Extract body
            body = ""
            if 'parts' in message['payload']:
                for part in message['payload']['parts']:
                    if part['mimeType'] == 'text/plain':
                        import base64
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                        break
            elif 'body' in message['payload'] and 'data' in message['payload']['body']:
                import base64
                body = base64.urlsafe_b64decode(message['payload']['body']['data']).decode('utf-8')

            return GmailMessage(
                message_id=message['id'],
                thread_id=message['threadId'],
                from_email=headers.get('From', 'unknown'),
                to_email=headers.get('To', 'unknown'),
                subject=headers.get('Subject', 'No Subject'),
                snippet=message.get('snippet', ''),
                body=body,
                received=datetime.fromtimestamp(int(message['internalDate']) / 1000),
                labels=message.get('labelIds', [])
            )
        except Exception as e:
            self.logger.error(f"Error parsing message: {e}")
            return None

    def create_action_file(self, message: GmailMessage) -> Path:
        """
        Create task file from Gmail message.

        File naming: EMAIL_{message_id}_{timestamp}.md

        Args:
            message: GmailMessage object

        Returns:
            Path to created task file
        """
        try:
            # Generate filename
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            filename = f"EMAIL_{message.message_id[:8]}_{timestamp}.md"
            file_path = self.needs_action / filename

            # Create task content
            content = f"""---
id: email_{message.message_id}_{timestamp}
source: gmail
type: email
status: pending
priority: high
created: {datetime.now().isoformat()}
processed: null
flags: []
amount: null
requires_approval: false
approved: null
email_from: {message.from_email}
email_subject: {message.subject}
email_message_id: {message.message_id}
---

## Email Content

**From**: {message.from_email}
**Subject**: {message.subject}
**Received**: {message.received.strftime('%Y-%m-%d %H:%M:%S')}

{message.body}

## Suggested Actions

- [ ] Reply to sender
- [ ] Forward to relevant party
- [ ] Archive after processing
"""

            # Write file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            # Mark as processed
            self.duplicate_tracker.mark_processed(message.message_id)

            self.logger.info(f"Created task file: {filename}")
            return file_path

        except Exception as e:
            self.logger.error(f"Error creating task file: {e}")
            raise TaskCreationError(f"Failed to create task file: {e}")


if __name__ == '__main__':
    """Run Gmail watcher standalone"""
    import sys
    from dotenv import load_dotenv

    load_dotenv()

    vault_path = os.getenv('VAULT_PATH', './vault')
    credentials_path = os.getenv('GMAIL_CREDENTIALS', './config/gmail_credentials.json')

    watcher = GmailWatcher(vault_path, credentials_path)

    try:
        watcher.run()
    except KeyboardInterrupt:
        print("\nGmail watcher stopped")
        sys.exit(0)

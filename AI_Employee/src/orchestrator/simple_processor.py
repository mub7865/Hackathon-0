#!/usr/bin/env python3
"""
Simple Task Processor - Direct Processing without Claude Code
Handles email replies, WhatsApp replies, and LinkedIn posts directly
"""

import sys
from pathlib import Path
from datetime import datetime
import logging
import yaml
import re

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from actions.gmail_action import send_email
from actions.whatsapp_action import send_whatsapp
from actions.linkedin_action import post_to_linkedin

logger = logging.getLogger(__name__)


def parse_task_file(task_file: Path):
    """Parse task file with YAML frontmatter"""
    with open(task_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract YAML frontmatter
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)$', content, re.DOTALL)
    if not match:
        raise ValueError("Invalid task file format - no YAML frontmatter found")

    yaml_content = match.group(1)
    body_content = match.group(2)

    # Parse YAML
    metadata = yaml.safe_load(yaml_content)

    # Create simple object
    class Task:
        def __init__(self, metadata, content):
            self.id = metadata.get('id')
            self.source = metadata.get('source')
            self.type = metadata.get('type')
            self.status = metadata.get('status')
            self.priority = metadata.get('priority', 'medium')  # Default to medium if not specified
            self.classification = metadata.get('classification', 'ROUTINE')
            self.email_from = metadata.get('email_from')
            self.email_subject = metadata.get('email_subject')
            self.whatsapp_sender = metadata.get('whatsapp_sender')
            self.whatsapp_from = metadata.get('whatsapp_from')  # Alternative field name
            self.content = content

    return Task(metadata, body_content)


def process_email_task(task, task_file: Path) -> bool:
    """
    Process email task - draft reply and send or request approval

    Args:
        task: TaskFile object
        task_file: Path to task file

    Returns:
        True if processed successfully
    """
    try:
        logger.info(f"Processing email task from {task.email_from}")

        # Extract email details
        sender = task.email_from
        subject = task.email_subject

        # Draft a professional reply based on the email content
        # For now, use a simple template
        reply_body = f"""Hi,

Thank you for your email regarding "{subject}".

I've received your message and will review it carefully. I'll get back to you with a detailed response within 24 hours.

If this is urgent, please feel free to call me directly.

Best regards,
Muhammad Ubaid
"""

        # Add draft to task file
        with open(task_file, 'a') as f:
            f.write(f"\n\n---\n\n")
            f.write(f"## Draft Reply (Awaiting Approval)\n\n")
            f.write(f"**To**: {sender}\n")
            f.write(f"**Subject**: Re: {subject}\n")
            f.write(f"**Draft Created**: {datetime.now().isoformat()}\n\n")
            f.write(reply_body)
            f.write(f"\n\n---\n\n")
            f.write(f"**Status**: Pending approval (requires review before sending)\n")

        logger.info(f"Draft reply added to {task_file.name}")
        return True

    except Exception as e:
        logger.error(f"Error processing email task: {e}")
        return False


def process_whatsapp_task(task, task_file: Path) -> bool:
    """
    Process WhatsApp task - draft reply and send or request approval

    Args:
        task: TaskFile object
        task_file: Path to task file

    Returns:
        True if processed successfully
    """
    try:
        logger.info(f"Processing WhatsApp task from {task.whatsapp_sender}")

        # Draft a simple reply
        reply_message = "Thanks for your message! I've received it and will respond shortly."

        # Add draft to task file
        with open(task_file, 'a') as f:
            f.write(f"\n\n---\n\n")
            f.write(f"## Draft Reply (Awaiting Approval)\n\n")
            f.write(f"**To**: {task.whatsapp_sender}\n")
            f.write(f"**Draft Created**: {datetime.now().isoformat()}\n\n")
            f.write(reply_message)
            f.write(f"\n\n---\n\n")
            f.write(f"**Status**: Pending approval (requires review before sending)\n")

        logger.info(f"Draft reply added to {task_file.name}")
        return True

    except Exception as e:
        logger.error(f"Error processing WhatsApp task: {e}")
        return False


def process_linkedin_task(task, task_file: Path) -> bool:
    """
    Process LinkedIn task - draft post and request approval

    Args:
        task: TaskFile object
        task_file: Path to task file

    Returns:
        True if processed successfully
    """
    try:
        logger.info(f"Processing LinkedIn task")

        # LinkedIn posts always require approval
        with open(task_file, 'a') as f:
            f.write(f"\n\n---\n\n")
            f.write(f"## Approval Required\n\n")
            f.write(f"**Risk Level**: Medium\n")
            f.write(f"**Reason**: LinkedIn posts are public and require review\n")
            f.write(f"**Draft Created**: {datetime.now().isoformat()}\n\n")
            f.write(f"[ ] Approve\n")
            f.write(f"[ ] Reject\n")
            f.write(f"[ ] Modify\n")

        logger.info(f"Approval request added to {task_file.name}")
        return True

    except Exception as e:
        logger.error(f"Error processing LinkedIn task: {e}")
        return False


def process_task(task_file: Path, vault_path: Path) -> bool:
    """
    Process a single task file

    Args:
        task_file: Path to task file
        vault_path: Path to vault directory

    Returns:
        True if processed successfully
    """
    try:
        # Read task file
        task = parse_task_file(task_file)

        # Route based on task type/source
        if task.type == 'email' or task.source == 'gmail':
            success = process_email_task(task, task_file)
        elif task.type == 'whatsapp' or task.source == 'whatsapp':
            success = process_whatsapp_task(task, task_file)
        elif task.type == 'linkedin' or task.source == 'linkedin':
            success = process_linkedin_task(task, task_file)
        else:
            logger.warning(f"Unknown task type: {task.type}, skipping")
            return False

        if success:
            # Move to Pending_Approval
            pending_approval = vault_path / 'Pending_Approval'
            pending_approval.mkdir(exist_ok=True)

            dest = pending_approval / task_file.name
            task_file.rename(dest)

            logger.info(f"Moved {task_file.name} to Pending_Approval")
            return True

        return False

    except Exception as e:
        logger.error(f"Error processing task {task_file.name}: {e}")
        return False


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Test processing
    vault_path = Path(__file__).parent.parent.parent / 'vault'
    needs_action = vault_path / 'Needs_Action'

    if not needs_action.exists():
        print(f"[ERROR] Needs_Action folder not found: {needs_action}")
        sys.exit(1)

    task_files = list(needs_action.glob('*.md'))

    if len(task_files) == 0:
        print("[INFO] No tasks to process")
        sys.exit(0)

    print(f"[INFO] Found {len(task_files)} task(s) to process")

    for task_file in task_files:
        print(f"\n[PROCESSING] {task_file.name}")
        success = process_task(task_file, vault_path)
        if success:
            print(f"[SUCCESS] Processed successfully")
        else:
            print(f"[FAILED] Failed to process")

#!/usr/bin/env python3
"""
Execute Approved Tasks - Sends real emails, WhatsApp, LinkedIn posts
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


def execute_email_task(task_file: Path, vault_path: Path) -> bool:
    """Execute approved email task - send real email"""
    try:
        with open(task_file, 'r') as f:
            content = f.read()

        # Extract email details from draft section
        to_match = re.search(r'\*\*To\*\*:\s*([^\n]+)', content)
        subject_match = re.search(r'\*\*Subject\*\*:\s*([^\n]+)', content)
        body_match = re.search(r'Draft Created.*?\n\n(.*?)\n\n---', content, re.DOTALL)

        if not (to_match and subject_match and body_match):
            logger.error(f"Could not extract email details from {task_file.name}")
            return False

        to_email = to_match.group(1).strip()
        subject = subject_match.group(1).strip()
        body = body_match.group(1).strip()

        logger.info(f"Sending email to {to_email}")
        result = send_email(to=to_email, subject=subject, body=body)

        if result['status'] == 'success':
            logger.info(f"Email sent successfully: {result['message_id']}")

            # Move to Done
            done_dir = vault_path / 'Done'
            done_file = done_dir / task_file.name
            task_file.rename(done_file)

            return True
        else:
            logger.error(f"Email failed: {result.get('error')}")
            return False

    except Exception as e:
        logger.error(f"Error executing email task: {e}")
        return False


def execute_whatsapp_task(task_file: Path, vault_path: Path) -> bool:
    """Execute approved WhatsApp task - send message"""
    try:
        with open(task_file, 'r') as f:
            content = f.read()

        # Extract WhatsApp details from draft section
        to_match = re.search(r'\*\*To\*\*:\s*([^\n]+)', content)
        body_match = re.search(r'Draft Created.*?\n\n(.*?)\n\n---', content, re.DOTALL)

        if not (to_match and body_match):
            logger.error(f"Could not extract WhatsApp details from {task_file.name}")
            return False

        to_number = to_match.group(1).strip()
        message = body_match.group(1).strip()

        logger.info(f"Sending WhatsApp to {to_number}")
        result = send_whatsapp(to=to_number, message=message)

        if result['status'] == 'success':
            logger.info(f"WhatsApp sent successfully (placeholder mode)")

            # Move to Done
            done_dir = vault_path / 'Done'
            done_file = done_dir / task_file.name
            task_file.rename(done_file)

            return True
        else:
            logger.error(f"WhatsApp failed: {result.get('error')}")
            return False

    except Exception as e:
        logger.error(f"Error executing WhatsApp task: {e}")
        return False


def execute_linkedin_task(task_file: Path, vault_path: Path) -> bool:
    """Execute approved LinkedIn task - post to LinkedIn"""
    try:
        with open(task_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract LinkedIn post content - try multiple patterns
        # Pattern 1: From skill (### Post Content:)
        content_match = re.search(r'### Post Content:\s*\n\n(.*?)(?:\n###|\n---|\Z)', content, re.DOTALL)
        
        # Pattern 2: Fallback (## Draft Post)
        if not content_match:
            content_match = re.search(r'## Draft Post.*?\n\n(.*?)\n\n---', content, re.DOTALL)

        if not content_match:
            logger.error(f"Could not extract LinkedIn content from {task_file.name}")
            return False

        post_content = content_match.group(1).strip()
        
        # Remove any hashtag section if it's already included in post_content or separate
        # (LinkedIn skill usually puts them under a separate header)
        if "### Hashtags:" in content:
            hashtags_match = re.search(r'### Hashtags:\s*\n([^\n]+)', content)
            if hashtags_match:
                post_content += "\n\n" + hashtags_match.group(1).strip()

        logger.info(f"Posting to LinkedIn: {post_content[:50]}...")
        result = post_to_linkedin(content=post_content)

        if result['status'] == 'success':
            logger.info(f"LinkedIn post created: {result.get('post_id')}")

            # Move to Done
            done_dir = vault_path / 'Done'
            done_file = done_dir / task_file.name
            task_file.rename(done_file)

            return True
        else:
            logger.error(f"LinkedIn failed: {result.get('error')}")
            return False

    except Exception as e:
        logger.error(f"Error executing LinkedIn task: {e}")
        return False


def execute_approved_tasks(vault_path: Path) -> int:
    """Execute all approved tasks"""
    approved_dir = vault_path / 'Approved'

    if not approved_dir.exists():
        return 0

    task_files = list(approved_dir.glob('*.md'))

    if len(task_files) == 0:
        return 0

    logger.info(f"Found {len(task_files)} approved task(s) to execute")

    executed_count = 0

    for task_file in task_files:
        try:
            logger.info(f"Executing: {task_file.name}")

            # Read task metadata to determine type
            with open(task_file, 'r') as f:
                content = f.read()

            # Extract YAML frontmatter
            match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
            if not match:
                logger.warning(f"No YAML frontmatter in {task_file.name}, skipping")
                continue

            metadata = yaml.safe_load(match.group(1))
            task_type = metadata.get('type')
            task_source = metadata.get('source')

            # Route based on type/source
            if task_type == 'email' or task_source == 'gmail':
                success = execute_email_task(task_file, vault_path)
            elif task_type == 'whatsapp' or task_source == 'whatsapp':
                success = execute_whatsapp_task(task_file, vault_path)
            elif task_type == 'linkedin' or task_source == 'linkedin':
                success = execute_linkedin_task(task_file, vault_path)
            else:
                logger.warning(f"Unknown task type: {task_type}, skipping")
                continue

            if success:
                executed_count += 1
                logger.info(f"Successfully executed {task_file.name}")

        except Exception as e:
            logger.error(f"Error processing {task_file.name}: {e}")
            continue

    return executed_count


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Execute approved tasks
    vault_path = Path(__file__).parent.parent.parent / 'vault'

    if not vault_path.exists():
        print(f"[ERROR] Vault not found: {vault_path}")
        sys.exit(1)

    executed = execute_approved_tasks(vault_path)

    if executed > 0:
        print(f"[SUCCESS] Executed {executed} approved task(s)")
    else:
        print("[INFO] No approved tasks to execute")

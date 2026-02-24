"""
Action Scripts for Silver Tier AI Employee

This package contains action executors for external integrations.
Currently in PLACEHOLDER mode - logs actions instead of executing them.

Available Actions:
- gmail_action.py: Send emails via Gmail API
- whatsapp_action.py: Send WhatsApp messages via Twilio API
- linkedin_action.py: Post to LinkedIn via Playwright browser automation

Usage:
    from src.actions.gmail_action import send_email
    from src.actions.whatsapp_action import send_whatsapp
    from src.actions.linkedin_action import post_to_linkedin

    # All functions currently log instead of executing
    result = send_email(to="user@example.com", subject="Test", body="Hello")
"""

__version__ = "0.1.0"
__all__ = ["gmail_action", "whatsapp_action", "linkedin_action"]

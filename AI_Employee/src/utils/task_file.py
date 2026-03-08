"""
Task File Data Model
Represents markdown task files with YAML frontmatter
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from pathlib import Path


@dataclass
class TaskFile:
    """
    Task file with YAML frontmatter.
    Represents a task to be processed by orchestrator.
    """
    # Required fields
    id: str
    source: str  # "file" | "gmail" | "whatsapp"
    type: str  # "email" | "whatsapp_message" | "file_drop" | "task"
    status: str  # "pending" | "processing" | "done" | "approved" | "rejected"
    priority: str  # "low" | "medium" | "high" | "urgent"
    created: str  # ISO 8601 timestamp

    # Optional fields
    processed: Optional[str] = None  # ISO 8601 timestamp
    flags: List[str] = field(default_factory=list)
    amount: Optional[float] = None
    requires_approval: bool = False
    approved: Optional[bool] = None
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None

    # Source-specific metadata
    email_from: Optional[str] = None
    email_subject: Optional[str] = None
    email_message_id: Optional[str] = None
    whatsapp_sender: Optional[str] = None
    whatsapp_chat: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None

    # Content
    content: str = ""

    def validate(self) -> List[str]:
        """
        Validate task file data.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Validate source
        if self.source not in ["file", "gmail", "whatsapp"]:
            errors.append(f"Invalid source: {self.source}")

        # Validate status
        valid_statuses = ["pending", "processing", "done", "approved", "rejected"]
        if self.status not in valid_statuses:
            errors.append(f"Invalid status: {self.status}")

        # Validate priority
        valid_priorities = ["low", "medium", "high", "urgent"]
        if self.priority not in valid_priorities:
            errors.append(f"Invalid priority: {self.priority}")

        # Validate approval logic
        if self.approved is not None and self.approved_by != "human":
            errors.append("Only humans can approve tasks")

        return errors

    def to_yaml_dict(self) -> dict:
        """
        Convert to dictionary for YAML frontmatter.

        Returns:
            Dictionary representation
        """
        return {
            'id': self.id,
            'source': self.source,
            'type': self.type,
            'status': self.status,
            'priority': self.priority,
            'created': self.created,
            'processed': self.processed,
            'flags': self.flags,
            'amount': self.amount,
            'requires_approval': self.requires_approval,
            'approved': self.approved,
            'approved_by': self.approved_by,
            'approved_at': self.approved_at,
            'email_from': self.email_from,
            'email_subject': self.email_subject,
            'email_message_id': self.email_message_id,
            'whatsapp_sender': self.whatsapp_sender,
            'whatsapp_chat': self.whatsapp_chat,
            'file_name': self.file_name,
            'file_size': self.file_size,
        }

    @staticmethod
    def from_yaml_dict(data: dict, content: str = "") -> 'TaskFile':
        """
        Create TaskFile from YAML frontmatter dictionary.

        Args:
            data: YAML frontmatter as dict
            content: Markdown content

        Returns:
            TaskFile instance
        """
        return TaskFile(
            id=data['id'],
            source=data['source'],
            type=data['type'],
            status=data['status'],
            priority=data.get('priority', 'medium'),  # Default to medium if not specified
            created=data.get('created', datetime.now().isoformat()),  # Default to now if not specified
            processed=data.get('processed'),
            flags=data.get('flags', []),
            amount=data.get('amount'),
            requires_approval=data.get('requires_approval', False),
            approved=data.get('approved'),
            approved_by=data.get('approved_by'),
            approved_at=data.get('approved_at'),
            email_from=data.get('email_from'),
            email_subject=data.get('email_subject'),
            email_message_id=data.get('email_message_id'),
            whatsapp_sender=data.get('whatsapp_sender'),
            whatsapp_chat=data.get('whatsapp_chat'),
            file_name=data.get('file_name'),
            file_size=data.get('file_size'),
            content=content
        )

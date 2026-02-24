"""
Approval Handler
Manages approval workflow for sensitive tasks
"""

from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass
import logging

from ..utils.task_file import TaskFile


@dataclass
class ApprovalResult:
    """Result of approval processing"""
    status: str  # "approved" | "rejected" | "pending"
    action_executed: bool
    error: Optional[str]


class ApprovalHandler:
    """Handles approval workflow for sensitive tasks"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize approval handler.

        Args:
            logger: Logger instance
        """
        self.logger = logger or logging.getLogger(__name__)

    def detect_approval_marker(self, task: TaskFile) -> Optional[bool]:
        """
        Detect approval marker in task YAML frontmatter.

        Args:
            task: TaskFile object

        Returns:
            True if approved, False if rejected, None if pending
        """
        return task.approved

    def process_approval(self, task: TaskFile) -> ApprovalResult:
        """
        Process approval decision for task.

        Args:
            task: TaskFile from Pending_Approval folder

        Returns:
            ApprovalResult with status and execution result
        """
        # Check approval status
        approval_status = self.detect_approval_marker(task)

        if approval_status is None:
            # Still pending
            return ApprovalResult(
                status="pending",
                action_executed=False,
                error=None
            )

        if approval_status is False:
            # Rejected
            self.logger.info(f"Task {task.id} rejected by user")
            return ApprovalResult(
                status="rejected",
                action_executed=False,
                error=None
            )

        # Approved - execute action
        self.logger.info(f"Task {task.id} approved by user")

        # For now, just mark as approved
        # MCP action execution will be added in Phase 6 & 7
        return ApprovalResult(
            status="approved",
            action_executed=False,  # Will be True when MCP is integrated
            error=None
        )

    def mark_approved(self, task: TaskFile, approved_by: str = "human") -> None:
        """
        Mark task as approved.

        Args:
            task: TaskFile to approve
            approved_by: Who approved (always "human")
        """
        task.approved = True
        task.approved_by = approved_by
        task.approved_at = datetime.now().isoformat()

    def mark_rejected(self, task: TaskFile, reason: Optional[str] = None) -> None:
        """
        Mark task as rejected.

        Args:
            task: TaskFile to reject
            reason: Optional rejection reason
        """
        task.approved = False
        task.approved_by = "human"
        task.approved_at = datetime.now().isoformat()

        if reason:
            task.content += f"\n\n## Rejection Reason\n\n{reason}\n"

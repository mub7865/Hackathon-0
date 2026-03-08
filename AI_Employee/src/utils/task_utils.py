"""
Task utilities for multi-step task management
Implements Multi-Step Task entity structure for Ralph Wiggum loop
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum


class TaskStatus(Enum):
    """Task status enumeration"""
    NEEDS_ACTION = "needs_action"
    IN_PROGRESS = "in_progress"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    DONE = "done"
    STUCK = "stuck"


class TaskType(Enum):
    """Task type enumeration"""
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    LINKEDIN = "linkedin"
    ACCOUNTING = "accounting"
    SOCIAL_MEDIA = "social_media"
    GENERAL = "general"


class TaskPriority(Enum):
    """Task priority enumeration"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class SubTask:
    """Represents a single step in a multi-step task"""
    step_number: int
    description: str
    status: str = "pending"  # pending, completed, failed
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'step_number': self.step_number,
            'description': self.description,
            'status': self.status,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SubTask':
        """Create from dictionary"""
        return cls(
            step_number=data['step_number'],
            description=data['description'],
            status=data.get('status', 'pending'),
            completed_at=datetime.fromisoformat(data['completed_at']) if data.get('completed_at') else None,
            error_message=data.get('error_message')
        )


@dataclass
class MultiStepTask:
    """
    Represents a complex workflow with multiple sub-tasks
    Used by Ralph Wiggum loop for autonomous task completion
    """
    task_id: str
    title: str
    task_type: TaskType
    priority: TaskPriority
    status: TaskStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    current_iteration: int = 0
    max_iterations: int = 10  # From clarifications
    sub_tasks: List[SubTask] = field(default_factory=list)
    requires_approval: bool = False
    approval_reason: Optional[str] = None
    error_history: List[Dict[str, Any]] = field(default_factory=list)
    file_path: Optional[str] = None

    def is_complete(self) -> bool:
        """Check if all sub-tasks are completed"""
        if not self.sub_tasks:
            return False
        return all(sub.status == "completed" for sub in self.sub_tasks)

    def is_stuck(self) -> bool:
        """Check if task has reached max iterations"""
        return self.current_iteration >= self.max_iterations

    def needs_approval(self) -> bool:
        """Check if task requires human approval"""
        return self.requires_approval

    def increment_iteration(self) -> None:
        """Increment iteration counter"""
        self.current_iteration += 1

    def add_error(self, iteration: int, error_message: str) -> None:
        """Add error to history"""
        self.error_history.append({
            'iteration': iteration,
            'error_message': error_message,
            'timestamp': datetime.now().isoformat()
        })

    def mark_subtask_complete(self, step_number: int) -> None:
        """Mark a sub-task as completed"""
        for sub in self.sub_tasks:
            if sub.step_number == step_number:
                sub.status = "completed"
                sub.completed_at = datetime.now()
                break

    def mark_subtask_failed(self, step_number: int, error_message: str) -> None:
        """Mark a sub-task as failed"""
        for sub in self.sub_tasks:
            if sub.step_number == step_number:
                sub.status = "failed"
                sub.error_message = error_message
                break

    def get_next_pending_subtask(self) -> Optional[SubTask]:
        """Get the next pending sub-task"""
        for sub in self.sub_tasks:
            if sub.status == "pending":
                return sub
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'task_id': self.task_id,
            'title': self.title,
            'task_type': self.task_type.value,
            'priority': self.priority.value,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'current_iteration': self.current_iteration,
            'max_iterations': self.max_iterations,
            'sub_tasks': [sub.to_dict() for sub in self.sub_tasks],
            'requires_approval': self.requires_approval,
            'approval_reason': self.approval_reason,
            'error_history': self.error_history,
            'file_path': self.file_path
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MultiStepTask':
        """Create from dictionary"""
        return cls(
            task_id=data['task_id'],
            title=data['title'],
            task_type=TaskType(data['task_type']),
            priority=TaskPriority(data['priority']),
            status=TaskStatus(data['status']),
            created_at=datetime.fromisoformat(data['created_at']),
            started_at=datetime.fromisoformat(data['started_at']) if data.get('started_at') else None,
            completed_at=datetime.fromisoformat(data['completed_at']) if data.get('completed_at') else None,
            current_iteration=data.get('current_iteration', 0),
            max_iterations=data.get('max_iterations', 10),
            sub_tasks=[SubTask.from_dict(sub) for sub in data.get('sub_tasks', [])],
            requires_approval=data.get('requires_approval', False),
            approval_reason=data.get('approval_reason'),
            error_history=data.get('error_history', []),
            file_path=data.get('file_path')
        )


def parse_subtasks_from_markdown(content: str) -> List[SubTask]:
    """
    Parse sub-tasks from markdown content
    Looks for checkbox lists in the format:
    - [ ] Step description
    - [x] Completed step
    """
    sub_tasks = []
    step_number = 1

    for line in content.split('\n'):
        line = line.strip()
        if line.startswith('- [ ]') or line.startswith('- [x]') or line.startswith('- [X]'):
            is_completed = '[x]' in line.lower()
            description = line.split(']', 1)[1].strip()

            sub_task = SubTask(
                step_number=step_number,
                description=description,
                status="completed" if is_completed else "pending",
                completed_at=datetime.now() if is_completed else None
            )
            sub_tasks.append(sub_task)
            step_number += 1

    return sub_tasks

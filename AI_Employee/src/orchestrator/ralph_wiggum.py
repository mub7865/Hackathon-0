"""
Ralph Wiggum Loop - Autonomous Multi-Step Task Completion
Named after Ralph Wiggum's "I'm helping!" persistence

Enables AI to continue working through multi-step tasks without stopping
after each step, with max iteration limit to prevent infinite loops.
"""

import os
import logging
from pathlib import Path
from typing import Optional, Callable, Any
from datetime import datetime

from src.utils.task_utils import MultiStepTask, TaskStatus, parse_subtasks_from_markdown
from src.utils.file_utils import (
    parse_task_file,
    update_task_frontmatter,
    increment_task_iteration,
    mark_task_stuck,
    move_task_file,
    get_task_iteration_count
)

logger = logging.getLogger(__name__)


class RalphWiggumLoop:
    """
    Autonomous multi-step task execution loop

    Continues processing a task until:
    - All sub-tasks are complete
    - Approval is required
    - Max iterations reached (stuck)
    - Unrecoverable error occurs
    """

    def __init__(self, task_file_path: str, max_iterations: int = 10):
        """
        Initialize Ralph Wiggum loop

        Args:
            task_file_path: Path to the task file
            max_iterations: Maximum iterations before marking as stuck (default: 10)
        """
        self.task_file_path = task_file_path
        self.max_iterations = max_iterations
        self.vault_root = Path(task_file_path).parent.parent

        logger.info(f"Initialized Ralph Wiggum loop for task: {task_file_path}")

    def execute(self, task_processor: Callable[[MultiStepTask], bool]) -> str:
        """
        Execute the Ralph Wiggum loop

        Args:
            task_processor: Function that processes one iteration of the task
                           Should return True if task needs another iteration,
                           False if task is complete or needs approval

        Returns:
            Final status: 'done', 'pending_approval', 'stuck', or 'error'
        """
        iteration = 0

        try:
            # Load task
            task = self._load_task()

            # Update status to in_progress
            update_task_frontmatter(
                self.task_file_path,
                {
                    'status': 'in_progress',
                    'started_at': datetime.now().isoformat()
                }
            )

            logger.info(f"Starting Ralph Wiggum loop for task: {task.title}")

            while iteration < self.max_iterations:
                iteration += 1
                logger.info(f"Iteration {iteration}/{self.max_iterations}")

                # Increment iteration counter in file
                increment_task_iteration(self.task_file_path)

                # Check if task is complete
                if task.is_complete():
                    logger.info("Task complete - all sub-tasks finished")
                    return self._complete_task()

                # Check if approval is needed
                if task.needs_approval():
                    logger.info("Task requires approval")
                    return self._request_approval(task.approval_reason)

                # Process one iteration
                try:
                    needs_more_work = task_processor(task)

                    # Reload task to get updated state
                    task = self._load_task()

                    if not needs_more_work:
                        # Task processor indicates completion
                        if task.is_complete():
                            return self._complete_task()
                        elif task.needs_approval():
                            return self._request_approval(task.approval_reason)
                        else:
                            # Task processor says done but task not complete
                            # This might be an error state
                            logger.warning("Task processor returned False but task not complete")
                            break

                except Exception as e:
                    logger.error(f"Error in iteration {iteration}: {e}")
                    task.add_error(iteration, str(e))

                    # Update error history in file
                    frontmatter, body = parse_task_file(self.task_file_path)
                    error_history = frontmatter.get('error_history', [])
                    error_history.append({
                        'iteration': iteration,
                        'error_message': str(e),
                        'timestamp': datetime.now().isoformat()
                    })
                    update_task_frontmatter(
                        self.task_file_path,
                        {'error_history': error_history}
                    )

                    # Check if we should continue or abort
                    consecutive_errors = self._count_consecutive_errors(error_history)
                    if consecutive_errors >= 3:
                        logger.error("3 consecutive errors - aborting")
                        return self._mark_error("3 consecutive errors")

            # Max iterations reached
            logger.warning(f"Max iterations ({self.max_iterations}) reached - marking as stuck")
            return self._mark_stuck("Max iterations reached")

        except Exception as e:
            logger.error(f"Fatal error in Ralph Wiggum loop: {e}")
            return self._mark_error(str(e))

    def _load_task(self) -> MultiStepTask:
        """Load task from file"""
        frontmatter, body = parse_task_file(self.task_file_path)

        # Parse sub-tasks from markdown
        sub_tasks = parse_subtasks_from_markdown(body)

        # Create MultiStepTask object
        from src.utils.task_utils import TaskType, TaskPriority

        task = MultiStepTask(
            task_id=Path(self.task_file_path).stem,
            title=frontmatter.get('title', 'Untitled Task'),
            task_type=TaskType(frontmatter.get('type', 'general')),
            priority=TaskPriority(frontmatter.get('priority', 'medium')),
            status=TaskStatus(frontmatter.get('status', 'needs_action')),
            created_at=datetime.fromisoformat(frontmatter['created']),
            started_at=datetime.fromisoformat(frontmatter['started_at']) if frontmatter.get('started_at') else None,
            current_iteration=frontmatter.get('current_iteration', 0),
            max_iterations=frontmatter.get('max_iterations', self.max_iterations),
            sub_tasks=sub_tasks,
            requires_approval=frontmatter.get('requires_approval', False),
            approval_reason=frontmatter.get('approval_reason'),
            error_history=frontmatter.get('error_history', []),
            file_path=self.task_file_path
        )

        return task

    def _complete_task(self) -> str:
        """Mark task as complete and move to Done folder"""
        update_task_frontmatter(
            self.task_file_path,
            {
                'status': 'done',
                'completed_at': datetime.now().isoformat()
            }
        )

        # Move to Done folder
        new_path = move_task_file(self.task_file_path, 'Done')
        logger.info(f"Task completed and moved to: {new_path}")

        return 'done'

    def _request_approval(self, reason: Optional[str] = None) -> str:
        """Move task to Pending_Approval folder"""
        update_task_frontmatter(
            self.task_file_path,
            {
                'status': 'pending_approval',
                'approval_requested_at': datetime.now().isoformat(),
                'approval_reason': reason or 'Task requires human approval'
            }
        )

        # Move to Pending_Approval folder
        new_path = move_task_file(self.task_file_path, 'Pending_Approval')
        logger.info(f"Approval requested, moved to: {new_path}")

        return 'pending_approval'

    def _mark_stuck(self, reason: str) -> str:
        """Mark task as stuck (max iterations reached)"""
        mark_task_stuck(self.task_file_path, reason)

        # Move back to Needs_Action with stuck flag
        new_path = move_task_file(self.task_file_path, 'Needs_Action')
        logger.warning(f"Task stuck, moved to: {new_path}")

        return 'stuck'

    def _mark_error(self, error_message: str) -> str:
        """Mark task with error status"""
        update_task_frontmatter(
            self.task_file_path,
            {
                'status': 'error',
                'error_message': error_message,
                'error_at': datetime.now().isoformat()
            }
        )

        # Move to Needs_Action for human review
        new_path = move_task_file(self.task_file_path, 'Needs_Action')
        logger.error(f"Task error, moved to: {new_path}")

        return 'error'

    def _count_consecutive_errors(self, error_history: list) -> int:
        """Count consecutive errors from the end of error history"""
        if not error_history:
            return 0

        # Sort by iteration (most recent last)
        sorted_errors = sorted(error_history, key=lambda x: x.get('iteration', 0))

        # Count consecutive errors from the end
        consecutive = 0
        for error in reversed(sorted_errors):
            if error.get('error_message'):
                consecutive += 1
            else:
                break

        return consecutive


def is_task_stuck(task_file_path: str) -> bool:
    """
    Check if a task has reached max iterations

    Args:
        task_file_path: Path to the task file

    Returns:
        True if task is stuck (current >= max iterations)
    """
    current, max_iter = get_task_iteration_count(task_file_path)
    return current >= max_iter


def reset_stuck_task(task_file_path: str) -> None:
    """
    Reset a stuck task (human intervention)

    Args:
        task_file_path: Path to the task file
    """
    update_task_frontmatter(
        task_file_path,
        {
            'current_iteration': 0,
            'status': 'needs_action',
            'stuck_reason': None,
            'stuck_at': None,
            'reset_at': datetime.now().isoformat()
        }
    )
    logger.info(f"Reset stuck task: {task_file_path}")

"""
Retry handler with exponential backoff
Implements resilient error recovery for transient failures
"""

import time
import random
import logging
from functools import wraps
from typing import Callable, Type, Tuple, Optional
import uuid
from datetime import datetime

from src.utils.error_utils import (
    ErrorLog,
    ErrorType,
    classify_error,
    log_error_to_file,
    ResolutionStatus
)

logger = logging.getLogger(__name__)


class RetryExhausted(Exception):
    """Raised when all retry attempts are exhausted"""
    pass


class CircuitBreakerOpen(Exception):
    """Raised when circuit breaker is open (too many failures)"""
    pass


# Circuit breaker state tracking
_circuit_breakers = {}


def with_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retry_on: Tuple[Type[Exception], ...] = (Exception,),
    component: str = "unknown",
    operation: str = "unknown"
):
    """
    Decorator for automatic retry with exponential backoff

    Args:
        max_attempts: Maximum number of retry attempts (default: 3)
        base_delay: Initial delay in seconds (default: 1.0)
        max_delay: Maximum delay in seconds (default: 60.0)
        exponential_base: Base for exponential backoff (default: 2.0)
        jitter: Add random jitter to prevent thundering herd (default: True)
        retry_on: Tuple of exception types to retry on (default: all exceptions)
        component: Component name for error logging
        operation: Operation name for error logging

    Returns:
        Decorated function with retry logic

    Example:
        @with_retry(max_attempts=3, base_delay=1, component="odoo_client", operation="create_invoice")
        def create_invoice(data):
            # Your code here
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            last_exception = None

            while attempt < max_attempts:
                try:
                    # Check circuit breaker
                    if _is_circuit_breaker_open(component, operation):
                        raise CircuitBreakerOpen(
                            f"Circuit breaker open for {component}.{operation}"
                        )

                    # Execute function
                    result = func(*args, **kwargs)

                    # Success - reset circuit breaker
                    _record_success(component, operation)

                    # If this was a retry, log success
                    if attempt > 0:
                        logger.info(
                            f"Retry successful for {component}.{operation} "
                            f"after {attempt} attempts"
                        )

                    return result

                except retry_on as e:
                    attempt += 1
                    last_exception = e

                    # Classify error
                    error_type = classify_error(e, component, operation)

                    # Create error log
                    error_log = ErrorLog(
                        error_id=str(uuid.uuid4()),
                        timestamp=datetime.now(),
                        error_type=error_type,
                        component=component,
                        operation=operation,
                        error_message=str(e),
                        retry_count=attempt,
                        max_retries=max_attempts,
                        context={
                            'function': func.__name__,
                            'args': str(args)[:200],  # Truncate for safety
                            'kwargs': str(kwargs)[:200]
                        }
                    )

                    # Don't retry permanent or authentication errors
                    if error_type in [ErrorType.PERMANENT, ErrorType.AUTHENTICATION]:
                        logger.error(
                            f"{error_type.value} error in {component}.{operation}: {e}"
                        )
                        error_log.mark_requires_human()
                        log_error_to_file(error_log)
                        _record_failure(component, operation)
                        raise

                    # Check if we should retry
                    if attempt >= max_attempts:
                        logger.error(
                            f"Max retry attempts ({max_attempts}) exhausted for "
                            f"{component}.{operation}: {e}"
                        )
                        error_log.resolution_status = ResolutionStatus.REQUIRES_HUMAN
                        log_error_to_file(error_log)
                        _record_failure(component, operation)
                        raise RetryExhausted(
                            f"Failed after {max_attempts} attempts: {e}"
                        ) from e

                    # Calculate delay with exponential backoff
                    delay = min(
                        base_delay * (exponential_base ** (attempt - 1)),
                        max_delay
                    )

                    # Add jitter to prevent thundering herd
                    if jitter:
                        delay = delay * (0.5 + random.random())

                    logger.warning(
                        f"Attempt {attempt}/{max_attempts} failed for "
                        f"{component}.{operation}: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )

                    # Log error
                    log_error_to_file(error_log)

                    # Wait before retry
                    time.sleep(delay)

            # Should never reach here, but just in case
            _record_failure(component, operation)
            raise RetryExhausted(
                f"Failed after {max_attempts} attempts: {last_exception}"
            ) from last_exception

        return wrapper
    return decorator


def retry_transient_errors(
    component: str,
    operation: str,
    max_attempts: int = 3
):
    """
    Simplified retry decorator for transient errors only

    Args:
        component: Component name
        operation: Operation name
        max_attempts: Maximum retry attempts

    Example:
        @retry_transient_errors("odoo_client", "authenticate")
        def authenticate():
            # Your code here
            pass
    """
    return with_retry(
        max_attempts=max_attempts,
        base_delay=1.0,
        max_delay=60.0,
        component=component,
        operation=operation
    )


# Circuit Breaker Implementation

def _get_circuit_breaker_key(component: str, operation: str) -> str:
    """Get circuit breaker key"""
    return f"{component}.{operation}"


def _is_circuit_breaker_open(component: str, operation: str) -> bool:
    """Check if circuit breaker is open"""
    key = _get_circuit_breaker_key(component, operation)

    if key not in _circuit_breakers:
        return False

    breaker = _circuit_breakers[key]

    # Check if breaker should be reset (5 minutes timeout)
    if time.time() - breaker['opened_at'] > 300:
        logger.info(f"Circuit breaker timeout expired for {key}, resetting")
        del _circuit_breakers[key]
        return False

    return breaker['is_open']


def _record_failure(component: str, operation: str) -> None:
    """Record a failure for circuit breaker"""
    key = _get_circuit_breaker_key(component, operation)

    if key not in _circuit_breakers:
        _circuit_breakers[key] = {
            'is_open': False,
            'failure_count': 0,
            'success_count': 0,
            'opened_at': None
        }

    breaker = _circuit_breakers[key]
    breaker['failure_count'] += 1
    breaker['success_count'] = 0  # Reset success count

    # Open circuit breaker if too many failures (5 consecutive)
    if breaker['failure_count'] >= 5:
        breaker['is_open'] = True
        breaker['opened_at'] = time.time()
        logger.error(
            f"Circuit breaker opened for {key} after {breaker['failure_count']} failures"
        )


def _record_success(component: str, operation: str) -> None:
    """Record a success for circuit breaker"""
    key = _get_circuit_breaker_key(component, operation)

    if key not in _circuit_breakers:
        return

    breaker = _circuit_breakers[key]
    breaker['success_count'] += 1
    breaker['failure_count'] = 0  # Reset failure count

    # Close circuit breaker after 3 consecutive successes
    if breaker['success_count'] >= 3 and breaker['is_open']:
        logger.info(f"Circuit breaker closed for {key} after successful recovery")
        del _circuit_breakers[key]


def reset_circuit_breaker(component: str, operation: str) -> None:
    """
    Manually reset circuit breaker (human intervention)

    Args:
        component: Component name
        operation: Operation name
    """
    key = _get_circuit_breaker_key(component, operation)

    if key in _circuit_breakers:
        del _circuit_breakers[key]
        logger.info(f"Circuit breaker manually reset for {key}")


def get_circuit_breaker_status() -> dict:
    """
    Get status of all circuit breakers

    Returns:
        Dictionary of circuit breaker states
    """
    return {
        key: {
            'is_open': breaker['is_open'],
            'failure_count': breaker['failure_count'],
            'success_count': breaker['success_count'],
            'opened_at': breaker['opened_at']
        }
        for key, breaker in _circuit_breakers.items()
    }


# Graceful Degradation Support

class ActionQueue:
    """Queue for actions when services are unavailable"""

    def __init__(self, queue_file: str = None):
        """
        Initialize action queue

        Args:
            queue_file: Path to queue file (default: vault/Logs/action_queue.json)
        """
        if queue_file is None:
            from pathlib import Path
            vault_path = Path(__file__).parent.parent.parent / "vault"
            queue_dir = vault_path / "Logs"
            queue_dir.mkdir(parents=True, exist_ok=True)
            queue_file = str(queue_dir / "action_queue.json")

        self.queue_file = queue_file

    def enqueue(self, component: str, operation: str, data: dict) -> None:
        """
        Add action to queue

        Args:
            component: Component name
            operation: Operation name
            data: Action data
        """
        import json
        from pathlib import Path

        # Load existing queue
        queue = []
        if Path(self.queue_file).exists():
            try:
                with open(self.queue_file, 'r') as f:
                    queue = json.load(f)
            except:
                queue = []

        # Add new action
        queue.append({
            'id': str(uuid.uuid4()),
            'component': component,
            'operation': operation,
            'data': data,
            'queued_at': datetime.now().isoformat(),
            'status': 'pending'
        })

        # Save queue
        with open(self.queue_file, 'w') as f:
            json.dump(queue, f, indent=2)

        logger.info(f"Queued action: {component}.{operation}")

    def dequeue_pending(self) -> list:
        """
        Get all pending actions from queue

        Returns:
            List of pending actions
        """
        import json
        from pathlib import Path

        if not Path(self.queue_file).exists():
            return []

        try:
            with open(self.queue_file, 'r') as f:
                queue = json.load(f)
        except:
            return []

        return [action for action in queue if action['status'] == 'pending']

    def mark_processed(self, action_id: str) -> None:
        """
        Mark action as processed

        Args:
            action_id: Action ID
        """
        import json
        from pathlib import Path

        if not Path(self.queue_file).exists():
            return

        try:
            with open(self.queue_file, 'r') as f:
                queue = json.load(f)
        except:
            return

        # Update status
        for action in queue:
            if action['id'] == action_id:
                action['status'] = 'processed'
                action['processed_at'] = datetime.now().isoformat()

        # Save queue
        with open(self.queue_file, 'w') as f:
            json.dump(queue, f, indent=2)


# Global action queue instance
_action_queue = ActionQueue()


def queue_action_on_failure(component: str, operation: str, data: dict) -> None:
    """
    Queue an action when service is unavailable (graceful degradation)

    Args:
        component: Component name
        operation: Operation name
        data: Action data
    """
    _action_queue.enqueue(component, operation, data)


def process_queued_actions() -> int:
    """
    Process all queued actions

    Returns:
        Number of actions processed
    """
    pending = _action_queue.dequeue_pending()
    processed = 0

    for action in pending:
        try:
            logger.info(f"Processing queued action: {action['component']}.{action['operation']}")
            # Action processing would be handled by the orchestrator
            # For now, just mark as processed
            _action_queue.mark_processed(action['id'])
            processed += 1
        except Exception as e:
            logger.error(f"Failed to process queued action {action['id']}: {e}")

    return processed

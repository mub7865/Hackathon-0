"""
Error utilities for error logging and classification
Implements Error Log entity structure for resilient error recovery
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
import json
from pathlib import Path


class ErrorType(Enum):
    """Error type classification"""
    TRANSIENT = "transient"  # Network timeout, rate limit, temporary unavailable
    PERMANENT = "permanent"  # Authentication, invalid data, not found
    AUTHENTICATION = "authentication"  # Auth failures, expired tokens
    LOGIC = "logic"  # Business logic errors, validation failures
    DATA = "data"  # Corrupted data, missing fields


class ResolutionStatus(Enum):
    """Error resolution status"""
    RETRYING = "retrying"
    RESOLVED = "resolved"
    REQUIRES_HUMAN = "requires_human"
    IGNORED = "ignored"


@dataclass
class ErrorLog:
    """
    Represents a system error with retry attempts and resolution tracking
    """
    error_id: str
    timestamp: datetime
    error_type: ErrorType
    component: str  # Which component failed (e.g., "odoo_client", "facebook_watcher")
    operation: str  # What was being attempted
    error_message: str
    stack_trace: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    resolution_status: ResolutionStatus = ResolutionStatus.RETRYING
    resolved_at: Optional[datetime] = None
    context: Dict[str, Any] = field(default_factory=dict)
    task_id: Optional[str] = None  # Reference to task if error during task processing

    def should_retry(self) -> bool:
        """Check if error should be retried"""
        if self.error_type == ErrorType.PERMANENT:
            return False
        if self.error_type == ErrorType.AUTHENTICATION:
            return False
        return self.retry_count < self.max_retries

    def increment_retry(self) -> None:
        """Increment retry counter"""
        self.retry_count += 1

    def mark_resolved(self) -> None:
        """Mark error as resolved"""
        self.resolution_status = ResolutionStatus.RESOLVED
        self.resolved_at = datetime.now()

    def mark_requires_human(self) -> None:
        """Mark error as requiring human intervention"""
        self.resolution_status = ResolutionStatus.REQUIRES_HUMAN

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'error_id': self.error_id,
            'timestamp': self.timestamp.isoformat(),
            'error_type': self.error_type.value,
            'component': self.component,
            'operation': self.operation,
            'error_message': self.error_message,
            'stack_trace': self.stack_trace,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'resolution_status': self.resolution_status.value,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'context': self.context,
            'task_id': self.task_id
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ErrorLog':
        """Create from dictionary"""
        return cls(
            error_id=data['error_id'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            error_type=ErrorType(data['error_type']),
            component=data['component'],
            operation=data['operation'],
            error_message=data['error_message'],
            stack_trace=data.get('stack_trace'),
            retry_count=data.get('retry_count', 0),
            max_retries=data.get('max_retries', 3),
            resolution_status=ResolutionStatus(data.get('resolution_status', 'retrying')),
            resolved_at=datetime.fromisoformat(data['resolved_at']) if data.get('resolved_at') else None,
            context=data.get('context', {}),
            task_id=data.get('task_id')
        )


def classify_error(exception: Exception, component: str, operation: str) -> ErrorType:
    """
    Classify an error based on exception type and message

    Args:
        exception: The exception that occurred
        component: Component where error occurred
        operation: Operation being performed

    Returns:
        ErrorType classification
    """
    error_msg = str(exception).lower()
    exception_type = type(exception).__name__

    # Authentication errors
    if any(keyword in error_msg for keyword in ['auth', 'unauthorized', '401', '403', 'forbidden', 'token', 'credential']):
        return ErrorType.AUTHENTICATION

    # Transient errors (network, timeout, rate limit)
    if any(keyword in error_msg for keyword in ['timeout', 'connection', 'network', 'rate limit', '429', '503', 'unavailable', 'temporary']):
        return ErrorType.TRANSIENT

    # Permanent errors (not found, invalid)
    if any(keyword in error_msg for keyword in ['not found', '404', 'invalid', 'does not exist', 'missing']):
        return ErrorType.PERMANENT

    # Data errors (corrupted, malformed)
    if any(keyword in error_msg for keyword in ['corrupt', 'malformed', 'parse', 'decode', 'json', 'yaml']):
        return ErrorType.DATA

    # Logic errors (validation, business rules)
    if any(keyword in error_msg for keyword in ['validation', 'constraint', 'required', 'invalid']):
        return ErrorType.LOGIC

    # Default to transient for unknown errors (safer to retry)
    return ErrorType.TRANSIENT


def log_error_to_file(error_log: ErrorLog, log_file: str = None) -> None:
    """
    Log error to JSON file

    Args:
        error_log: ErrorLog instance to log
        log_file: Path to log file (default: vault/Logs/errors.json)
    """
    if log_file is None:
        # Default to vault/Logs/errors.json
        vault_path = Path(__file__).parent.parent.parent / "vault"
        log_dir = vault_path / "Logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = str(log_dir / "errors.json")

    # Load existing errors
    errors = []
    if Path(log_file).exists():
        try:
            with open(log_file, 'r') as f:
                errors = json.load(f)
        except:
            errors = []

    # Append new error
    errors.append(error_log.to_dict())

    # Write back to file
    with open(log_file, 'w') as f:
        json.dump(errors, f, indent=2)


def get_recent_errors(component: Optional[str] = None, hours: int = 24, log_file: str = None) -> List[ErrorLog]:
    """
    Get recent errors from log file

    Args:
        component: Filter by component (optional)
        hours: Number of hours to look back
        log_file: Path to log file (default: vault/Logs/errors.json)

    Returns:
        List of ErrorLog instances
    """
    if log_file is None:
        vault_path = Path(__file__).parent.parent.parent / "vault"
        log_file = str(vault_path / "Logs" / "errors.json")

    if not Path(log_file).exists():
        return []

    try:
        with open(log_file, 'r') as f:
            errors_data = json.load(f)
    except:
        return []

    # Convert to ErrorLog objects
    errors = [ErrorLog.from_dict(data) for data in errors_data]

    # Filter by time
    cutoff = datetime.now().timestamp() - (hours * 3600)
    errors = [e for e in errors if e.timestamp.timestamp() > cutoff]

    # Filter by component if specified
    if component:
        errors = [e for e in errors if e.component == component]

    return errors


def count_errors_by_type(component: Optional[str] = None, hours: int = 24) -> Dict[str, int]:
    """
    Count errors by type for monitoring

    Args:
        component: Filter by component (optional)
        hours: Number of hours to look back

    Returns:
        Dictionary of error type counts
    """
    errors = get_recent_errors(component, hours)

    counts = {
        'transient': 0,
        'permanent': 0,
        'authentication': 0,
        'logic': 0,
        'data': 0
    }

    for error in errors:
        counts[error.error_type.value] += 1

    return counts


def should_alert_human(component: str, hours: int = 1) -> bool:
    """
    Determine if human should be alerted based on error patterns

    Args:
        component: Component to check
        hours: Time window to analyze

    Returns:
        True if human alert needed
    """
    errors = get_recent_errors(component, hours)

    # Alert if any permanent or authentication errors
    for error in errors:
        if error.error_type in [ErrorType.PERMANENT, ErrorType.AUTHENTICATION]:
            return True

    # Alert if more than 5 errors in the time window
    if len(errors) > 5:
        return True

    # Alert if same operation failing repeatedly
    operation_counts = {}
    for error in errors:
        operation_counts[error.operation] = operation_counts.get(error.operation, 0) + 1

    if any(count >= 3 for count in operation_counts.values()):
        return True

    return False


def create_error_alert(error_log: ErrorLog) -> str:
    """
    Create human-readable error alert message

    Args:
        error_log: ErrorLog instance

    Returns:
        Alert message string
    """
    alert = f"""
🚨 ERROR ALERT

Component: {error_log.component}
Operation: {error_log.operation}
Error Type: {error_log.error_type.value}
Time: {error_log.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

Message: {error_log.error_message}

Retry Count: {error_log.retry_count}/{error_log.max_retries}
Status: {error_log.resolution_status.value}

Suggested Actions:
"""

    if error_log.error_type == ErrorType.AUTHENTICATION:
        alert += "- Check credentials and tokens\n"
        alert += "- Re-authenticate if needed\n"
    elif error_log.error_type == ErrorType.PERMANENT:
        alert += "- Verify the resource exists\n"
        alert += "- Check input data validity\n"
    elif error_log.error_type == ErrorType.TRANSIENT:
        alert += "- System will retry automatically\n"
        alert += "- Check service availability if persists\n"
    else:
        alert += "- Review error details and context\n"
        alert += "- Check system logs for more information\n"

    if error_log.task_id:
        alert += f"\nRelated Task: {error_log.task_id}\n"

    return alert

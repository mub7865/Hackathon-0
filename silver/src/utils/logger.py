"""
Logger Utility

Handles logging to files and console with timestamps.
Includes log rotation and comprehensive error tracking.
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler
import json
import traceback


def setup_logger(
    name: str,
    log_dir: str = "vault/Logs",
    level: str = "INFO",
    max_bytes: int = 10485760,  # 10 MB
    backup_count: int = 5,
    json_format: bool = False
) -> logging.Logger:
    """
    Setup logger with file and console handlers with rotation.

    Args:
        name: Logger name
        log_dir: Directory for log files
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        max_bytes: Maximum log file size before rotation (default: 10 MB)
        backup_count: Number of backup files to keep (default: 5)
        json_format: Use JSON format for structured logging (default: False)

    Returns:
        Configured logger instance
    """
    # Create logs directory if it doesn't exist
    Path(log_dir).mkdir(parents=True, exist_ok=True)

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter('[%(levelname)s] %(message)s')
    console_handler.setFormatter(console_format)

    # Rotating file handler
    log_file = os.path.join(log_dir, f"{name}.log")
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)

    if json_format:
        file_handler.setFormatter(JSONFormatter())
    else:
        file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_format)

    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.

        Args:
            record: Log record to format

        Returns:
            JSON string
        """
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }

        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }

        return json.dumps(log_data)


def log_to_file(log_dir: str, filename: str, content: str):
    """
    Write content to a log file.

    Args:
        log_dir: Directory for log files
        filename: Log filename
        content: Content to write
    """
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    log_path = os.path.join(log_dir, filename)

    with open(log_path, 'a', encoding='utf-8') as f:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f"[{timestamp}] {content}\n")


def create_error_log(log_dir: str, error: Exception, context: str = "") -> str:
    """
    Create an error log file with details.

    Args:
        log_dir: Directory for log files
        error: Exception that occurred
        context: Additional context about the error

    Returns:
        Path to created error log file
    """
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    filename = f"error-{timestamp}.md"

    content = f"""# Error Log

**Timestamp**: {datetime.now().isoformat()}
**Context**: {context}

## Error Details

**Type**: {type(error).__name__}
**Message**: {str(error)}

## Stack Trace

```
{error.__traceback__ if hasattr(error, '__traceback__') else 'No traceback available'}
```

## Resolution

Check the error message above and refer to troubleshooting guide in README.md.
"""

    log_path = os.path.join(log_dir, filename)
    with open(log_path, 'w', encoding='utf-8') as f:
        f.write(content)

    return log_path

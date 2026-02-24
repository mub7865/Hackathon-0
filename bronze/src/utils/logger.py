"""
Logger Utility

Handles logging to files and console with timestamps.
"""

import logging
import os
from datetime import datetime
from pathlib import Path


def setup_logger(name: str, log_dir: str = "vault/Logs", level: str = "INFO") -> logging.Logger:
    """
    Setup logger with file and console handlers.

    Args:
        name: Logger name
        log_dir: Directory for log files
        level: Logging level (DEBUG, INFO, WARNING, ERROR)

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

    # File handler
    log_file = os.path.join(log_dir, f"{name}-{datetime.now().strftime('%Y%m%d')}.log")
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_format)

    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


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

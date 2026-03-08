"""
Error Handling Utilities
Provides retry logic, exponential backoff, and graceful degradation
"""

import time
import logging
from typing import Callable, Any, Optional, Type
from functools import wraps


class TransientError(Exception):
    """Error that may succeed on retry"""
    pass


class PermanentError(Exception):
    """Error that won't succeed on retry"""
    pass


def retry_with_backoff(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential: bool = True
):
    """
    Decorator for retrying functions with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential: Use exponential backoff if True, constant if False

    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            logger = logging.getLogger(func.__module__)

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except PermanentError:
                    # Don't retry permanent errors
                    raise
                except Exception as e:
                    if attempt == max_attempts - 1:
                        logger.error(f"{func.__name__} failed after {max_attempts} attempts: {e}")
                        raise

                    # Calculate delay
                    if exponential:
                        delay = min(base_delay * (2 ** attempt), max_delay)
                    else:
                        delay = base_delay

                    logger.warning(f"{func.__name__} attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                    time.sleep(delay)

            return None  # Should never reach here

        return wrapper
    return decorator


def log_error(
    error: Exception,
    context: str,
    logger: Optional[logging.Logger] = None
) -> None:
    """
    Log error with context.

    Args:
        error: Exception to log
        context: Context description
        logger: Logger instance (creates new if None)
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    logger.error(f"{context}: {type(error).__name__}: {str(error)}")


def graceful_degradation(
    func: Callable,
    fallback_value: Any = None,
    error_types: tuple = (Exception,)
) -> Callable:
    """
    Decorator for graceful degradation on errors.

    Args:
        func: Function to wrap
        fallback_value: Value to return on error
        error_types: Tuple of exception types to catch

    Returns:
        Decorated function
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        logger = logging.getLogger(func.__module__)
        try:
            return func(*args, **kwargs)
        except error_types as e:
            logger.warning(f"{func.__name__} failed, using fallback: {e}")
            return fallback_value

    return wrapper


class ErrorHandler:
    """Centralized error handling"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize error handler.

        Args:
            logger: Logger instance
        """
        self.logger = logger or logging.getLogger(__name__)

    def handle_error(
        self,
        error: Exception,
        context: str,
        fatal: bool = False
    ) -> None:
        """
        Handle error with logging and optional re-raise.

        Args:
            error: Exception to handle
            context: Context description
            fatal: Re-raise if True
        """
        log_error(error, context, self.logger)

        if fatal:
            raise error

    def is_transient(self, error: Exception) -> bool:
        """
        Determine if error is transient (worth retrying).

        Args:
            error: Exception to check

        Returns:
            True if transient, False if permanent
        """
        # Network errors are usually transient
        transient_errors = [
            'ConnectionError',
            'TimeoutError',
            'ConnectionResetError',
            'BrokenPipeError',
            'ECONNRESET',
            'rate limit',
            'timeout'
        ]

        error_str = str(error).lower()
        error_type = type(error).__name__

        return any(
            keyword in error_str or keyword in error_type.lower()
            for keyword in transient_errors
        )

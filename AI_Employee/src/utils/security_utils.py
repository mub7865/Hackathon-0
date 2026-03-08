"""
Security Utilities Module
Provides input validation, sanitization, and rate limiting for security hardening
"""

import re
import os
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class SecurityValidationError(Exception):
    """Exception raised for security validation failures"""
    pass


# Constants
MAX_AMOUNT = 1_000_000.00  # $1M max transaction
MIN_AMOUNT = 0.01  # $0.01 min transaction
MAX_TEXT_LENGTH = 1000  # Max length for text fields
MAX_PARTY_NAME_LENGTH = 200  # Max length for party names
MAX_DATE_FUTURE_DAYS = 365  # Max 1 year in future
MAX_DATE_PAST_DAYS = 3650  # Max 10 years in past

# Allowed characters patterns
PARTY_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9\s\-\.\,\&\']+$')
DESCRIPTION_PATTERN = re.compile(r'^[a-zA-Z0-9\s\-\.\,\;\:\!\?\(\)\[\]\&\'\"\/\#\@\+\=\*]+$')
CATEGORY_PATTERN = re.compile(r'^[a-zA-Z0-9\s\-\/]+$')


def validate_amount(amount: float, field_name: str = "amount") -> Tuple[bool, Optional[str]]:
    """
    Validate transaction amount

    Args:
        amount: Amount to validate
        field_name: Name of the field (for error messages)

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Check type
        if not isinstance(amount, (int, float)):
            return False, f"{field_name} must be a number"

        # Convert to float
        amount = float(amount)

        # Check range
        if amount < MIN_AMOUNT:
            return False, f"{field_name} must be at least ${MIN_AMOUNT:.2f}"

        if amount > MAX_AMOUNT:
            return False, f"{field_name} cannot exceed ${MAX_AMOUNT:,.2f}"

        # Check for reasonable precision (max 2 decimal places)
        if round(amount, 2) != amount:
            return False, f"{field_name} must have at most 2 decimal places"

        return True, None

    except (ValueError, TypeError) as e:
        return False, f"Invalid {field_name}: {str(e)}"


def validate_date(date_str: str, field_name: str = "date") -> Tuple[bool, Optional[str]]:
    """
    Validate date string

    Args:
        date_str: Date string in YYYY-MM-DD format
        field_name: Name of the field (for error messages)

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Check format
        if not isinstance(date_str, str):
            return False, f"{field_name} must be a string"

        # Parse date
        parsed_date = datetime.strptime(date_str, '%Y-%m-%d').date()

        # Check not too far in past
        min_date = date.today() - timedelta(days=MAX_DATE_PAST_DAYS)
        if parsed_date < min_date:
            return False, f"{field_name} cannot be more than {MAX_DATE_PAST_DAYS} days in the past"

        # Check not too far in future
        max_date = date.today() + timedelta(days=MAX_DATE_FUTURE_DAYS)
        if parsed_date > max_date:
            return False, f"{field_name} cannot be more than {MAX_DATE_FUTURE_DAYS} days in the future"

        return True, None

    except ValueError:
        return False, f"Invalid {field_name} format. Expected YYYY-MM-DD"


def sanitize_text(text: str, field_name: str = "text", max_length: int = MAX_TEXT_LENGTH) -> Tuple[bool, Optional[str], str]:
    """
    Sanitize and validate text input

    Args:
        text: Text to sanitize
        field_name: Name of the field (for error messages)
        max_length: Maximum allowed length

    Returns:
        Tuple of (is_valid, error_message, sanitized_text)
    """
    try:
        # Check type
        if not isinstance(text, str):
            return False, f"{field_name} must be a string", ""

        # Strip whitespace
        sanitized = text.strip()

        # Check not empty
        if not sanitized:
            return False, f"{field_name} cannot be empty", ""

        # Check length
        if len(sanitized) > max_length:
            return False, f"{field_name} cannot exceed {max_length} characters", ""

        # Remove null bytes (security risk)
        sanitized = sanitized.replace('\x00', '')

        # Remove control characters except newlines and tabs
        sanitized = ''.join(char for char in sanitized if char == '\n' or char == '\t' or ord(char) >= 32)

        return True, None, sanitized

    except Exception as e:
        return False, f"Error sanitizing {field_name}: {str(e)}", ""


def validate_party_name(party_name: str, field_name: str = "party_name") -> Tuple[bool, Optional[str], str]:
    """
    Validate and sanitize party name (customer/vendor)

    Args:
        party_name: Party name to validate
        field_name: Name of the field (for error messages)

    Returns:
        Tuple of (is_valid, error_message, sanitized_name)
    """
    # First sanitize
    is_valid, error_msg, sanitized = sanitize_text(party_name, field_name, MAX_PARTY_NAME_LENGTH)
    if not is_valid:
        return False, error_msg, ""

    # Check pattern (alphanumeric, spaces, hyphens, periods, commas, ampersands, apostrophes)
    if not PARTY_NAME_PATTERN.match(sanitized):
        return False, f"{field_name} contains invalid characters. Only letters, numbers, spaces, hyphens, periods, commas, ampersands, and apostrophes are allowed", ""

    return True, None, sanitized


def validate_description(description: str, field_name: str = "description") -> Tuple[bool, Optional[str], str]:
    """
    Validate and sanitize description text

    Args:
        description: Description to validate
        field_name: Name of the field (for error messages)

    Returns:
        Tuple of (is_valid, error_message, sanitized_description)
    """
    # First sanitize
    is_valid, error_msg, sanitized = sanitize_text(description, field_name, MAX_TEXT_LENGTH)
    if not is_valid:
        return False, error_msg, ""

    # Check pattern (more permissive than party names)
    if not DESCRIPTION_PATTERN.match(sanitized):
        return False, f"{field_name} contains invalid characters", ""

    return True, None, sanitized


def validate_category(category: str, field_name: str = "category") -> Tuple[bool, Optional[str], str]:
    """
    Validate and sanitize category name

    Args:
        category: Category to validate
        field_name: Name of the field (for error messages)

    Returns:
        Tuple of (is_valid, error_message, sanitized_category)
    """
    # First sanitize
    is_valid, error_msg, sanitized = sanitize_text(category, field_name, 100)
    if not is_valid:
        return False, error_msg, ""

    # Check pattern (alphanumeric, spaces, hyphens, slashes)
    if not CATEGORY_PATTERN.match(sanitized):
        return False, f"{field_name} contains invalid characters. Only letters, numbers, spaces, hyphens, and slashes are allowed", ""

    return True, None, sanitized


def sanitize_file_path(file_path: str, base_path: Optional[str] = None) -> Tuple[bool, Optional[str], str]:
    """
    Sanitize and validate file path to prevent directory traversal attacks

    Args:
        file_path: File path to sanitize
        base_path: Base directory path (optional, defaults to vault path)

    Returns:
        Tuple of (is_valid, error_message, sanitized_path)
    """
    try:
        # Get base path
        if base_path is None:
            base_path = os.getenv('VAULT_PATH', str(Path(__file__).parent.parent.parent / 'vault'))

        base_path = Path(base_path).resolve()

        # Resolve the file path
        resolved_path = Path(file_path).resolve()

        # Check if resolved path is within base path
        try:
            resolved_path.relative_to(base_path)
        except ValueError:
            return False, "File path is outside allowed directory", ""

        # Check for suspicious patterns
        suspicious_patterns = ['..', '~', '$', '`', '|', ';', '&', '>', '<', '\x00']
        for pattern in suspicious_patterns:
            if pattern in str(file_path):
                return False, f"File path contains suspicious pattern: {pattern}", ""

        return True, None, str(resolved_path)

    except Exception as e:
        return False, f"Error sanitizing file path: {str(e)}", ""


def validate_transaction_data(
    amount: float,
    party: str,
    description: str,
    transaction_date: str,
    category: Optional[str] = None
) -> Tuple[bool, Optional[str], dict]:
    """
    Validate all transaction data at once

    Args:
        amount: Transaction amount
        party: Customer/vendor name
        description: Transaction description
        transaction_date: Transaction date (YYYY-MM-DD)
        category: Expense category (optional)

    Returns:
        Tuple of (is_valid, error_message, sanitized_data)
    """
    sanitized_data = {}

    # Validate amount
    is_valid, error_msg = validate_amount(amount)
    if not is_valid:
        return False, error_msg, {}
    sanitized_data['amount'] = float(amount)

    # Validate party name
    is_valid, error_msg, sanitized_party = validate_party_name(party)
    if not is_valid:
        return False, error_msg, {}
    sanitized_data['party'] = sanitized_party

    # Validate description
    is_valid, error_msg, sanitized_desc = validate_description(description)
    if not is_valid:
        return False, error_msg, {}
    sanitized_data['description'] = sanitized_desc

    # Validate date
    is_valid, error_msg = validate_date(transaction_date)
    if not is_valid:
        return False, error_msg, {}
    sanitized_data['date'] = transaction_date

    # Validate category if provided
    if category:
        is_valid, error_msg, sanitized_cat = validate_category(category)
        if not is_valid:
            return False, error_msg, {}
        sanitized_data['category'] = sanitized_cat

    return True, None, sanitized_data


# Rate limiting (simple in-memory implementation)
_rate_limit_cache = {}
_rate_limit_window = 60  # 60 seconds
_rate_limit_max_requests = 10  # 10 requests per minute


def check_rate_limit(identifier: str, max_requests: int = _rate_limit_max_requests, window: int = _rate_limit_window) -> Tuple[bool, Optional[str]]:
    """
    Check if request is within rate limit

    Args:
        identifier: Unique identifier for rate limiting (e.g., IP address, user ID)
        max_requests: Maximum requests allowed in window
        window: Time window in seconds

    Returns:
        Tuple of (is_allowed, error_message)
    """
    now = datetime.now()

    # Clean old entries
    cutoff = now - timedelta(seconds=window)
    _rate_limit_cache[identifier] = [
        timestamp for timestamp in _rate_limit_cache.get(identifier, [])
        if timestamp > cutoff
    ]

    # Check limit
    request_count = len(_rate_limit_cache.get(identifier, []))
    if request_count >= max_requests:
        return False, f"Rate limit exceeded. Maximum {max_requests} requests per {window} seconds"

    # Add current request
    if identifier not in _rate_limit_cache:
        _rate_limit_cache[identifier] = []
    _rate_limit_cache[identifier].append(now)

    return True, None


def validate_integer_id(value: any, field_name: str = "id") -> Tuple[bool, Optional[str], Optional[int]]:
    """
    Validate integer ID (e.g., partner_id)

    Args:
        value: Value to validate
        field_name: Name of the field (for error messages)

    Returns:
        Tuple of (is_valid, error_message, validated_id)
    """
    if value is None:
        return True, None, None

    try:
        int_value = int(value)

        if int_value < 1:
            return False, f"{field_name} must be a positive integer", None

        if int_value > 2147483647:  # Max 32-bit integer
            return False, f"{field_name} is too large", None

        return True, None, int_value

    except (ValueError, TypeError):
        return False, f"{field_name} must be an integer", None

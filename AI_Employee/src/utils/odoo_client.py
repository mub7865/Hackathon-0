"""
Odoo JSON-RPC Client
Provides interface to Odoo Community Edition via JSON-RPC 2.0 protocol
"""

import os
import json
import logging
import requests
from typing import Any, Dict, List, Optional
from pathlib import Path
import yaml

from src.utils.retry_handler import with_retry
from src.utils.error_utils import ErrorType

logger = logging.getLogger(__name__)


class OdooError(Exception):
    """Base exception for Odoo-related errors"""
    pass


class OdooAuthenticationError(OdooError):
    """Authentication failed"""
    pass


class OdooValidationError(OdooError):
    """Validation error (missing fields, invalid data)"""
    pass


class OdooNotFoundError(OdooError):
    """Record not found"""
    pass


class OdooClient:
    """
    Odoo JSON-RPC 2.0 client

    Handles authentication and method execution for Odoo Community Edition
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize Odoo client

        Args:
            config_path: Path to odoo_config.yaml (default: config/odoo_config.yaml)
        """
        # Load configuration
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "odoo_config.yaml"

        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        # Load connection settings from environment
        self.url = os.getenv('ODOO_URL', 'http://localhost:8069')
        self.database = os.getenv('ODOO_DB', 'odoo')
        self.username = os.getenv('ODOO_USERNAME', 'admin')
        self.password = os.getenv('ODOO_PASSWORD', 'admin')

        # Ensure URL ends with /jsonrpc
        if not self.url.endswith('/jsonrpc'):
            self.url = f"{self.url.rstrip('/')}/jsonrpc"

        # Session state
        self.uid: Optional[int] = None
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json'
        })

        # Request counter for rate limiting
        self._request_count = 0
        self._request_window_start = None

        logger.info(f"Initialized Odoo client for {self.url}")

    @with_retry(
        max_attempts=3,
        base_delay=1.0,
        component="odoo_client",
        operation="authenticate"
    )
    def authenticate(self) -> int:
        """
        Authenticate with Odoo and get user ID

        Returns:
            User ID (uid)

        Raises:
            OdooAuthenticationError: If authentication fails
        """
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "service": "common",
                "method": "authenticate",
                "args": [self.database, self.username, self.password, {}]
            },
            "id": 1
        }

        try:
            response = self.session.post(self.url, json=payload, timeout=30)
            response.raise_for_status()

            data = response.json()

            # Check for error response
            if 'error' in data:
                error = data['error']
                error_msg = error.get('data', {}).get('message', error.get('message', 'Unknown error'))
                logger.error(f"Authentication failed: {error_msg}")
                raise OdooAuthenticationError(f"Authentication failed: {error_msg}")

            # Get uid from result
            self.uid = data.get('result')

            if not self.uid or self.uid is False:
                raise OdooAuthenticationError("Authentication failed: Invalid credentials")

            logger.info(f"Successfully authenticated as user {self.uid}")
            return self.uid

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error during authentication: {e}")
            raise OdooAuthenticationError(f"Network error: {e}") from e

    def _check_rate_limit(self) -> None:
        """Check and enforce rate limits"""
        import time

        max_rpm = self.config.get('max_requests_per_minute', 100)
        current_time = time.time()

        # Reset counter if window expired (60 seconds)
        if self._request_window_start is None or (current_time - self._request_window_start) >= 60:
            self._request_count = 0
            self._request_window_start = current_time

        # Check if rate limit exceeded
        if self._request_count >= max_rpm:
            wait_time = 60 - (current_time - self._request_window_start)
            if wait_time > 0:
                logger.warning(f"Rate limit reached, waiting {wait_time:.1f}s")
                time.sleep(wait_time)
                self._request_count = 0
                self._request_window_start = time.time()

        self._request_count += 1

    @with_retry(
        max_attempts=3,
        base_delay=1.0,
        component="odoo_client",
        operation="call"
    )
    def call(
        self,
        model: str,
        method: str,
        args: List[Any],
        kwargs: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Execute Odoo method via JSON-RPC

        Args:
            model: Odoo model name (e.g., 'account.move', 'res.partner')
            method: Method name (e.g., 'create', 'search_read', 'write')
            args: Positional arguments for the method
            kwargs: Keyword arguments for the method (optional)

        Returns:
            Method result

        Raises:
            OdooAuthenticationError: If not authenticated
            OdooValidationError: If validation fails
            OdooNotFoundError: If record not found
            OdooError: For other Odoo errors
        """
        # Ensure authenticated
        if self.uid is None:
            logger.info("Not authenticated, authenticating now...")
            self.authenticate()

        # Check rate limit
        self._check_rate_limit()

        # Build request payload
        call_args = [self.database, self.uid, self.password, model, method, args]
        if kwargs:
            call_args.append(kwargs)

        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "service": "object",
                "method": "execute_kw",
                "args": call_args
            },
            "id": self._request_count
        }

        try:
            response = self.session.post(self.url, json=payload, timeout=60)
            response.raise_for_status()

            data = response.json()

            # Check for error response
            if 'error' in data:
                error = data['error']
                error_code = error.get('code', 0)
                error_data = error.get('data', {})
                error_name = error_data.get('name', '')
                error_msg = error_data.get('message', error.get('message', 'Unknown error'))

                logger.error(f"Odoo error {error_code}: {error_msg}")

                # Classify error and raise appropriate exception
                if error_code == 100 or 'AccessDenied' in error_name:
                    raise OdooAuthenticationError(f"Access denied: {error_msg}")
                elif error_code == 200 or 'MissingError' in error_name or 'required' in error_msg.lower():
                    raise OdooValidationError(f"Validation error: {error_msg}")
                elif error_code == 300 or 'not found' in error_msg.lower():
                    raise OdooNotFoundError(f"Record not found: {error_msg}")
                else:
                    raise OdooError(f"Odoo error {error_code}: {error_msg}")

            # Return result
            result = data.get('result')
            logger.debug(f"Successfully called {model}.{method}")
            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error during {model}.{method}: {e}")
            raise OdooError(f"Network error: {e}") from e

    def create(self, model: str, values: Dict[str, Any]) -> int:
        """
        Create a record

        Args:
            model: Odoo model name
            values: Field values for the new record

        Returns:
            Created record ID
        """
        return self.call(model, 'create', [values])

    def write(self, model: str, record_ids: List[int], values: Dict[str, Any]) -> bool:
        """
        Update records

        Args:
            model: Odoo model name
            record_ids: List of record IDs to update
            values: Field values to update

        Returns:
            True if successful
        """
        return self.call(model, 'write', [record_ids, values])

    def search(self, model: str, domain: List[Any], limit: Optional[int] = None) -> List[int]:
        """
        Search for record IDs

        Args:
            model: Odoo model name
            domain: Search domain (Odoo domain syntax)
            limit: Maximum number of results

        Returns:
            List of record IDs
        """
        kwargs = {}
        if limit:
            kwargs['limit'] = limit

        return self.call(model, 'search', [domain], kwargs)

    def read(self, model: str, record_ids: List[int], fields: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Read record data

        Args:
            model: Odoo model name
            record_ids: List of record IDs to read
            fields: List of field names to read (None = all fields)

        Returns:
            List of record dictionaries
        """
        kwargs = {}
        if fields:
            kwargs['fields'] = fields

        return self.call(model, 'read', [record_ids], kwargs)

    def search_read(
        self,
        model: str,
        domain: List[Any],
        fields: Optional[List[str]] = None,
        limit: Optional[int] = None,
        order: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search and read records in one call

        Args:
            model: Odoo model name
            domain: Search domain
            fields: List of field names to read
            limit: Maximum number of results
            order: Sort order (e.g., 'name asc', 'date desc')

        Returns:
            List of record dictionaries
        """
        kwargs = {}
        if fields:
            kwargs['fields'] = fields
        if limit:
            kwargs['limit'] = limit
        if order:
            kwargs['order'] = order

        return self.call(model, 'search_read', [domain], kwargs)

    def unlink(self, model: str, record_ids: List[int]) -> bool:
        """
        Delete records

        Args:
            model: Odoo model name
            record_ids: List of record IDs to delete

        Returns:
            True if successful
        """
        return self.call(model, 'unlink', [record_ids])

    def get_model_fields(self, model: str) -> Dict[str, Any]:
        """
        Get field definitions for a model

        Args:
            model: Odoo model name

        Returns:
            Dictionary of field definitions
        """
        return self.call(model, 'fields_get', [])

    def close(self) -> None:
        """Close the session"""
        self.session.close()
        logger.info("Odoo client session closed")

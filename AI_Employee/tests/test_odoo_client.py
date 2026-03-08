"""
Unit tests for Odoo JSON-RPC Client
Tests authentication, method calls, error handling, and rate limiting
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
from datetime import datetime

from src.utils.odoo_client import (
    OdooClient,
    OdooError,
    OdooAuthenticationError,
    OdooValidationError,
    OdooNotFoundError
)


class TestOdooClient(unittest.TestCase):
    """Test cases for OdooClient"""

    def setUp(self):
        """Set up test fixtures"""
        # Mock environment variables
        self.env_patcher = patch.dict('os.environ', {
            'ODOO_URL': 'http://localhost:8069',
            'ODOO_DB': 'test_db',
            'ODOO_USERNAME': 'admin',
            'ODOO_PASSWORD': 'admin'
        })
        self.env_patcher.start()

        # Create client with mocked config
        with patch('builtins.open', unittest.mock.mock_open(read_data='approval_threshold: 100.00\nmax_requests_per_minute: 100')):
            with patch('yaml.safe_load', return_value={'approval_threshold': 100.00, 'max_requests_per_minute': 100}):
                self.client = OdooClient()

    def tearDown(self):
        """Clean up after tests"""
        self.env_patcher.stop()

    @patch('requests.Session.post')
    def test_authenticate_success(self, mock_post):
        """Test successful authentication"""
        # Mock successful authentication response
        mock_response = Mock()
        mock_response.json.return_value = {
            'jsonrpc': '2.0',
            'result': 2,
            'id': 1
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        # Authenticate
        uid = self.client.authenticate()

        # Verify
        self.assertEqual(uid, 2)
        self.assertEqual(self.client.uid, 2)
        mock_post.assert_called_once()

    @patch('requests.Session.post')
    def test_authenticate_failure(self, mock_post):
        """Test authentication failure"""
        # Mock authentication error response
        mock_response = Mock()
        mock_response.json.return_value = {
            'jsonrpc': '2.0',
            'error': {
                'code': 100,
                'message': 'Access Denied',
                'data': {
                    'name': 'odoo.exceptions.AccessDenied',
                    'message': 'Invalid credentials'
                }
            },
            'id': 1
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        # Verify authentication raises error
        with self.assertRaises(OdooAuthenticationError) as context:
            self.client.authenticate()

        self.assertIn('Invalid credentials', str(context.exception))

    @patch('requests.Session.post')
    def test_authenticate_network_error(self, mock_post):
        """Test authentication with network error"""
        # Mock network error
        import requests
        mock_post.side_effect = requests.exceptions.ConnectionError('Connection refused')

        # Verify authentication raises error
        with self.assertRaises(OdooAuthenticationError) as context:
            self.client.authenticate()

        self.assertIn('Network error', str(context.exception))

    @patch('requests.Session.post')
    def test_call_success(self, mock_post):
        """Test successful method call"""
        # Set uid (authenticated)
        self.client.uid = 2

        # Mock successful call response
        mock_response = Mock()
        mock_response.json.return_value = {
            'jsonrpc': '2.0',
            'result': 42,
            'id': 1
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        # Call method
        result = self.client.call('account.move', 'create', [{'partner_id': 7}])

        # Verify
        self.assertEqual(result, 42)
        mock_post.assert_called_once()

    @patch('requests.Session.post')
    def test_call_authentication_error(self, mock_post):
        """Test method call with authentication error"""
        # Set uid (authenticated)
        self.client.uid = 2

        # Mock authentication error response
        mock_response = Mock()
        mock_response.json.return_value = {
            'jsonrpc': '2.0',
            'error': {
                'code': 100,
                'message': 'Access Denied',
                'data': {
                    'name': 'odoo.exceptions.AccessDenied',
                    'message': 'Session expired'
                }
            },
            'id': 1
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        # Verify call raises authentication error
        with self.assertRaises(OdooAuthenticationError) as context:
            self.client.call('account.move', 'create', [{}])

        self.assertIn('Session expired', str(context.exception))

    @patch('requests.Session.post')
    def test_call_validation_error(self, mock_post):
        """Test method call with validation error"""
        # Set uid (authenticated)
        self.client.uid = 2

        # Mock validation error response
        mock_response = Mock()
        mock_response.json.return_value = {
            'jsonrpc': '2.0',
            'error': {
                'code': 200,
                'message': 'Validation Error',
                'data': {
                    'name': 'odoo.exceptions.ValidationError',
                    'message': 'partner_id is required'
                }
            },
            'id': 1
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        # Verify call raises validation error
        with self.assertRaises(OdooValidationError) as context:
            self.client.call('account.move', 'create', [{}])

        self.assertIn('required', str(context.exception))

    @patch('requests.Session.post')
    def test_call_not_found_error(self, mock_post):
        """Test method call with not found error"""
        # Set uid (authenticated)
        self.client.uid = 2

        # Mock not found error response
        mock_response = Mock()
        mock_response.json.return_value = {
            'jsonrpc': '2.0',
            'error': {
                'code': 300,
                'message': 'Record not found',
                'data': {
                    'name': 'odoo.exceptions.MissingError',
                    'message': 'Record with ID 999 not found'
                }
            },
            'id': 1
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        # Verify call raises not found error
        with self.assertRaises(OdooNotFoundError) as context:
            self.client.call('account.move', 'read', [[999]])

        self.assertIn('not found', str(context.exception))

    @patch('requests.Session.post')
    def test_call_auto_authenticate(self, mock_post):
        """Test automatic authentication when uid is None"""
        # Mock authentication response
        auth_response = Mock()
        auth_response.json.return_value = {
            'jsonrpc': '2.0',
            'result': 2,
            'id': 1
        }
        auth_response.raise_for_status = Mock()

        # Mock call response
        call_response = Mock()
        call_response.json.return_value = {
            'jsonrpc': '2.0',
            'result': 42,
            'id': 2
        }
        call_response.raise_for_status = Mock()

        mock_post.side_effect = [auth_response, call_response]

        # Call method (should auto-authenticate)
        result = self.client.call('account.move', 'create', [{}])

        # Verify
        self.assertEqual(result, 42)
        self.assertEqual(self.client.uid, 2)
        self.assertEqual(mock_post.call_count, 2)

    @patch('requests.Session.post')
    def test_create_method(self, mock_post):
        """Test create convenience method"""
        # Set uid (authenticated)
        self.client.uid = 2

        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            'jsonrpc': '2.0',
            'result': 42,
            'id': 1
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        # Create record
        record_id = self.client.create('account.move', {'partner_id': 7})

        # Verify
        self.assertEqual(record_id, 42)

    @patch('requests.Session.post')
    def test_search_read_method(self, mock_post):
        """Test search_read convenience method"""
        # Set uid (authenticated)
        self.client.uid = 2

        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            'jsonrpc': '2.0',
            'result': [
                {'id': 1, 'name': 'Record 1'},
                {'id': 2, 'name': 'Record 2'}
            ],
            'id': 1
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        # Search and read
        results = self.client.search_read(
            'account.move',
            [['state', '=', 'posted']],
            fields=['name'],
            limit=10
        )

        # Verify
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['name'], 'Record 1')

    def test_rate_limiting(self):
        """Test rate limiting enforcement"""
        # Set uid (authenticated)
        self.client.uid = 2

        # Set low rate limit for testing
        self.client.config['max_requests_per_minute'] = 5

        # Mock successful responses
        with patch('requests.Session.post') as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = {
                'jsonrpc': '2.0',
                'result': True,
                'id': 1
            }
            mock_response.raise_for_status = Mock()
            mock_post.return_value = mock_response

            # Make 5 requests (should succeed)
            for i in range(5):
                self.client.call('account.move', 'search', [[]])

            # 6th request should trigger rate limit wait
            with patch('time.sleep') as mock_sleep:
                self.client.call('account.move', 'search', [[]])
                # Verify sleep was called (rate limit triggered)
                mock_sleep.assert_called()

    def test_close_session(self):
        """Test session cleanup"""
        with patch.object(self.client.session, 'close') as mock_close:
            self.client.close()
            mock_close.assert_called_once()


class TestOdooClientIntegration(unittest.TestCase):
    """Integration tests for OdooClient (requires running Odoo instance)"""

    @unittest.skip("Requires running Odoo instance")
    def test_full_workflow(self):
        """Test full authentication and CRUD workflow"""
        # This test requires a running Odoo instance
        # Uncomment and configure when testing against real Odoo

        client = OdooClient()

        # Authenticate
        uid = client.authenticate()
        self.assertIsNotNone(uid)

        # Create invoice
        invoice_id = client.create('account.move', {
            'partner_id': 1,
            'move_type': 'out_invoice',
            'invoice_date': datetime.now().strftime('%Y-%m-%d')
        })
        self.assertIsNotNone(invoice_id)

        # Read invoice
        invoices = client.read('account.move', [invoice_id], ['name', 'state'])
        self.assertEqual(len(invoices), 1)

        # Search invoices
        found = client.search('account.move', [['id', '=', invoice_id]])
        self.assertIn(invoice_id, found)

        # Clean up
        client.unlink('account.move', [invoice_id])
        client.close()


if __name__ == '__main__':
    unittest.main()

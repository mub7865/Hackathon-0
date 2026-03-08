#!/usr/bin/env python3
"""
Setup script for Odoo Community Edition
Creates test data: customers, vendors, products for Gold Tier testing
"""

import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from src.utils.odoo_client import OdooClient
except ImportError:
    print("ERROR: OdooClient not yet implemented. This script will work after Phase 3.")
    sys.exit(1)

def create_test_data():
    """Create test customers, vendors, and products in Odoo"""

    print("Connecting to Odoo...")
    client = OdooClient()

    print("\n=== Creating Test Customers ===")
    customers = [
        {"name": "Client A", "email": "clienta@example.com", "phone": "+1234567890"},
        {"name": "Client B", "email": "clientb@example.com", "phone": "+1234567891"},
        {"name": "Client C", "email": "clientc@example.com", "phone": "+1234567892"},
    ]

    for customer in customers:
        try:
            partner_id = client.call('res.partner', 'create', [customer])
            print(f"✓ Created customer: {customer['name']} (ID: {partner_id})")
        except Exception as e:
            print(f"✗ Failed to create {customer['name']}: {e}")

    print("\n=== Creating Test Vendors ===")
    vendors = [
        {"name": "Software Vendor", "email": "vendor@software.com", "supplier_rank": 1},
        {"name": "Office Supplies Co", "email": "sales@officesupplies.com", "supplier_rank": 1},
    ]

    for vendor in vendors:
        try:
            partner_id = client.call('res.partner', 'create', [vendor])
            print(f"✓ Created vendor: {vendor['name']} (ID: {partner_id})")
        except Exception as e:
            print(f"✗ Failed to create {vendor['name']}: {e}")

    print("\n=== Creating Test Products/Services ===")
    products = [
        {"name": "Consulting Services - Hourly", "type": "service", "list_price": 150.00},
        {"name": "Consulting Services - Project", "type": "service", "list_price": 5000.00},
        {"name": "Software Subscription", "type": "service", "list_price": 49.99},
        {"name": "Training Session", "type": "service", "list_price": 500.00},
        {"name": "Support Package", "type": "service", "list_price": 200.00},
    ]

    for product in products:
        try:
            product_id = client.call('product.product', 'create', [product])
            print(f"✓ Created product: {product['name']} (ID: {product_id})")
        except Exception as e:
            print(f"✗ Failed to create {product['name']}: {e}")

    print("\n=== Test Data Creation Complete ===")
    print("You can now create invoices, payments, and expenses using these test records.")

if __name__ == "__main__":
    load_dotenv()

    # Check environment variables
    required_vars = ['ODOO_URL', 'ODOO_DB', 'ODOO_USERNAME', 'ODOO_PASSWORD']
    missing = [var for var in required_vars if not os.getenv(var)]

    if missing:
        print(f"ERROR: Missing environment variables: {', '.join(missing)}")
        print("Please configure these in silver/.env")
        sys.exit(1)

    try:
        create_test_data()
    except Exception as e:
        print(f"\nERROR: {e}")
        print("\nMake sure Odoo is running and accessible at:", os.getenv('ODOO_URL'))
        sys.exit(1)

"""
Business Transaction entity
Represents financial activity (invoice, payment, expense) in Odoo
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class TransactionType(Enum):
    """Transaction type enumeration"""
    INVOICE = "invoice"
    PAYMENT = "payment"
    EXPENSE = "expense"


class TransactionStatus(Enum):
    """Transaction status enumeration"""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    POSTED = "posted"
    PAID = "paid"
    CANCELLED = "cancelled"


@dataclass
class BusinessTransaction:
    """
    Represents financial activity (invoice, payment, expense)
    Maps to Odoo account.move and account.payment models
    """
    transaction_id: Optional[str] = None  # Odoo record ID
    transaction_type: TransactionType = TransactionType.INVOICE
    amount: float = 0.0
    currency: str = "USD"
    date: datetime = field(default_factory=datetime.now)
    party: str = ""  # Customer/vendor name
    party_id: Optional[str] = None  # Odoo partner ID
    category: str = ""  # Expense category or revenue source
    description: str = ""
    status: TransactionStatus = TransactionStatus.DRAFT
    approval_threshold: float = 100.00  # From clarifications
    requires_approval: bool = False
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    odoo_url: Optional[str] = None
    audit_trail: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self):
        """Calculate requires_approval based on amount"""
        self.requires_approval = self.amount > self.approval_threshold

    def add_audit_entry(self, action: str, user: str, details: str = "") -> None:
        """Add entry to audit trail"""
        self.audit_trail.append({
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'user': user,
            'details': details,
            'status': self.status.value
        })

    def approve(self, approved_by: str) -> None:
        """Approve transaction"""
        self.status = TransactionStatus.APPROVED
        self.approved_by = approved_by
        self.approved_at = datetime.now()
        self.add_audit_entry('approved', approved_by)

    def post_to_odoo(self, odoo_id: str, odoo_url: str) -> None:
        """Mark as posted to Odoo"""
        self.transaction_id = odoo_id
        self.odoo_url = odoo_url
        self.status = TransactionStatus.POSTED
        self.add_audit_entry('posted', 'system', f'Posted to Odoo: {odoo_id}')

    def mark_paid(self) -> None:
        """Mark transaction as paid"""
        self.status = TransactionStatus.PAID
        self.add_audit_entry('paid', 'system')

    def cancel(self, reason: str) -> None:
        """Cancel transaction"""
        self.status = TransactionStatus.CANCELLED
        self.add_audit_entry('cancelled', 'system', reason)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'transaction_id': self.transaction_id,
            'transaction_type': self.transaction_type.value,
            'amount': self.amount,
            'currency': self.currency,
            'date': self.date.isoformat(),
            'party': self.party,
            'party_id': self.party_id,
            'category': self.category,
            'description': self.description,
            'status': self.status.value,
            'approval_threshold': self.approval_threshold,
            'requires_approval': self.requires_approval,
            'approved_by': self.approved_by,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'odoo_url': self.odoo_url,
            'audit_trail': self.audit_trail
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BusinessTransaction':
        """Create from dictionary"""
        return cls(
            transaction_id=data.get('transaction_id'),
            transaction_type=TransactionType(data['transaction_type']),
            amount=data['amount'],
            currency=data.get('currency', 'USD'),
            date=datetime.fromisoformat(data['date']),
            party=data['party'],
            party_id=data.get('party_id'),
            category=data.get('category', ''),
            description=data.get('description', ''),
            status=TransactionStatus(data.get('status', 'draft')),
            approval_threshold=data.get('approval_threshold', 100.00),
            requires_approval=data.get('requires_approval', False),
            approved_by=data.get('approved_by'),
            approved_at=datetime.fromisoformat(data['approved_at']) if data.get('approved_at') else None,
            odoo_url=data.get('odoo_url'),
            audit_trail=data.get('audit_trail', [])
        )

    @classmethod
    def from_task_file(cls, frontmatter: Dict[str, Any], body: str) -> 'BusinessTransaction':
        """
        Create BusinessTransaction from task file

        Args:
            frontmatter: YAML frontmatter from task file
            body: Task file body content

        Returns:
            BusinessTransaction instance
        """
        import re

        # Parse transaction details from frontmatter and body
        transaction_type = TransactionType(frontmatter.get('action', 'invoice'))
        amount = float(frontmatter.get('amount', 0.0))
        party = frontmatter.get('party', frontmatter.get('client', 'Unknown'))
        party_id = frontmatter.get('party_id', frontmatter.get('client_id'))
        category = frontmatter.get('category', '')
        description = frontmatter.get('description', '')

        # Parse from body if not in frontmatter
        for line in body.split('\n'):
            line_stripped = line.strip()

            # Extract amount: "- Amount: $50" or "Amount: $50"
            if amount == 0.0:
                amount_match = re.search(r'[-*]?\s*Amount:\s*\$?(\d+(?:\.\d+)?)', line_stripped, re.IGNORECASE)
                if amount_match:
                    amount = float(amount_match.group(1))

            # Extract party/client: "Create an invoice for Test Client A:" or "- Client: Test Client A"
            if party == 'Unknown':
                # Pattern 1: "for [Client Name]:"
                party_match = re.search(r'for\s+([^:]+):', line_stripped)
                if party_match:
                    party = party_match.group(1).strip()
                # Pattern 2: "- Client: [Client Name]" or "Client: [Client Name]"
                else:
                    client_match = re.search(r'[-*]?\s*(?:Client|Party|Customer):\s*(.+)', line_stripped, re.IGNORECASE)
                    if client_match:
                        party = client_match.group(1).strip()

            # Extract description: "- Description: Website maintenance"
            if not description:
                desc_match = re.search(r'[-*]?\s*Description:\s*(.+)', line_stripped, re.IGNORECASE)
                if desc_match:
                    description = desc_match.group(1).strip()

        return cls(
            transaction_type=transaction_type,
            amount=amount,
            party=party,
            party_id=party_id,
            category=category,
            description=description,
            date=datetime.now()
        )


def validate_transaction(transaction: BusinessTransaction) -> tuple[bool, Optional[str]]:
    """
    Validate transaction data with security checks

    Args:
        transaction: BusinessTransaction to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    from src.utils.security_utils import (
        validate_amount,
        validate_party_name,
        validate_description,
        validate_category
    )

    # Validate amount
    is_valid, error_msg = validate_amount(transaction.amount)
    if not is_valid:
        return False, error_msg

    # Validate party name
    is_valid, error_msg, _ = validate_party_name(transaction.party)
    if not is_valid:
        return False, error_msg

    # Validate description
    is_valid, error_msg, _ = validate_description(transaction.description)
    if not is_valid:
        return False, error_msg

    # Validate category for expenses
    if transaction.transaction_type == TransactionType.EXPENSE:
        if not transaction.category:
            return False, "Category is required for expenses"

        is_valid, error_msg, _ = validate_category(transaction.category)
        if not is_valid:
            return False, error_msg

    return True, None

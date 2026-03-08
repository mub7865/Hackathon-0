"""
Task Classification and Processing
Determines if tasks are safe or sensitive based on Company Handbook rules
"""

from dataclasses import dataclass
from typing import List, Dict, Any
import re
import logging


@dataclass
class Classification:
    """
    Task classification result.
    Determines if task requires approval.
    """
    is_sensitive: bool
    reasons: List[str]
    confidence: float  # 0.0 to 1.0


class TaskProcessor:
    """Classifies tasks as safe or sensitive"""

    def __init__(self, handbook_rules: Dict[str, Any]):
        """
        Initialize task processor.

        Args:
            handbook_rules: Parsed Company Handbook rules
        """
        self.handbook_rules = handbook_rules
        self.logger = logging.getLogger(__name__)

        # Default sensitive keywords
        self.sensitive_keywords = [
            'send email',
            'post to linkedin',
            'share on linkedin',
            'payment',
            'transfer',
            'delete',
            'external api',
            'api call'
        ]

    def classify_task(self, task_content: str, task_metadata: Dict[str, Any]) -> Classification:
        """
        Classify task as safe or sensitive.

        Args:
            task_content: Task content (markdown body)
            task_metadata: Task YAML frontmatter

        Returns:
            Classification result
        """
        reasons = []
        is_sensitive = False

        # Check 1: Amount-based classification
        amount = task_metadata.get('amount')
        if amount and amount > 500:
            reasons.append(f"Amount ${amount} exceeds $500 threshold")
            is_sensitive = True

        # Check 2: Email send action
        content_lower = task_content.lower()
        if any(keyword in content_lower for keyword in ['send email', 'reply to', 'email to']):
            reasons.append("Contains email send action")
            is_sensitive = True

        # Check 3: LinkedIn post action
        if any(keyword in content_lower for keyword in ['post to linkedin', 'share on linkedin', 'linkedin post']):
            reasons.append("Contains LinkedIn post action")
            is_sensitive = True

        # Check 4: External API calls
        if any(keyword in content_lower for keyword in ['external api', 'api call', 'webhook']):
            reasons.append("Contains external API call")
            is_sensitive = True

        # Check 5: User-defined sensitive keywords from handbook
        for keyword in self.sensitive_keywords:
            if keyword.lower() in content_lower:
                reasons.append(f"Contains sensitive keyword: {keyword}")
                is_sensitive = True
                break

        # Confidence is 1.0 for rule-based classification
        confidence = 1.0 if is_sensitive else 1.0

        return Classification(
            is_sensitive=is_sensitive,
            reasons=reasons,
            confidence=confidence
        )

    def extract_amount(self, text: str) -> float:
        """
        Extract financial amount from text.

        Args:
            text: Text to search

        Returns:
            Extracted amount or 0.0 if not found
        """
        # Pattern: $123, $1,234, $1234.56
        pattern = r'\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
        matches = re.findall(pattern, text)

        if matches:
            # Remove commas and convert to float
            amount_str = matches[0].replace(',', '')
            return float(amount_str)

        return 0.0

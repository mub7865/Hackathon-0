"""
Handbook Model

Manages the Company_Handbook.md file with user-defined processing rules.
"""

import os
import re
from typing import Dict, List, Any


class Handbook:
    """Model for Company_Handbook.md file."""

    def __init__(self, vault_path: str):
        """
        Initialize Handbook.

        Args:
            vault_path: Path to vault root
        """
        self.vault_path = vault_path
        self.handbook_path = os.path.join(vault_path, "Company_Handbook.md")
        self.rules = {
            'summarization': [],
            'tone_style': [],
            'special_instructions': [],
            'custom_flags': [],
            'preferences': {}
        }

    def read(self) -> Dict[str, Any]:
        """
        Read and parse handbook rules.

        Returns:
            Dictionary of parsed rules
        """
        if not os.path.exists(self.handbook_path):
            return self._get_default_rules()

        with open(self.handbook_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse sections
        self.rules['summarization'] = self._extract_section(content, '### Summarization')
        self.rules['tone_style'] = self._extract_section(content, '### Tone & Style')
        self.rules['special_instructions'] = self._extract_section(content, '### Special Instructions')
        self.rules['custom_flags'] = self._extract_section(content, '## Custom Flags')
        self.rules['preferences'] = self._extract_preferences(content)

        return self.rules

    def _extract_section(self, content: str, section_header: str) -> List[str]:
        """
        Extract bullet points from a section.

        Args:
            content: Full handbook content
            section_header: Section header to find

        Returns:
            List of rules/items in that section
        """
        # Find section
        pattern = f"{re.escape(section_header)}(.*?)(?=###|##|$)"
        match = re.search(pattern, content, re.DOTALL)

        if not match:
            return []

        section_content = match.group(1)

        # Extract bullet points
        rules = []
        for line in section_content.split('\n'):
            line = line.strip()
            if line.startswith('- '):
                rules.append(line[2:])  # Remove "- " prefix

        return rules

    def _extract_preferences(self, content: str) -> Dict[str, str]:
        """
        Extract preferences from Preferences section.

        Args:
            content: Full handbook content

        Returns:
            Dictionary of preferences
        """
        preferences = {}

        pattern = r"## Preferences(.*?)(?=##|$)"
        match = re.search(pattern, content, re.DOTALL)

        if not match:
            return preferences

        pref_content = match.group(1)

        # Extract key-value pairs
        for line in pref_content.split('\n'):
            line = line.strip()
            if line.startswith('- **') and '**:' in line:
                # Format: - **Key**: Value
                key_match = re.match(r'- \*\*(.+?)\*\*:\s*(.+)', line)
                if key_match:
                    key = key_match.group(1).lower().replace(' ', '_')
                    value = key_match.group(2)
                    preferences[key] = value

        return preferences

    def _get_default_rules(self) -> Dict[str, Any]:
        """
        Get default rules if handbook doesn't exist.

        Returns:
            Dictionary of default rules
        """
        return {
            'summarization': [
                'Use 3 bullet points for summaries',
                'Keep summaries under 200 words',
                'Extract action items as checkboxes'
            ],
            'tone_style': [
                'Professional and courteous',
                'Concise and clear',
                'Action-oriented'
            ],
            'special_instructions': [],
            'custom_flags': [
                'Amount > $1000 → 💰 High-value'
            ],
            'preferences': {
                'summary_length': '150-200 words',
                'action_item_format': 'Checkboxes',
                'date_format': 'ISO 8601',
                'time_zone': 'UTC'
            }
        }

    def get_processing_context(self) -> str:
        """
        Get formatted processing context for AI prompt.

        Returns:
            Formatted string with all rules
        """
        rules = self.read()

        context = "# Processing Rules\n\n"

        if rules['summarization']:
            context += "## Summarization:\n"
            for rule in rules['summarization']:
                context += f"- {rule}\n"
            context += "\n"

        if rules['tone_style']:
            context += "## Tone & Style:\n"
            for rule in rules['tone_style']:
                context += f"- {rule}\n"
            context += "\n"

        if rules['special_instructions']:
            context += "## Special Instructions:\n"
            for rule in rules['special_instructions']:
                context += f"- {rule}\n"
            context += "\n"

        if rules['custom_flags']:
            context += "## Custom Flags:\n"
            for flag in rules['custom_flags']:
                context += f"- {flag}\n"
            context += "\n"

        if rules['preferences']:
            context += "## Preferences:\n"
            for key, value in rules['preferences'].items():
                context += f"- {key.replace('_', ' ').title()}: {value}\n"

        return context

    def parse_custom_flags(self) -> List[Dict[str, str]]:
        """
        Parse custom flags into structured format.

        Returns:
            List of flag dictionaries with condition and flag
        """
        flags = []
        custom_flags = self.rules.get('custom_flags', [])

        for flag_rule in custom_flags:
            if '→' in flag_rule:
                parts = flag_rule.split('→')
                if len(parts) == 2:
                    flags.append({
                        'condition': parts[0].strip(),
                        'flag': parts[1].strip()
                    })

        return flags

    def apply_custom_flags(self, content: str) -> List[str]:
        """
        Detect and apply custom flags based on content.

        Args:
            content: Original content to analyze

        Returns:
            List of flags that apply to this content
        """
        applied_flags = []
        flags = self.parse_custom_flags()

        for flag_def in flags:
            condition = flag_def['condition']
            flag = flag_def['flag']

            # Parse condition (e.g., "Amount > $500")
            if self._check_condition(condition, content):
                applied_flags.append(flag)

        return applied_flags

    def _check_condition(self, condition: str, content: str) -> bool:
        """
        Check if a condition matches the content.

        Args:
            condition: Condition string (e.g., "Amount > $500")
            content: Content to check

        Returns:
            True if condition matches
        """
        # Handle amount conditions (e.g., "Amount > $500")
        if 'Amount' in condition or '$' in condition:
            return self._check_amount_condition(condition, content)

        # Handle keyword conditions (e.g., "Contains 'urgent'")
        if 'Contains' in condition or 'contains' in condition:
            keyword = condition.split("'")[1] if "'" in condition else ""
            return keyword.lower() in content.lower()

        # Handle date conditions (e.g., "Due date < 7 days")
        if 'Due date' in condition or 'due date' in condition:
            return self._check_date_condition(condition, content)

        return False

    def _check_amount_condition(self, condition: str, content: str) -> bool:
        """
        Check if amount condition matches content.

        Args:
            condition: Amount condition (e.g., "Amount > $500")
            content: Content to check

        Returns:
            True if condition matches
        """
        import re

        # Extract threshold from condition
        threshold_match = re.search(r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)', condition)
        if not threshold_match:
            return False

        threshold = float(threshold_match.group(1).replace(',', ''))

        # Find all amounts in content
        amount_pattern = r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)'
        amounts = re.findall(amount_pattern, content)

        if not amounts:
            return False

        # Check if any amount meets condition
        for amount_str in amounts:
            amount = float(amount_str.replace(',', ''))

            if '>' in condition:
                if amount > threshold:
                    return True
            elif '<' in condition:
                if amount < threshold:
                    return True
            elif '=' in condition or '==' in condition:
                if amount == threshold:
                    return True

        return False

    def _check_date_condition(self, condition: str, content: str) -> bool:
        """
        Check if date condition matches content.

        Args:
            condition: Date condition (e.g., "Due date < 7 days")
            content: Content to check

        Returns:
            True if condition matches
        """
        import re
        from datetime import datetime, timedelta

        # Extract days threshold
        days_match = re.search(r'(\d+)\s*days?', condition)
        if not days_match:
            return False

        threshold_days = int(days_match.group(1))

        # Look for date patterns in content
        date_patterns = [
            r'(\d{4}-\d{2}-\d{2})',  # ISO format
            r'(\d{1,2}/\d{1,2}/\d{4})',  # MM/DD/YYYY
            r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}'
        ]

        for pattern in date_patterns:
            dates = re.findall(pattern, content, re.IGNORECASE)
            if dates:
                # Found dates - check if within threshold
                # This is a simplified check
                return True

        return False

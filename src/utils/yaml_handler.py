"""
YAML Frontmatter Parser Utility

Handles reading and writing YAML frontmatter in markdown files.
"""

import yaml
import re
from typing import Dict, Tuple, Any


def parse_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """
    Extract YAML frontmatter and markdown content from a file.

    Args:
        content: Full file content with frontmatter

    Returns:
        Tuple of (metadata_dict, markdown_content)
    """
    # Match frontmatter pattern: --- ... ---
    pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
    match = re.match(pattern, content, re.DOTALL)

    if not match:
        return {}, content

    yaml_content = match.group(1)
    markdown_content = match.group(2)

    try:
        metadata = yaml.safe_load(yaml_content)
        return metadata or {}, markdown_content
    except yaml.YAMLError as e:
        print(f"YAML parsing error: {e}")
        return {}, content


def write_frontmatter(metadata: Dict[str, Any], markdown_content: str) -> str:
    """
    Combine metadata and markdown into single file content.

    Args:
        metadata: Dictionary of frontmatter fields
        markdown_content: Markdown body content

    Returns:
        Complete file content with frontmatter
    """
    yaml_content = yaml.dump(metadata, default_flow_style=False, sort_keys=False)
    return f"---\n{yaml_content}---\n\n{markdown_content}"


def update_frontmatter_field(content: str, field: str, value: Any) -> str:
    """
    Update a single field in frontmatter without rewriting entire file.

    Args:
        content: Full file content
        field: Field name to update
        value: New value for field

    Returns:
        Updated file content
    """
    metadata, markdown = parse_frontmatter(content)
    metadata[field] = value
    return write_frontmatter(metadata, markdown)

"""
File utilities for task file management
Implements YAML frontmatter read/write for task state persistence
"""

import os
import re
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import yaml
from datetime import datetime


class TaskFileError(Exception):
    """Custom exception for task file operations"""
    pass


def parse_task_file(file_path: str) -> Tuple[Dict[str, Any], str]:
    """
    Parse a task file with YAML frontmatter

    Args:
        file_path: Path to the task file

    Returns:
        Tuple of (frontmatter_dict, content_body)

    Raises:
        TaskFileError: If file cannot be parsed
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        raise TaskFileError(f"Failed to read file {file_path}: {e}")

    # Match YAML frontmatter between --- delimiters
    pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
    match = re.match(pattern, content, re.DOTALL)

    if not match:
        raise TaskFileError(f"No valid YAML frontmatter found in {file_path}")

    frontmatter_str = match.group(1)
    body = match.group(2)

    try:
        frontmatter = yaml.safe_load(frontmatter_str)
        if frontmatter is None:
            frontmatter = {}
    except yaml.YAMLError as e:
        raise TaskFileError(f"Invalid YAML in frontmatter: {e}")

    return frontmatter, body


def write_task_file(file_path: str, frontmatter: Dict[str, Any], body: str) -> None:
    """
    Write a task file with YAML frontmatter

    Args:
        file_path: Path to the task file
        frontmatter: Dictionary of frontmatter fields
        body: Content body (markdown)

    Raises:
        TaskFileError: If file cannot be written
    """
    try:
        # Ensure datetime objects are converted to ISO format strings
        frontmatter_clean = _clean_frontmatter_for_yaml(frontmatter)

        # Generate YAML frontmatter
        frontmatter_str = yaml.dump(frontmatter_clean, default_flow_style=False, sort_keys=False)

        # Combine frontmatter and body
        content = f"---\n{frontmatter_str}---\n\n{body}"

        # Write to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

    except Exception as e:
        raise TaskFileError(f"Failed to write file {file_path}: {e}")


def update_task_frontmatter(file_path: str, updates: Dict[str, Any]) -> None:
    """
    Update specific fields in task file frontmatter

    Args:
        file_path: Path to the task file
        updates: Dictionary of fields to update

    Raises:
        TaskFileError: If file cannot be updated
    """
    frontmatter, body = parse_task_file(file_path)
    frontmatter.update(updates)
    write_task_file(file_path, frontmatter, body)


def increment_task_iteration(file_path: str) -> int:
    """
    Increment the current_iteration field in task file

    Args:
        file_path: Path to the task file

    Returns:
        New iteration count

    Raises:
        TaskFileError: If file cannot be updated
    """
    frontmatter, body = parse_task_file(file_path)

    current = frontmatter.get('current_iteration', 0)
    new_iteration = current + 1

    frontmatter['current_iteration'] = new_iteration
    write_task_file(file_path, frontmatter, body)

    return new_iteration


def mark_task_stuck(file_path: str, reason: str) -> None:
    """
    Mark a task as stuck (max iterations reached)

    Args:
        file_path: Path to the task file
        reason: Reason for stuck status

    Raises:
        TaskFileError: If file cannot be updated
    """
    updates = {
        'status': 'stuck',
        'stuck_reason': reason,
        'stuck_at': datetime.now().isoformat()
    }
    update_task_frontmatter(file_path, updates)


def move_task_file(source_path: str, destination_folder: str) -> str:
    """
    Move a task file to a different folder (workflow state transition)

    Args:
        source_path: Current file path
        destination_folder: Target folder (e.g., 'Pending_Approval', 'Done')

    Returns:
        New file path

    Raises:
        TaskFileError: If file cannot be moved
    """
    try:
        source = Path(source_path)

        # Determine vault root (parent of Needs_Action, Done, etc.)
        vault_root = source.parent.parent

        # Construct destination path
        dest_folder = vault_root / destination_folder
        dest_folder.mkdir(parents=True, exist_ok=True)

        dest_path = dest_folder / source.name

        # Move file
        source.rename(dest_path)

        return str(dest_path)

    except Exception as e:
        raise TaskFileError(f"Failed to move file from {source_path} to {destination_folder}: {e}")


def get_task_status(file_path: str) -> str:
    """
    Get the current status of a task

    Args:
        file_path: Path to the task file

    Returns:
        Task status string

    Raises:
        TaskFileError: If file cannot be read
    """
    frontmatter, _ = parse_task_file(file_path)
    return frontmatter.get('status', 'unknown')


def get_task_iteration_count(file_path: str) -> Tuple[int, int]:
    """
    Get current and max iteration counts

    Args:
        file_path: Path to the task file

    Returns:
        Tuple of (current_iteration, max_iterations)

    Raises:
        TaskFileError: If file cannot be read
    """
    frontmatter, _ = parse_task_file(file_path)
    current = frontmatter.get('current_iteration', 0)
    max_iter = frontmatter.get('max_iterations', 10)
    return current, max_iter


def create_task_file(
    folder: str,
    filename: str,
    task_type: str,
    priority: str,
    content: str,
    additional_frontmatter: Optional[Dict[str, Any]] = None
) -> str:
    """
    Create a new task file with frontmatter

    Args:
        folder: Folder to create file in (e.g., 'Needs_Action')
        filename: Name of the file
        task_type: Type of task (email, whatsapp, etc.)
        priority: Priority level (high, medium, low)
        content: Task content body
        additional_frontmatter: Additional frontmatter fields

    Returns:
        Path to created file

    Raises:
        TaskFileError: If file cannot be created
    """
    frontmatter = {
        'type': task_type,
        'priority': priority,
        'status': 'needs_action',
        'created': datetime.now().isoformat(),
        'current_iteration': 0,
        'max_iterations': 10
    }

    if additional_frontmatter:
        frontmatter.update(additional_frontmatter)

    # Ensure folder exists
    folder_path = Path(folder)
    folder_path.mkdir(parents=True, exist_ok=True)

    file_path = folder_path / filename
    write_task_file(str(file_path), frontmatter, content)

    return str(file_path)


def _clean_frontmatter_for_yaml(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean frontmatter data for YAML serialization
    Converts datetime objects to ISO format strings

    Args:
        data: Frontmatter dictionary

    Returns:
        Cleaned dictionary
    """
    cleaned = {}
    for key, value in data.items():
        if isinstance(value, datetime):
            cleaned[key] = value.isoformat()
        elif isinstance(value, dict):
            cleaned[key] = _clean_frontmatter_for_yaml(value)
        elif isinstance(value, list):
            cleaned[key] = [
                _clean_frontmatter_for_yaml(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            cleaned[key] = value
    return cleaned


def validate_task_file(file_path: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a task file has required frontmatter fields

    Args:
        file_path: Path to the task file

    Returns:
        Tuple of (is_valid, error_message)
    """
    required_fields = ['type', 'priority', 'status', 'created']

    try:
        frontmatter, _ = parse_task_file(file_path)

        missing = [field for field in required_fields if field not in frontmatter]

        if missing:
            return False, f"Missing required fields: {', '.join(missing)}"

        # Validate enum values
        valid_types = ['email', 'whatsapp', 'linkedin', 'accounting', 'social_media', 'general']
        if frontmatter['type'] not in valid_types:
            return False, f"Invalid type: {frontmatter['type']}"

        valid_priorities = ['high', 'medium', 'low']
        if frontmatter['priority'] not in valid_priorities:
            return False, f"Invalid priority: {frontmatter['priority']}"

        valid_statuses = ['needs_action', 'in_progress', 'pending_approval', 'approved', 'done', 'stuck']
        if frontmatter['status'] not in valid_statuses:
            return False, f"Invalid status: {frontmatter['status']}"

        return True, None

    except TaskFileError as e:
        return False, str(e)

"""
Dashboard Model

Manages the Dashboard.md file with task statistics and recent activity.
"""

import os
from datetime import datetime, timezone
from typing import List, Dict, Any
from collections import Counter


class Dashboard:
    """Model for Dashboard.md file."""

    def __init__(self, vault_path: str):
        """
        Initialize Dashboard.

        Args:
            vault_path: Path to vault root
        """
        self.vault_path = vault_path
        self.dashboard_path = os.path.join(vault_path, "Dashboard.md")
        self.stats = {
            'completed_today': 0,
            'pending_today': 0,
            'failed_today': 0,
            'total_processed': 0,
            'avg_time': 0,
            'success_rate': 100.0,
            'most_common_type': 'N/A'
        }
        self.recent_activity: List[Dict[str, str]] = []

    def read(self):
        """Read current dashboard state from file."""
        if not os.path.exists(self.dashboard_path):
            return

        with open(self.dashboard_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse stats from content (simple parsing)
        lines = content.split('\n')
        for line in lines:
            if '✅ Completed:' in line:
                self.stats['completed_today'] = int(line.split(':')[1].strip().split()[0])
            elif '⏳ Pending:' in line:
                self.stats['pending_today'] = int(line.split(':')[1].strip().split()[0])
            elif '❌ Failed:' in line:
                self.stats['failed_today'] = int(line.split(':')[1].strip().split()[0])

    def update_stats(self, vault_path: str):
        """
        Recalculate statistics from file system.

        Args:
            vault_path: Path to vault root
        """
        # Count files in folders
        needs_action_path = os.path.join(vault_path, "Needs_Action")
        done_path = os.path.join(vault_path, "Done")

        # Count pending tasks
        pending_count = 0
        if os.path.exists(needs_action_path):
            pending_count = len([f for f in os.listdir(needs_action_path) if f.endswith('.md')])

        # Count completed tasks and gather metadata
        completed_count = 0
        completed_tasks = []
        if os.path.exists(done_path):
            for filename in os.listdir(done_path):
                if filename.endswith('.md'):
                    completed_count += 1
                    task_path = os.path.join(done_path, filename)
                    try:
                        with open(task_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        from src.utils.yaml_handler import parse_frontmatter
                        metadata, _ = parse_frontmatter(content)
                        completed_tasks.append(metadata)
                    except Exception:
                        pass  # Skip files that can't be parsed

        self.stats['pending_today'] = pending_count
        self.stats['completed_today'] = completed_count
        self.stats['total_processed'] = completed_count

        # Calculate advanced statistics
        self.stats['avg_time'] = self._calculate_avg_time(completed_tasks)
        self.stats['success_rate'] = self._calculate_success_rate(vault_path)
        self.stats['most_common_type'] = self._calculate_most_common_type(completed_tasks)

    def _calculate_avg_time(self, completed_tasks: List[Dict[str, Any]]) -> int:
        """
        Calculate average processing time from completed tasks.

        Args:
            completed_tasks: List of task metadata dictionaries

        Returns:
            Average processing time in seconds
        """
        if not completed_tasks:
            return 0

        total_time = 0
        count = 0

        for task in completed_tasks:
            if 'processing' in task and 'duration_seconds' in task['processing']:
                total_time += task['processing']['duration_seconds']
                count += 1

        return int(total_time / count) if count > 0 else 0

    def _calculate_success_rate(self, vault_path: str) -> float:
        """
        Calculate success rate based on completed vs failed tasks.

        Args:
            vault_path: Path to vault root

        Returns:
            Success rate as percentage
        """
        completed = self.stats['completed_today']
        failed = self.stats['failed_today']

        # Also check for failed files in Logs folder
        logs_path = os.path.join(vault_path, 'Logs')
        if os.path.exists(logs_path):
            error_files = [f for f in os.listdir(logs_path) if f.startswith('error-') and f.endswith('.md')]
            failed += len(error_files)

        total = completed + failed
        if total == 0:
            return 100.0

        return (completed / total) * 100

    def _calculate_most_common_type(self, completed_tasks: List[Dict[str, Any]]) -> str:
        """
        Calculate most common task type from completed tasks.

        Args:
            completed_tasks: List of task metadata dictionaries

        Returns:
            Most common task type or 'N/A'
        """
        if not completed_tasks:
            return 'N/A'

        types = []
        for task in completed_tasks:
            if 'type' in task:
                types.append(task['type'])

        if not types:
            return 'N/A'

        # Use Counter to find most common
        type_counts = Counter(types)
        most_common = type_counts.most_common(1)[0][0]

        # Format nicely
        return most_common.replace('_', ' ').title()

    def add_activity(self, task_id: str, display_name: str, status: str, summary: str):
        """
        Add activity to recent activity list.

        Args:
            task_id: Task ID
            display_name: Display name for task
            status: Status emoji (✅, ❌, ⏳)
            summary: Brief summary
        """
        # Sanitize inputs
        display_name = display_name.strip() if display_name else 'Unknown'
        summary = summary.strip() if summary else 'No summary available'

        activity = {
            'time': datetime.now(timezone.utc).strftime('%H:%M'),
            'task_id': task_id,
            'display_name': display_name,
            'status': status,
            'summary': summary[:50]  # Truncate to 50 chars
        }

        self.recent_activity.insert(0, activity)

        # Keep only last 10
        self.recent_activity = self.recent_activity[:10]

    def write(self):
        """Write dashboard to file."""
        # Build recent activity table
        activity_rows = []
        if self.recent_activity:
            for activity in self.recent_activity:
                row = f"| {activity['time']} | [[{activity['task_id']}|{activity['display_name']}]] | {activity['status']} | {activity['summary']} |"
                activity_rows.append(row)
        else:
            activity_rows.append("| -- | No activity yet | -- | Drop files in Inbox/ to get started |")

        content = f"""# AI Assistant Dashboard

**Last Updated**: {datetime.now(timezone.utc).isoformat()}

## Today's Summary

- ✅ Completed: {self.stats['completed_today']} tasks
- ⏳ Pending: {self.stats['pending_today']} tasks
- ❌ Failed: {self.stats['failed_today']} tasks

## Recent Activity

| Time | File | Status | Summary |
|------|------|--------|---------|
{chr(10).join(activity_rows)}

## Statistics

- **Total tasks processed**: {self.stats['total_processed']}
- **Average processing time**: {self.stats['avg_time']}s
- **Success rate**: {self.stats['success_rate']:.1f}%
- **Most common type**: {self.stats['most_common_type']}

## Quick Links

- [[Company_Handbook]] - Edit processing rules
- [[Needs_Action/]] - View pending tasks
- [[Done/]] - View completed tasks
- [[Logs/]] - View error logs
"""

        with open(self.dashboard_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def increment_completed(self):
        """Increment completed count."""
        self.stats['completed_today'] += 1
        if self.stats['pending_today'] > 0:
            self.stats['pending_today'] -= 1

    def increment_failed(self):
        """Increment failed count."""
        self.stats['failed_today'] += 1
        if self.stats['pending_today'] > 0:
            self.stats['pending_today'] -= 1

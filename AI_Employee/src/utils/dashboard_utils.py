"""
Dashboard utilities for updating vault Dashboard.md
Provides real-time visibility into system status and task metrics
"""

import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


def update_dashboard(vault_path: str, updates: Dict[str, Any]) -> None:
    """
    Update Dashboard.md with current system status

    Args:
        vault_path: Path to vault directory
        updates: Dictionary of updates to apply
    """
    dashboard_path = Path(vault_path) / "Dashboard.md"

    # Read current dashboard
    if dashboard_path.exists():
        with open(dashboard_path, 'r', encoding='utf-8') as f:
            content = f.read()
    else:
        content = _create_default_dashboard()

    # Apply updates
    if 'task_statistics' in updates:
        content = _update_task_statistics(content, updates['task_statistics'])

    if 'orchestrator_status' in updates:
        content = _update_orchestrator_status(content, updates['orchestrator_status'])

    if 'recent_activity' in updates:
        content = _update_recent_activity(content, updates['recent_activity'])

    # Update last updated timestamp
    content = _update_timestamp(content)

    # Write back
    with open(dashboard_path, 'w', encoding='utf-8') as f:
        f.write(content)

    logger.info("Dashboard updated successfully")


def _create_default_dashboard() -> str:
    """Create default dashboard template"""
    return """# AI Employee Dashboard

**Status**: 🟢 Running
**Last Updated**: {timestamp}

---

## Task Statistics

- **Needs Action**: 0 tasks
- **Pending Approval**: 0 tasks
- **Done**: 0 tasks
- **Last Updated**: {timestamp}

## Orchestrator Status

- **Current Cycle**: 0
- **Last Run**: Never
- **Status**: Starting
- **Cycle Interval**: 5 minutes

### Today's Processing

- **Tasks Processed**: 0
- **Tasks Approved**: 0
- **Tasks Rejected**: 0
- **Errors**: 0

---

## Recent Activity

| Time | Source | Type | Status | Summary |
|------|--------|------|--------|---------|
| - | - | - | - | - |

---

## Quick Actions

- 📝 [[Company_Handbook]] - Edit processing rules
- 📥 [[Needs_Action/]] - View pending tasks
- ⏳ [[Pending_Approval/]] - Review sensitive tasks
- ✅ [[Done/]] - View completed tasks
- 📊 [[Logs/]] - View system logs
""".format(timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))


def _update_task_statistics(content: str, stats: Dict[str, int]) -> str:
    """Update task statistics section"""
    import re

    # Find Task Statistics section
    pattern = r'(## Task Statistics.*?)(- \*\*Needs Action\*\*:.*?\n- \*\*Pending Approval\*\*:.*?\n- \*\*Done\*\*:.*?\n- \*\*Last Updated\*\*:.*?\n)'

    replacement = f"""- **Needs Action**: {stats.get('needs_action', 0)} tasks
- **Pending Approval**: {stats.get('pending_approval', 0)} tasks
- **Done**: {stats.get('done', 0)} tasks
- **Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, r'\1' + replacement, content, flags=re.DOTALL)

    return content


def _update_orchestrator_status(content: str, status: Dict[str, Any]) -> str:
    """Update orchestrator status section"""
    import re

    # Find Orchestrator Status section
    pattern = r'(## Orchestrator Status.*?)(- \*\*Current Cycle\*\*:.*?\n- \*\*Last Run\*\*:.*?\n- \*\*Status\*\*:.*?\n)'

    replacement = f"""- **Current Cycle**: {status.get('current_cycle', 0)}
- **Last Run**: {status.get('last_run', 'Never')}
- **Status**: {status.get('status', 'Unknown')}
"""

    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, r'\1' + replacement, content, flags=re.DOTALL)

    # Update Today's Processing
    if 'today_stats' in status:
        today = status['today_stats']
        pattern2 = r'(### Today\'s Processing.*?)(- \*\*Tasks Processed\*\*:.*?\n- \*\*Tasks Approved\*\*:.*?\n- \*\*Tasks Rejected\*\*:.*?\n- \*\*Errors\*\*:.*?\n)'

        replacement2 = f"""- **Tasks Processed**: {today.get('tasks_processed', 0)}
- **Tasks Approved**: {today.get('tasks_approved', 0)}
- **Tasks Rejected**: {today.get('tasks_rejected', 0)}
- **Errors**: {today.get('errors', 0)}
"""

        if re.search(pattern2, content, re.DOTALL):
            content = re.sub(pattern2, r'\1' + replacement2, content, flags=re.DOTALL)

    return content


def _update_recent_activity(content: str, activities: List[Dict[str, str]]) -> str:
    """Update recent activity section"""
    import re

    # Build activity table rows (keep last 10)
    rows = []
    for activity in activities[-10:]:
        row = f"| {activity.get('time', '-')} | {activity.get('source', '-')} | {activity.get('type', '-')} | {activity.get('status', '-')} | {activity.get('summary', '-')} |"
        rows.append(row)

    if not rows:
        rows = ["| - | - | - | - | - |"]

    activity_table = "\n".join(rows)

    # Find Recent Activity section
    pattern = r'(## Recent Activity.*?\| Time \| Source \| Type \| Status \| Summary \|\n\|------|--------|------|--------|---------|)(.*?)(\n\n---)'

    replacement = f"\n{activity_table}"

    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, r'\1' + replacement + r'\3', content, flags=re.DOTALL)

    return content


def _update_timestamp(content: str) -> str:
    """Update last updated timestamp"""
    import re

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Update main timestamp
    content = re.sub(
        r'\*\*Last Updated\*\*: .*',
        f'**Last Updated**: {timestamp}',
        content,
        count=1
    )

    return content


def add_activity_entry(
    vault_path: str,
    source: str,
    activity_type: str,
    status: str,
    summary: str
) -> None:
    """
    Add a new activity entry to dashboard

    Args:
        vault_path: Path to vault directory
        source: Activity source (e.g., "WhatsApp", "Email", "Orchestrator")
        activity_type: Type of activity (e.g., "Task Processed", "Approval")
        status: Status (e.g., "Done", "Pending", "Error")
        summary: Brief summary of activity
    """
    dashboard_path = Path(vault_path) / "Dashboard.md"

    if not dashboard_path.exists():
        return

    with open(dashboard_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Create activity entry
    activity = {
        'time': datetime.now().strftime('%H:%M'),
        'source': source,
        'type': activity_type,
        'status': status,
        'summary': summary
    }

    # Update recent activity
    content = _update_recent_activity(content, [activity])
    content = _update_timestamp(content)

    with open(dashboard_path, 'w', encoding='utf-8') as f:
        f.write(content)


def get_task_counts(vault_path: str) -> Dict[str, int]:
    """
    Get current task counts from vault folders

    Args:
        vault_path: Path to vault directory

    Returns:
        Dictionary with task counts
    """
    vault = Path(vault_path)

    counts = {
        'needs_action': len(list((vault / 'Needs_Action').glob('*.md'))) if (vault / 'Needs_Action').exists() else 0,
        'pending_approval': len(list((vault / 'Pending_Approval').glob('*.md'))) if (vault / 'Pending_Approval').exists() else 0,
        'done': len(list((vault / 'Done').glob('*.md'))) if (vault / 'Done').exists() else 0,
    }

    return counts

"""
Briefing Actions Module
Generates weekly CEO briefing with revenue, expenses, tasks, and recommendations
"""

import os
import logging
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import Optional

from src.models.briefing import (
    CEOBriefing,
    BriefingStatus,
    validate_briefing
)
from src.utils.analytics_utils import (
    calculate_revenue_summary,
    calculate_expense_summary,
    calculate_task_metrics,
    detect_bottlenecks,
    analyze_subscriptions,
    generate_recommendations,
    get_previous_week_dates
)
from src.utils.odoo_client import OdooClient
from src.utils.dashboard_utils import update_dashboard

logger = logging.getLogger(__name__)


def get_last_sunday() -> date:
    """
    Get the date of the most recent Sunday

    Returns:
        Date of last Sunday (or today if today is Sunday)
    """
    today = date.today()
    days_since_sunday = (today.weekday() + 1) % 7  # Monday=0, Sunday=6
    if days_since_sunday == 0:
        return today
    return today - timedelta(days=days_since_sunday)


def get_week_dates(sunday: date) -> tuple[date, date]:
    """
    Get the week start (Monday) and end (Sunday) dates for a given Sunday

    Args:
        sunday: The Sunday date

    Returns:
        Tuple of (week_start, week_end)
    """
    week_end = sunday
    week_start = sunday - timedelta(days=6)  # Monday
    return week_start, week_end


def generate_briefing(
    vault_path: Optional[str] = None,
    target_date: Optional[date] = None
) -> CEOBriefing:
    """
    Generate CEO briefing for the week ending on target_date

    Args:
        vault_path: Path to vault directory (optional)
        target_date: Target Sunday date (optional, defaults to last Sunday)

    Returns:
        CEOBriefing object

    Raises:
        Exception: If briefing generation fails
    """
    try:
        # Get vault path
        if vault_path is None:
            vault_path = os.getenv('VAULT_PATH', str(Path(__file__).parent.parent.parent / 'vault'))

        # Get target date (last Sunday if not specified)
        if target_date is None:
            target_date = get_last_sunday()

        # Ensure target_date is a Sunday
        if target_date.weekday() != 6:
            raise ValueError(f"Target date must be a Sunday, got {target_date.strftime('%A')}")

        # Get week dates
        period_start, period_end = get_week_dates(target_date)

        logger.info(f"Generating briefing for week {period_start} to {period_end}")

        # Create briefing ID
        briefing_id = f"{period_end.isoformat()}_briefing"

        # Initialize briefing
        # Set generated_at to target Sunday at 11:00 PM (23:00)
        generated_at = datetime.combine(target_date, datetime.min.time()).replace(hour=23, minute=0, second=0)

        briefing = CEOBriefing(
            briefing_id=briefing_id,
            period_start=period_start,
            period_end=period_end,
            generated_at=generated_at,
            status=BriefingStatus.GENERATING
        )

        # Connect to Odoo
        client = OdooClient()
        client.authenticate()

        # Calculate revenue summary (with week-over-week comparison)
        previous_start, previous_end = get_previous_week_dates(period_start, period_end)
        briefing.revenue_summary = calculate_revenue_summary(
            client,
            period_start,
            period_end,
            previous_start,
            previous_end
        )

        # Calculate expense summary
        briefing.expense_summary = calculate_expense_summary(
            client,
            period_start,
            period_end
        )

        # Calculate task metrics
        briefing.task_metrics = calculate_task_metrics(
            vault_path,
            period_start,
            period_end
        )

        # Detect bottlenecks
        briefing.bottlenecks = detect_bottlenecks(
            vault_path,
            period_start,
            period_end
        )

        # Analyze subscriptions
        briefing.cost_optimization = analyze_subscriptions(
            client,
            period_start,
            period_end
        )

        # Generate recommendations
        briefing.recommendations = generate_recommendations(
            briefing.revenue_summary,
            briefing.expense_summary,
            briefing.task_metrics,
            briefing.bottlenecks,
            briefing.cost_optimization
        )

        # Close Odoo connection
        client.close()

        # Validate briefing
        is_valid, error_msg = validate_briefing(briefing)
        if not is_valid:
            raise ValueError(f"Briefing validation failed: {error_msg}")

        # Mark as ready
        briefing.mark_ready()

        logger.info(f"Briefing generated successfully: {briefing_id}")
        return briefing

    except Exception as e:
        logger.error(f"Failed to generate briefing: {e}")
        raise


def render_briefing_markdown(briefing: CEOBriefing) -> str:
    """
    Render briefing as markdown document

    Args:
        briefing: CEOBriefing object

    Returns:
        Markdown formatted string
    """
    # Calculate derived metrics
    net_profit = briefing.calculate_net_profit()
    profit_margin = briefing.get_profit_margin()

    # Build markdown
    md = f"""# Weekly Business Intelligence Briefing

**Period:** {briefing.period_start.strftime('%B %d')} - {briefing.period_end.strftime('%B %d, %Y')}
**Generated:** {briefing.generated_at.strftime('%A, %B %d, %Y at %I:%M %p')}
**Status:** {briefing.status.value.title()}

---

## Executive Summary

"""

    # Add executive summary based on key metrics
    if briefing.revenue_summary.week_over_week_change > 20:
        md += f"🟢 **Strong Growth:** Revenue increased {briefing.revenue_summary.week_over_week_change:.1f}% week-over-week.\n\n"
    elif briefing.revenue_summary.week_over_week_change < -20:
        md += f"🔴 **Revenue Decline:** Revenue decreased {abs(briefing.revenue_summary.week_over_week_change):.1f}% week-over-week.\n\n"
    else:
        md += f"🟡 **Stable Performance:** Revenue changed {briefing.revenue_summary.week_over_week_change:+.1f}% week-over-week.\n\n"

    if net_profit > 0:
        md += f"✅ **Profitable:** Net profit of ${net_profit:,.2f} ({profit_margin:.1f}% margin)\n\n"
    else:
        md += f"⚠️ **Operating at Loss:** ${abs(net_profit):,.2f} loss this week\n\n"

    md += f"📊 **Tasks Completed:** {briefing.task_metrics.tasks_completed} tasks\n\n"

    if len(briefing.bottlenecks) > 0:
        md += f"⏱️ **Bottlenecks Detected:** {len(briefing.bottlenecks)} tasks took longer than expected\n\n"

    md += "---\n\n"

    # Financial Performance
    md += "## 💰 Financial Performance\n\n"
    md += f"### Revenue: ${briefing.revenue_summary.total_revenue:,.2f}\n\n"

    if briefing.revenue_summary.revenue_by_source:
        md += "**Revenue by Source:**\n\n"
        for source, amount in sorted(briefing.revenue_summary.revenue_by_source.items(), key=lambda x: x[1], reverse=True):
            percentage = (amount / briefing.revenue_summary.total_revenue * 100) if briefing.revenue_summary.total_revenue > 0 else 0
            md += f"- {source}: ${amount:,.2f} ({percentage:.1f}%)\n"
        md += "\n"

    md += f"**Week-over-Week Change:** {briefing.revenue_summary.week_over_week_change:+.1f}%\n\n"

    md += f"### Expenses: ${briefing.expense_summary.total_expenses:,.2f}\n\n"

    if briefing.expense_summary.expenses_by_category:
        md += "**Expenses by Category:**\n\n"
        for category, amount in sorted(briefing.expense_summary.expenses_by_category.items(), key=lambda x: x[1], reverse=True):
            percentage = (amount / briefing.expense_summary.total_expenses * 100) if briefing.expense_summary.total_expenses > 0 else 0
            md += f"- {category}: ${amount:,.2f} ({percentage:.1f}%)\n"
        md += "\n"

    md += f"### Net Profit: ${net_profit:,.2f}\n\n"
    md += f"**Profit Margin:** {profit_margin:.1f}%\n\n"

    md += "---\n\n"

    # Operational Metrics
    md += "## 📈 Operational Metrics\n\n"
    md += f"- **Tasks Completed:** {briefing.task_metrics.tasks_completed}\n"
    md += f"- **Average Completion Time:** {briefing.task_metrics.average_completion_time:.1f} hours\n"
    md += f"- **Tasks Requiring Approval:** {briefing.task_metrics.tasks_requiring_approval}\n\n"

    # Bottlenecks
    if briefing.bottlenecks:
        md += "### ⏱️ Bottlenecks Identified\n\n"
        md += "| Task | Expected | Actual | Delay | Reason |\n"
        md += "|------|----------|--------|-------|--------|\n"
        for bottleneck in briefing.bottlenecks:
            delay = bottleneck.actual_duration - bottleneck.expected_duration
            md += f"| {bottleneck.task_name} | {bottleneck.expected_duration:.1f}h | {bottleneck.actual_duration:.1f}h | +{delay:.1f}h | {bottleneck.delay_reason} |\n"
        md += "\n"

    md += "---\n\n"

    # Cost Optimization
    if briefing.cost_optimization:
        md += "## 💡 Cost Optimization Opportunities\n\n"
        total_monthly_cost = sum(c.monthly_cost for c in briefing.cost_optimization)
        md += f"**Total Monthly Spend Under Review:** ${total_monthly_cost:,.2f}\n\n"

        for opt in briefing.cost_optimization:
            md += f"### {opt.subscription_name}\n\n"
            md += f"- **Monthly Cost:** ${opt.monthly_cost:,.2f}\n"
            md += f"- **Usage Analysis:** {opt.usage_analysis}\n"
            md += f"- **Recommendation:** {opt.recommendation}\n\n"

    md += "---\n\n"

    # Recommendations
    if briefing.recommendations:
        md += "## 🎯 Recommendations\n\n"

        # Group by priority
        high_priority = [r for r in briefing.recommendations if r.priority.value == 'high']
        medium_priority = [r for r in briefing.recommendations if r.priority.value == 'medium']
        low_priority = [r for r in briefing.recommendations if r.priority.value == 'low']

        if high_priority:
            md += "### 🔴 High Priority\n\n"
            for rec in high_priority:
                md += f"**{rec.category}:** {rec.description}\n\n"
                md += f"*Confidence: {rec.confidence_level}*\n\n"

        if medium_priority:
            md += "### 🟡 Medium Priority\n\n"
            for rec in medium_priority:
                md += f"**{rec.category}:** {rec.description}\n\n"
                md += f"*Confidence: {rec.confidence_level}*\n\n"

        if low_priority:
            md += "### 🟢 Low Priority\n\n"
            for rec in low_priority:
                md += f"**{rec.category}:** {rec.description}\n\n"
                md += f"*Confidence: {rec.confidence_level}*\n\n"

    md += "---\n\n"

    # Footer
    md += f"*Generated by AI Employee System on {briefing.generated_at.strftime('%Y-%m-%d at %H:%M:%S')}*\n"

    return md


def save_briefing(briefing: CEOBriefing, vault_path: Optional[str] = None) -> str:
    """
    Save briefing to markdown file

    Args:
        briefing: CEOBriefing object
        vault_path: Path to vault directory (optional)

    Returns:
        Path to saved briefing file
    """
    try:
        # Get vault path
        if vault_path is None:
            vault_path = os.getenv('VAULT_PATH', str(Path(__file__).parent.parent.parent / 'vault'))

        vault = Path(vault_path)

        # Create Briefings folder if not exists
        briefings_folder = vault / 'Briefings'
        briefings_folder.mkdir(parents=True, exist_ok=True)

        # Generate filename
        filename = f"{briefing.period_end.isoformat()}_briefing.md"
        file_path = briefings_folder / filename

        # Render markdown
        markdown_content = render_briefing_markdown(briefing)

        # Write to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        # Update briefing with file path
        briefing.file_path = str(file_path)

        logger.info(f"Briefing saved to: {file_path}")

        # Update dashboard with link to latest briefing
        try:
            update_dashboard(
                vault_path,
                {
                    'recent_activity': [{
                        'time': datetime.now().strftime('%H:%M'),
                        'source': 'Briefing',
                        'type': 'Weekly Report',
                        'status': 'Generated',
                        'summary': f"Week ending {briefing.period_end.strftime('%b %d')}"
                    }]
                }
            )
        except Exception as e:
            logger.warning(f"Failed to update dashboard: {e}")

        return str(file_path)

    except Exception as e:
        logger.error(f"Failed to save briefing: {e}")
        raise


def generate_and_save_briefing(
    vault_path: Optional[str] = None,
    target_date: Optional[date] = None
) -> tuple[CEOBriefing, str]:
    """
    Generate and save CEO briefing

    Args:
        vault_path: Path to vault directory (optional)
        target_date: Target Sunday date (optional, defaults to last Sunday)

    Returns:
        Tuple of (CEOBriefing, file_path)
    """
    # Generate briefing
    briefing = generate_briefing(vault_path, target_date)

    # Save to file
    file_path = save_briefing(briefing, vault_path)

    return briefing, file_path

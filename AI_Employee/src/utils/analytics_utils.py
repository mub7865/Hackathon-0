"""
Analytics utilities for CEO Briefing generation
Provides data aggregation and analysis functions
"""

import os
import logging
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import Dict, List, Tuple, Optional, Any
import yaml

from src.utils.odoo_client import OdooClient
from src.utils.odoo_methods import search_transactions, get_weekly_summary
from src.utils.file_utils import parse_task_file
from src.models.briefing import (
    RevenueSummary,
    ExpenseSummary,
    TaskMetrics,
    Bottleneck,
    CostOptimization,
    Recommendation,
    RecommendationPriority
)

logger = logging.getLogger(__name__)


def calculate_revenue_summary(
    client: OdooClient,
    period_start: date,
    period_end: date,
    previous_period_start: Optional[date] = None,
    previous_period_end: Optional[date] = None
) -> RevenueSummary:
    """
    Calculate revenue summary for the period

    Args:
        client: Authenticated OdooClient
        period_start: Start of reporting period
        period_end: End of reporting period
        previous_period_start: Start of previous period (for comparison)
        previous_period_end: End of previous period (for comparison)

    Returns:
        RevenueSummary with total, by source, and week-over-week change
    """
    try:
        logger.info(f"Calculating revenue for {period_start} to {period_end}")

        # Get current period summary
        current_summary = get_weekly_summary(
            client,
            week_start=period_start.isoformat(),
            week_end=period_end.isoformat()
        )

        total_revenue = current_summary['revenue']
        revenue_by_source = {}

        # Aggregate revenue by category/source
        for txn in current_summary.get('transactions', []):
            if txn.get('move_type') == 'out_invoice':
                # For now, use a simple categorization
                # In production, this would map to actual product categories
                source = "Consulting Services"  # Default
                amount = txn.get('amount_total', 0.0)
                revenue_by_source[source] = revenue_by_source.get(source, 0.0) + amount

        # Calculate week-over-week change
        week_over_week_change = 0.0
        if previous_period_start and previous_period_end:
            try:
                previous_summary = get_weekly_summary(
                    client,
                    week_start=previous_period_start.isoformat(),
                    week_end=previous_period_end.isoformat()
                )
                previous_revenue = previous_summary['revenue']

                if previous_revenue > 0:
                    week_over_week_change = ((total_revenue - previous_revenue) / previous_revenue) * 100
            except Exception as e:
                logger.warning(f"Could not calculate week-over-week change: {e}")

        return RevenueSummary(
            total_revenue=total_revenue,
            revenue_by_source=revenue_by_source,
            week_over_week_change=week_over_week_change
        )

    except Exception as e:
        logger.error(f"Failed to calculate revenue summary: {e}")
        return RevenueSummary()


def calculate_expense_summary(
    client: OdooClient,
    period_start: date,
    period_end: date
) -> ExpenseSummary:
    """
    Calculate expense summary for the period

    Args:
        client: Authenticated OdooClient
        period_start: Start of reporting period
        period_end: End of reporting period

    Returns:
        ExpenseSummary with total and by category
    """
    try:
        logger.info(f"Calculating expenses for {period_start} to {period_end}")

        # Get weekly summary
        summary = get_weekly_summary(
            client,
            week_start=period_start.isoformat(),
            week_end=period_end.isoformat()
        )

        total_expenses = summary['expenses']
        expenses_by_category = {}

        # Aggregate expenses by category
        for txn in summary.get('transactions', []):
            if txn.get('move_type') == 'in_invoice':
                # For now, use a simple categorization
                # In production, this would map to actual expense categories
                category = "Software Subscriptions"  # Default
                amount = txn.get('amount_total', 0.0)
                expenses_by_category[category] = expenses_by_category.get(category, 0.0) + amount

        return ExpenseSummary(
            total_expenses=total_expenses,
            expenses_by_category=expenses_by_category
        )

    except Exception as e:
        logger.error(f"Failed to calculate expense summary: {e}")
        return ExpenseSummary()


def calculate_task_metrics(vault_path: str, period_start: date, period_end: date) -> TaskMetrics:
    """
    Calculate task completion metrics for the period

    Args:
        vault_path: Path to vault directory
        period_start: Start of reporting period
        period_end: End of reporting period

    Returns:
        TaskMetrics with completion stats
    """
    try:
        logger.info(f"Calculating task metrics for {period_start} to {period_end}")

        vault = Path(vault_path)
        done_folder = vault / 'Done'

        if not done_folder.exists():
            return TaskMetrics()

        tasks_completed = 0
        total_completion_time = 0.0
        tasks_requiring_approval = 0

        # Read all task files in Done folder
        for task_file in done_folder.glob('*.md'):
            try:
                frontmatter, _ = parse_task_file(str(task_file))

                # Check if completed in this period
                completed_at_str = frontmatter.get('completed_at')
                if not completed_at_str:
                    continue

                completed_at = datetime.fromisoformat(completed_at_str).date()

                if period_start <= completed_at <= period_end:
                    tasks_completed += 1

                    # Calculate completion time if started_at exists
                    started_at_str = frontmatter.get('started_at')
                    if started_at_str:
                        started_at = datetime.fromisoformat(started_at_str)
                        completed_at_dt = datetime.fromisoformat(completed_at_str)
                        duration_hours = (completed_at_dt - started_at).total_seconds() / 3600
                        total_completion_time += duration_hours

                    # Check if required approval
                    if frontmatter.get('requires_approval') or frontmatter.get('approved_by'):
                        tasks_requiring_approval += 1

            except Exception as e:
                logger.warning(f"Failed to parse task file {task_file}: {e}")
                continue

        # Calculate average completion time
        average_completion_time = 0.0
        if tasks_completed > 0:
            average_completion_time = total_completion_time / tasks_completed

        return TaskMetrics(
            tasks_completed=tasks_completed,
            average_completion_time=round(average_completion_time, 2),
            tasks_requiring_approval=tasks_requiring_approval
        )

    except Exception as e:
        logger.error(f"Failed to calculate task metrics: {e}")
        return TaskMetrics()


def detect_bottlenecks(vault_path: str, period_start: date, period_end: date) -> List[Bottleneck]:
    """
    Detect task bottlenecks (tasks that took longer than expected)

    Args:
        vault_path: Path to vault directory
        period_start: Start of reporting period
        period_end: End of reporting period

    Returns:
        List of Bottleneck objects
    """
    try:
        logger.info(f"Detecting bottlenecks for {period_start} to {period_end}")

        vault = Path(vault_path)
        done_folder = vault / 'Done'

        if not done_folder.exists():
            return []

        bottlenecks = []

        # Expected durations by task type (in hours)
        expected_durations = {
            'accounting': 0.5,
            'email': 0.25,
            'whatsapp': 0.25,
            'linkedin': 0.5,
            'social_media': 1.0,
            'general': 1.0
        }

        # Read all task files in Done folder
        for task_file in done_folder.glob('*.md'):
            try:
                frontmatter, _ = parse_task_file(str(task_file))

                # Check if completed in this period
                completed_at_str = frontmatter.get('completed_at')
                if not completed_at_str:
                    continue

                completed_at = datetime.fromisoformat(completed_at_str).date()

                if period_start <= completed_at <= period_end:
                    # Calculate actual duration
                    started_at_str = frontmatter.get('started_at')
                    if not started_at_str:
                        continue

                    started_at = datetime.fromisoformat(started_at_str)
                    completed_at_dt = datetime.fromisoformat(completed_at_str)
                    actual_duration = (completed_at_dt - started_at).total_seconds() / 3600

                    # Get expected duration based on task type
                    task_type = frontmatter.get('type', 'general')
                    expected_duration = expected_durations.get(task_type, 1.0)

                    # If actual > expected by 50%, it's a bottleneck
                    if actual_duration > expected_duration * 1.5:
                        task_name = frontmatter.get('title', task_file.stem)
                        delay_reason = "Unknown"

                        # Try to determine delay reason
                        if frontmatter.get('requires_approval'):
                            delay_reason = "Required approval"
                        elif frontmatter.get('error_history'):
                            delay_reason = "Encountered errors during processing"
                        elif frontmatter.get('current_iteration', 0) > 3:
                            delay_reason = "Multiple retry attempts needed"

                        bottlenecks.append(Bottleneck(
                            task_name=task_name,
                            expected_duration=round(expected_duration, 2),
                            actual_duration=round(actual_duration, 2),
                            delay_reason=delay_reason
                        ))

            except Exception as e:
                logger.warning(f"Failed to analyze task file {task_file}: {e}")
                continue

        logger.info(f"Found {len(bottlenecks)} bottlenecks")
        return bottlenecks

    except Exception as e:
        logger.error(f"Failed to detect bottlenecks: {e}")
        return []


def analyze_subscriptions(
    client: OdooClient,
    period_start: date,
    period_end: date
) -> List[CostOptimization]:
    """
    Analyze recurring subscriptions for optimization opportunities

    Args:
        client: Authenticated OdooClient
        period_start: Start of reporting period
        period_end: End of reporting period

    Returns:
        List of CostOptimization recommendations
    """
    try:
        logger.info(f"Analyzing subscriptions for {period_start} to {period_end}")

        # Get all expenses for the period
        from src.models.transaction import TransactionType
        transactions = search_transactions(
            client,
            start_date=period_start.isoformat(),
            end_date=period_end.isoformat(),
            transaction_type=TransactionType.EXPENSE,
            state='posted',
            limit=1000
        )

        # Group by vendor to detect recurring charges
        vendor_charges = {}
        for txn in transactions:
            partner = txn.get('partner_id')
            if partner and isinstance(partner, list) and len(partner) > 1:
                vendor_name = partner[1]
                amount = txn.get('amount_total', 0.0)
                vendor_charges[vendor_name] = vendor_charges.get(vendor_name, 0.0) + amount

        # Generate optimization recommendations
        optimizations = []

        for vendor, total_cost in vendor_charges.items():
            # Simple heuristic: if spending > $100/week, flag for review
            if total_cost > 100:
                monthly_cost = total_cost * 4.33  # Approximate monthly cost

                optimizations.append(CostOptimization(
                    subscription_name=vendor,
                    monthly_cost=round(monthly_cost, 2),
                    usage_analysis=f"Spending ${total_cost:.2f}/week on {vendor}",
                    recommendation=f"Review usage and consider negotiating better rates or alternatives"
                ))

        logger.info(f"Found {len(optimizations)} optimization opportunities")
        return optimizations

    except Exception as e:
        logger.error(f"Failed to analyze subscriptions: {e}")
        return []


def generate_recommendations(
    revenue_summary: RevenueSummary,
    expense_summary: ExpenseSummary,
    task_metrics: TaskMetrics,
    bottlenecks: List[Bottleneck],
    cost_optimizations: List[CostOptimization]
) -> List[Recommendation]:
    """
    Generate proactive business recommendations based on data

    Args:
        revenue_summary: Revenue data
        expense_summary: Expense data
        task_metrics: Task completion data
        bottlenecks: Identified bottlenecks
        cost_optimizations: Cost optimization opportunities

    Returns:
        List of Recommendation objects
    """
    recommendations = []

    # Revenue-based recommendations
    if revenue_summary.week_over_week_change < -20:
        recommendations.append(Recommendation(
            category="Revenue",
            description=f"Revenue declined {abs(revenue_summary.week_over_week_change):.1f}% this week. Review sales pipeline and client engagement.",
            priority=RecommendationPriority.HIGH,
            confidence_level="high"
        ))
    elif revenue_summary.week_over_week_change > 20:
        recommendations.append(Recommendation(
            category="Revenue",
            description=f"Revenue increased {revenue_summary.week_over_week_change:.1f}% this week. Consider scaling successful strategies.",
            priority=RecommendationPriority.MEDIUM,
            confidence_level="high"
        ))

    # Expense-based recommendations
    net_profit = revenue_summary.total_revenue - expense_summary.total_expenses
    if net_profit < 0:
        recommendations.append(Recommendation(
            category="Profitability",
            description=f"Operating at a loss (${abs(net_profit):.2f}). Review expenses and pricing strategy.",
            priority=RecommendationPriority.HIGH,
            confidence_level="high"
        ))

    # Task efficiency recommendations
    if task_metrics.tasks_requiring_approval > task_metrics.tasks_completed * 0.3:
        recommendations.append(Recommendation(
            category="Operations",
            description=f"{task_metrics.tasks_requiring_approval} tasks required approval. Consider raising approval threshold or delegating authority.",
            priority=RecommendationPriority.MEDIUM,
            confidence_level="medium"
        ))

    # Bottleneck recommendations
    if len(bottlenecks) > 3:
        recommendations.append(Recommendation(
            category="Operations",
            description=f"Identified {len(bottlenecks)} task bottlenecks. Review processes and consider automation opportunities.",
            priority=RecommendationPriority.HIGH,
            confidence_level="high"
        ))

    # Cost optimization recommendations
    if len(cost_optimizations) > 0:
        total_potential_savings = sum(c.monthly_cost * 0.2 for c in cost_optimizations)  # Assume 20% savings potential
        recommendations.append(Recommendation(
            category="Cost Optimization",
            description=f"Potential savings of ${total_potential_savings:.2f}/month by optimizing {len(cost_optimizations)} subscriptions.",
            priority=RecommendationPriority.MEDIUM,
            confidence_level="medium"
        ))

    return recommendations


def get_previous_week_dates(current_start: date, current_end: date) -> Tuple[date, date]:
    """
    Get the previous week's start and end dates

    Args:
        current_start: Current period start
        current_end: Current period end

    Returns:
        Tuple of (previous_start, previous_end)
    """
    period_length = (current_end - current_start).days + 1
    previous_end = current_start - timedelta(days=1)
    previous_start = previous_end - timedelta(days=period_length - 1)
    return previous_start, previous_end

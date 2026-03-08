"""
CEO Briefing entity
Represents weekly business intelligence report generated every Sunday 11 PM
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from enum import Enum


class BriefingStatus(Enum):
    """Briefing generation status"""
    GENERATING = "generating"
    READY = "ready"
    REVIEWED = "reviewed"


class RecommendationPriority(Enum):
    """Recommendation priority levels"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class RevenueSummary:
    """Weekly revenue breakdown"""
    total_revenue: float = 0.0
    revenue_by_source: Dict[str, float] = field(default_factory=dict)
    week_over_week_change: float = 0.0  # Percentage change


@dataclass
class ExpenseSummary:
    """Weekly expense breakdown"""
    total_expenses: float = 0.0
    expenses_by_category: Dict[str, float] = field(default_factory=dict)


@dataclass
class TaskMetrics:
    """Task completion statistics"""
    tasks_completed: int = 0
    average_completion_time: float = 0.0  # Hours
    tasks_requiring_approval: int = 0


@dataclass
class Bottleneck:
    """Identified task delay"""
    task_name: str
    expected_duration: float  # Hours
    actual_duration: float  # Hours
    delay_reason: str


@dataclass
class CostOptimization:
    """Subscription analysis and recommendation"""
    subscription_name: str
    monthly_cost: float
    usage_analysis: str
    recommendation: str


@dataclass
class Recommendation:
    """Proactive business suggestion"""
    category: str
    description: str
    priority: RecommendationPriority
    confidence_level: str = "medium"  # high, medium, low


@dataclass
class CEOBriefing:
    """
    Weekly business intelligence briefing
    Generated every Sunday at 11:00 PM
    """
    briefing_id: str  # Format: YYYY-MM-DD_briefing
    period_start: date
    period_end: date
    generated_at: datetime
    status: BriefingStatus = BriefingStatus.GENERATING

    # Financial summaries
    revenue_summary: RevenueSummary = field(default_factory=RevenueSummary)
    expense_summary: ExpenseSummary = field(default_factory=ExpenseSummary)

    # Operational metrics
    task_metrics: TaskMetrics = field(default_factory=TaskMetrics)
    bottlenecks: List[Bottleneck] = field(default_factory=list)

    # Optimization insights
    cost_optimization: List[CostOptimization] = field(default_factory=list)
    recommendations: List[Recommendation] = field(default_factory=list)

    # Social media summary (optional - will be added when Phase 4 is implemented)
    social_media_summary: Optional[Dict[str, Any]] = None

    # File path
    file_path: Optional[str] = None

    def __post_init__(self):
        """Validate briefing data"""
        # Validate period is exactly 7 days
        period_length = (self.period_end - self.period_start).days
        if period_length != 6:  # 6 days difference = 7 days total (inclusive)
            raise ValueError(f"Period must be exactly 7 days, got {period_length + 1} days")

        # Validate generated_at is Sunday
        if self.generated_at.weekday() != 6:  # 6 = Sunday
            raise ValueError(f"Briefing must be generated on Sunday, got {self.generated_at.strftime('%A')}")

    def calculate_net_profit(self) -> float:
        """Calculate net profit for the week"""
        return self.revenue_summary.total_revenue - self.expense_summary.total_expenses

    def get_profit_margin(self) -> float:
        """Calculate profit margin percentage"""
        if self.revenue_summary.total_revenue == 0:
            return 0.0
        return (self.calculate_net_profit() / self.revenue_summary.total_revenue) * 100

    def has_significant_revenue_change(self, threshold: float = 20.0) -> bool:
        """Check if revenue changed significantly (>20% by default)"""
        return abs(self.revenue_summary.week_over_week_change) > threshold

    def get_high_priority_recommendations(self) -> List[Recommendation]:
        """Get only high priority recommendations"""
        return [r for r in self.recommendations if r.priority == RecommendationPriority.HIGH]

    def mark_ready(self) -> None:
        """Mark briefing as ready for review"""
        self.status = BriefingStatus.READY

    def mark_reviewed(self) -> None:
        """Mark briefing as reviewed by CEO"""
        self.status = BriefingStatus.REVIEWED

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'briefing_id': self.briefing_id,
            'period_start': self.period_start.isoformat(),
            'period_end': self.period_end.isoformat(),
            'generated_at': self.generated_at.isoformat(),
            'status': self.status.value,
            'revenue_summary': {
                'total_revenue': self.revenue_summary.total_revenue,
                'revenue_by_source': self.revenue_summary.revenue_by_source,
                'week_over_week_change': self.revenue_summary.week_over_week_change
            },
            'expense_summary': {
                'total_expenses': self.expense_summary.total_expenses,
                'expenses_by_category': self.expense_summary.expenses_by_category
            },
            'task_metrics': {
                'tasks_completed': self.task_metrics.tasks_completed,
                'average_completion_time': self.task_metrics.average_completion_time,
                'tasks_requiring_approval': self.task_metrics.tasks_requiring_approval
            },
            'bottlenecks': [
                {
                    'task_name': b.task_name,
                    'expected_duration': b.expected_duration,
                    'actual_duration': b.actual_duration,
                    'delay_reason': b.delay_reason
                }
                for b in self.bottlenecks
            ],
            'cost_optimization': [
                {
                    'subscription_name': c.subscription_name,
                    'monthly_cost': c.monthly_cost,
                    'usage_analysis': c.usage_analysis,
                    'recommendation': c.recommendation
                }
                for c in self.cost_optimization
            ],
            'recommendations': [
                {
                    'category': r.category,
                    'description': r.description,
                    'priority': r.priority.value,
                    'confidence_level': r.confidence_level
                }
                for r in self.recommendations
            ],
            'social_media_summary': self.social_media_summary,
            'file_path': self.file_path,
            'net_profit': self.calculate_net_profit(),
            'profit_margin': self.get_profit_margin()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CEOBriefing':
        """Create from dictionary"""
        # Parse revenue summary
        revenue_data = data.get('revenue_summary', {})
        revenue_summary = RevenueSummary(
            total_revenue=revenue_data.get('total_revenue', 0.0),
            revenue_by_source=revenue_data.get('revenue_by_source', {}),
            week_over_week_change=revenue_data.get('week_over_week_change', 0.0)
        )

        # Parse expense summary
        expense_data = data.get('expense_summary', {})
        expense_summary = ExpenseSummary(
            total_expenses=expense_data.get('total_expenses', 0.0),
            expenses_by_category=expense_data.get('expenses_by_category', {})
        )

        # Parse task metrics
        task_data = data.get('task_metrics', {})
        task_metrics = TaskMetrics(
            tasks_completed=task_data.get('tasks_completed', 0),
            average_completion_time=task_data.get('average_completion_time', 0.0),
            tasks_requiring_approval=task_data.get('tasks_requiring_approval', 0)
        )

        # Parse bottlenecks
        bottlenecks = [
            Bottleneck(
                task_name=b['task_name'],
                expected_duration=b['expected_duration'],
                actual_duration=b['actual_duration'],
                delay_reason=b['delay_reason']
            )
            for b in data.get('bottlenecks', [])
        ]

        # Parse cost optimization
        cost_optimization = [
            CostOptimization(
                subscription_name=c['subscription_name'],
                monthly_cost=c['monthly_cost'],
                usage_analysis=c['usage_analysis'],
                recommendation=c['recommendation']
            )
            for c in data.get('cost_optimization', [])
        ]

        # Parse recommendations
        recommendations = [
            Recommendation(
                category=r['category'],
                description=r['description'],
                priority=RecommendationPriority(r['priority']),
                confidence_level=r.get('confidence_level', 'medium')
            )
            for r in data.get('recommendations', [])
        ]

        return cls(
            briefing_id=data['briefing_id'],
            period_start=date.fromisoformat(data['period_start']),
            period_end=date.fromisoformat(data['period_end']),
            generated_at=datetime.fromisoformat(data['generated_at']),
            status=BriefingStatus(data.get('status', 'generating')),
            revenue_summary=revenue_summary,
            expense_summary=expense_summary,
            task_metrics=task_metrics,
            bottlenecks=bottlenecks,
            cost_optimization=cost_optimization,
            recommendations=recommendations,
            social_media_summary=data.get('social_media_summary'),
            file_path=data.get('file_path')
        )


def validate_briefing(briefing: CEOBriefing) -> tuple[bool, Optional[str]]:
    """
    Validate briefing data

    Args:
        briefing: CEOBriefing to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check period length
    period_length = (briefing.period_end - briefing.period_start).days
    if period_length != 6:
        return False, f"Period must be exactly 7 days, got {period_length + 1} days"

    # Check generated_at is Sunday
    if briefing.generated_at.weekday() != 6:
        return False, f"Briefing must be generated on Sunday, got {briefing.generated_at.strftime('%A')}"

    # Check monetary values are non-negative
    if briefing.revenue_summary.total_revenue < 0:
        return False, "Total revenue cannot be negative"

    if briefing.expense_summary.total_expenses < 0:
        return False, "Total expenses cannot be negative"

    # Check bottlenecks have actual > expected duration
    for bottleneck in briefing.bottlenecks:
        if bottleneck.actual_duration <= bottleneck.expected_duration:
            return False, f"Bottleneck '{bottleneck.task_name}' must have actual_duration > expected_duration"

    return True, None

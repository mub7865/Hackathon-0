---
name: "generate-briefing"
description: "Generate comprehensive weekly CEO briefing with revenue summary, task analysis, bottlenecks, and business recommendations. Use when task requires creating Monday morning business intelligence report."
---

# Generate Briefing Skill

## When to Use This Skill

Use this skill when:
- Task asks for CEO briefing or business report
- Monday morning briefing generation
- Weekly business intelligence summary needed
- Task mentions "briefing", "business report", or "weekly summary"
- Scheduled Sunday night briefing generation

## Procedure

### Step 1: Determine Briefing Period

1. Read task to identify:
   - **Time Period**: Last week, specific date range, or default (previous 7 days)
   - **Briefing Type**: Weekly (standard), monthly, or custom period
   - **Focus Areas**: All areas or specific (revenue, tasks, social media)

2. Default period: Previous Monday to Sunday

### Step 2: Gather Data from All Sources

Collect data from multiple systems:

```python
from src.actions.briefing_actions import generate_briefing

briefing_params = {
    "start_date": "[YYYY-MM-DD]",  # Monday
    "end_date": "[YYYY-MM-DD]",    # Sunday
    "include_revenue": True,
    "include_tasks": True,
    "include_social_media": True,
    "include_recommendations": True
}

briefing = generate_briefing(briefing_params)
```

**Data Sources:**
- **Odoo**: Revenue, expenses, invoices, payments
- **Vault/Done/**: Completed tasks
- **Vault/Needs_Action/**: Pending tasks
- **Social Media**: Engagement metrics (if available)
- **Dashboard.md**: Current business status

### Step 3: Analyze and Calculate Metrics

**Revenue Analysis:**
- Total revenue (invoices created)
- Total expenses
- Net income (revenue - expenses)
- Week-over-week comparison
- Revenue by client

**Task Analysis:**
- Tasks completed
- Tasks pending
- Average completion time
- Task categories breakdown

**Bottleneck Detection:**
- Tasks taking longer than expected
- Recurring issues
- Resource constraints

**Cost Optimization:**
- Recurring expenses analysis
- Unused subscriptions
- Duplicate tools

### Step 4: Generate Briefing Document

Create comprehensive briefing in markdown format:

```markdown
# CEO Briefing - Week of [Date Range]

**Generated**: [ISO timestamp]
**Period**: [Start Date] to [End Date]

---

## 📊 Executive Summary

**Key Highlights:**
- Revenue: $[Amount] ([+/-]% vs last week)
- Tasks Completed: [Count]
- Net Income: $[Amount]
- Top Priority: [Most important item requiring attention]

---

## 💰 Financial Performance

### Revenue
- **Total Revenue**: $[Amount]
- **Change from Last Week**: [+/-]$[Amount] ([+/-]%)
- **Invoices Created**: [Count]
- **Average Invoice**: $[Amount]

### Expenses
- **Total Expenses**: $[Amount]
- **Change from Last Week**: [+/-]$[Amount] ([+/-]%)
- **Largest Expense**: [Category] - $[Amount]

### Net Income
- **Net Income**: $[Revenue - Expenses]
- **Profit Margin**: [(Net / Revenue) × 100]%

### Revenue by Client
| Client | Amount | Invoices | Status |
|--------|--------|----------|--------|
| [Client 1] | $[Amount] | [Count] | [Paid/Pending] |
| [Client 2] | $[Amount] | [Count] | [Paid/Pending] |

---

## ✅ Task Performance

### Completed Tasks
- **Total Completed**: [Count]
- **By Category**:
  - Accounting: [Count]
  - Social Media: [Count]
  - Client Work: [Count]
  - Administrative: [Count]

### Pending Tasks
- **Total Pending**: [Count]
- **High Priority**: [Count]
- **Awaiting Approval**: [Count]

### Task Efficiency
- **Average Completion Time**: [Hours/Days]
- **Fastest Task**: [Task name] - [Time]
- **Slowest Task**: [Task name] - [Time]

---

## 🚧 Bottlenecks & Issues

### Identified Bottlenecks
1. **[Bottleneck 1]**
   - Impact: [Description]
   - Recommendation: [How to resolve]

2. **[Bottleneck 2]**
   - Impact: [Description]
   - Recommendation: [How to resolve]

### Tasks Taking Longer Than Expected
| Task | Expected | Actual | Delay |
|------|----------|--------|-------|
| [Task] | [Time] | [Time] | [Difference] |

---

## 📱 Social Media Performance

### Engagement Summary
- **Total Posts**: [Count] (Facebook: [#], Instagram: [#])
- **Total Engagement**: [Count]
- **Engagement Rate**: [%]
- **Top Post**: [Brief description] - [Engagement count]

### Platform Breakdown
- **Facebook**: [Posts] posts, [Engagement] total engagement
- **Instagram**: [Posts] posts, [Engagement] total engagement

---

## 💡 Recommendations

### High Priority (Action This Week)
1. **[Recommendation 1]**
   - Why: [Rationale]
   - Impact: [Expected benefit]
   - Effort: [Low/Medium/High]

2. **[Recommendation 2]**
   - Why: [Rationale]
   - Impact: [Expected benefit]
   - Effort: [Low/Medium/High]

### Cost Optimization Opportunities
1. **[Opportunity 1]**
   - Current Cost: $[Amount]/month
   - Potential Savings: $[Amount]/month
   - Confidence: [High/Medium/Low]

### Growth Opportunities
1. **[Opportunity 1]**
   - Description: [What to do]
   - Expected Impact: [Revenue/efficiency gain]
   - Next Steps: [Specific actions]

---

## 📅 Week Ahead

### Upcoming Priorities
- [ ] [Priority 1]
- [ ] [Priority 2]
- [ ] [Priority 3]

### Deadlines This Week
- [Date]: [Deadline description]
- [Date]: [Deadline description]

---

## 📈 Trends & Insights

**Revenue Trend**: [Increasing/Stable/Decreasing]
- [Observation about revenue pattern]

**Task Completion Trend**: [Improving/Stable/Declining]
- [Observation about task efficiency]

**Social Media Trend**: [Growing/Stable/Declining]
- [Observation about engagement]

---

**Next Briefing**: [Next Monday date]
```

### Step 5: Save Briefing

1. Save briefing to `vault/Briefings/YYYY-MM-DD_briefing.md`
2. Update Dashboard.md with link to latest briefing
3. Log briefing generation

### Step 6: Update Task

```yaml
status: completed
briefing_generated: true
briefing_period: "[Start] to [End]"
briefing_file: "vault/Briefings/YYYY-MM-DD_briefing.md"
total_revenue: [Amount]
total_expenses: [Amount]
tasks_completed: [Count]
```

Move to `vault/Done/`

## Output Format

### Generated Briefing File:

```markdown
---
id: briefing_20260303
type: briefing
period_start: 2026-02-24
period_end: 2026-03-02
generated_at: 2026-03-03T23:00:00Z
total_revenue: 3250.00
total_expenses: 487.50
net_income: 2762.50
tasks_completed: 18
---

# CEO Briefing - Week of Feb 24 - Mar 2, 2026

**Generated**: 2026-03-03T23:00:00Z
**Period**: February 24 - March 2, 2026

---

## 📊 Executive Summary

**Key Highlights:**
- Revenue: $3,250 (+23% vs last week)
- Tasks Completed: 18
- Net Income: $2,762.50
- Top Priority: Follow up with 2 clients on pending invoices ($1,200 outstanding)

---

## 💰 Financial Performance

### Revenue
- **Total Revenue**: $3,250.00
- **Change from Last Week**: +$600.00 (+23%)
- **Invoices Created**: 4
- **Average Invoice**: $812.50

### Expenses
- **Total Expenses**: $487.50
- **Change from Last Week**: +$50.00 (+11%)
- **Largest Expense**: Software/SaaS - $250.00

### Net Income
- **Net Income**: $2,762.50
- **Profit Margin**: 85%

### Revenue by Client
| Client | Amount | Invoices | Status |
|--------|--------|----------|--------|
| Client B | $2,500 | 1 | Paid |
| Client A | $500 | 2 | Paid |
| Client C | $250 | 1 | Pending |

---

[... rest of briefing sections ...]

---

**Next Briefing**: March 10, 2026
```

## Quality Criteria

- **Completeness**: All sections present with data
- **Accuracy**: Calculations and metrics correct
- **Insights**: Actionable observations provided
- **Clarity**: Easy to read and understand
- **Timeliness**: Generated on schedule (Sunday 11 PM)
- **Actionability**: Clear recommendations with next steps

## Important Notes

- **Scheduled Generation**: Typically runs Sunday 11:00 PM for Monday morning delivery
- **Manual Generation**: Can be triggered anytime with `--generate-now` flag
- **Data Sources**: Pulls from Odoo, vault files, social media data
- **Confidence Levels**: Recommendations include confidence (high/medium/low)
- **Week-over-Week**: Compares to previous week for trend analysis
- **Graceful Degradation**: If data source unavailable, notes it and continues

## Success Criteria

- ✅ All data sources queried successfully
- ✅ Revenue calculations correct
- ✅ Task analysis complete
- ✅ Bottlenecks identified
- ✅ Recommendations provided
- ✅ Briefing file created in vault/Briefings/
- ✅ Dashboard updated with briefing link
- ✅ Action logged
- ✅ Task completed

---
name: "analyze-revenue"
description: "Analyze revenue trends, patterns, and anomalies from Odoo accounting data. Use when task requires revenue analysis, trend identification, or financial forecasting."
---

# Analyze Revenue Skill

## When to Use This Skill

Use this skill when:
- Task asks for revenue analysis or trends
- Need to understand revenue patterns
- Identifying revenue growth or decline
- Task mentions "revenue analysis", "revenue trends", or "financial analysis"
- Preparing financial forecasts

## Procedure

### Step 1: Define Analysis Scope

1. Read task to identify:
   - **Time Period**: Week, month, quarter, year, or custom range
   - **Comparison**: Week-over-week, month-over-month, year-over-year
   - **Granularity**: Daily, weekly, monthly breakdown
   - **Focus**: Total revenue, by client, by service, by category

### Step 2: Query Revenue Data

```python
from src.utils.analytics_utils import calculate_revenue_metrics

analysis_params = {
    "start_date": "[YYYY-MM-DD]",
    "end_date": "[YYYY-MM-DD]",
    "comparison_period": "previous_week|previous_month|previous_year",
    "breakdown_by": "client|service|time",
    "include_trends": True
}

revenue_analysis = calculate_revenue_metrics(analysis_params)
```

### Step 3: Calculate Key Metrics

**Core Metrics:**
- Total revenue for period
- Average revenue per transaction
- Revenue growth rate
- Revenue by client/category
- Highest/lowest revenue days

**Trend Analysis:**
- Week-over-week change (%)
- Month-over-month change (%)
- Moving average (7-day, 30-day)
- Trend direction (increasing/stable/decreasing)

**Anomaly Detection:**
- Unusual spikes or drops
- Missing expected revenue
- Outlier transactions

### Step 4: Generate Analysis Report

```markdown
## Revenue Analysis Report

**Period**: [Start Date] to [End Date]
**Generated**: [ISO timestamp]
**Comparison**: vs [Previous period]

---

### Summary Metrics

- **Total Revenue**: $[Amount]
- **Change from Previous Period**: [+/-]$[Amount] ([+/-]%)
- **Average Daily Revenue**: $[Amount]
- **Highest Revenue Day**: [Date] - $[Amount]
- **Lowest Revenue Day**: [Date] - $[Amount]

---

### Revenue Breakdown

#### By Client
| Client | Revenue | % of Total | Change vs Previous |
|--------|---------|------------|-------------------|
| [Client 1] | $[Amount] | [%] | [+/-]% |
| [Client 2] | $[Amount] | [%] | [+/-]% |

#### By Service Category
| Category | Revenue | % of Total | Transactions |
|----------|---------|------------|--------------|
| [Category 1] | $[Amount] | [%] | [Count] |
| [Category 2] | $[Amount] | [%] | [Count] |

---

### Trend Analysis

**Overall Trend**: [Increasing/Stable/Decreasing]

**Key Observations:**
- [Observation 1: e.g., "Revenue increased 23% week-over-week"]
- [Observation 2: e.g., "Client B contributed 77% of total revenue"]
- [Observation 3: e.g., "Tuesday and Wednesday are highest revenue days"]

**Moving Averages:**
- 7-day average: $[Amount]/day
- 30-day average: $[Amount]/day
- Trend: [Above/Below] moving average

---

### Anomalies & Insights

**Unusual Activity:**
- [Anomaly 1: e.g., "Revenue spike on March 2 ($2,500 - 3x normal)"]
  - Cause: [Explanation if known]
  - Impact: [One-time or recurring]

**Missing Revenue:**
- [Expected revenue that didn't materialize]
- Potential cause: [Delayed invoice, lost client, etc.]

---

### Forecasting

**Based on Current Trends:**
- **Next Week Projection**: $[Amount] (±[Confidence range])
- **Next Month Projection**: $[Amount] (±[Confidence range])
- **Confidence Level**: [High/Medium/Low]

**Assumptions:**
- [Assumption 1: e.g., "Current client base remains stable"]
- [Assumption 2: e.g., "No major seasonal variations"]

---

### Recommendations

**Revenue Growth Opportunities:**
1. **[Opportunity 1]**
   - Current: $[Amount]
   - Potential: $[Amount]
   - Action: [Specific step]

2. **[Opportunity 2]**
   - Current: $[Amount]
   - Potential: $[Amount]
   - Action: [Specific step]

**Risk Mitigation:**
1. **[Risk 1]**
   - Impact: [Description]
   - Mitigation: [How to address]

**Action Items:**
- [ ] [Action 1: Specific next step]
- [ ] [Action 2: Specific next step]
```

### Step 5: Update Task

```yaml
status: completed
revenue_analysis_generated: true
analysis_period: "[Start] to [End]"
total_revenue: [Amount]
revenue_change_percent: [%]
trend_direction: "increasing|stable|decreasing"
```

Move to `vault/Done/`

## Output Format

### Complete Revenue Analysis:

```markdown
---
id: revenue_analysis_20260304
type: analytics
status: completed
analysis_period: "2026-02-24 to 2026-03-02"
total_revenue: 3250.00
revenue_change_percent: 23
trend_direction: "increasing"
---

# Revenue Analysis Report

**Period**: February 24 - March 2, 2026 (1 week)
**Generated**: 2026-03-04T10:00:00Z
**Comparison**: vs Previous week (Feb 17-23)

---

### Summary Metrics

- **Total Revenue**: $3,250.00
- **Change from Previous Period**: +$600.00 (+23%)
- **Average Daily Revenue**: $464.29
- **Highest Revenue Day**: March 1 - $2,500.00
- **Lowest Revenue Day**: February 26 - $75.00

---

### Revenue Breakdown

#### By Client
| Client | Revenue | % of Total | Change vs Previous |
|--------|---------|------------|-------------------|
| Client B | $2,500 | 77% | +100% (new) |
| Client A | $500 | 15% | +15% |
| Client C | $250 | 8% | -20% |

#### By Service Category
| Category | Revenue | % of Total | Transactions |
|----------|---------|------------|--------------|
| Web Development | $2,500 | 77% | 1 |
| Consulting | $500 | 15% | 2 |
| Maintenance | $250 | 8% | 1 |

---

### Trend Analysis

**Overall Trend**: Increasing

**Key Observations:**
- Revenue increased 23% week-over-week, driven by large Client B project
- Client B's $2,500 invoice represents 77% of weekly revenue
- Tuesday (March 1) had highest revenue due to Client B payment
- Consulting services showing consistent growth (+15%)
- Maintenance revenue declining (-20%), may need attention

**Moving Averages:**
- 7-day average: $464.29/day
- 30-day average: $412.50/day
- Trend: 12.5% above 30-day average (positive momentum)

---

### Anomalies & Insights

**Unusual Activity:**
- Revenue spike on March 1 ($2,500 - 5.4x daily average)
  - Cause: Client B project completion (expected, per contract)
  - Impact: One-time, but demonstrates capacity for larger projects

**Missing Revenue:**
- Client D invoice expected ($800) but not yet created
  - Potential cause: Project delayed or awaiting client approval
  - Action: Follow up with Client D on project status

---

### Forecasting

**Based on Current Trends:**
- **Next Week Projection**: $2,800 (±$400)
- **Next Month Projection**: $11,500 (±$1,500)
- **Confidence Level**: Medium

**Assumptions:**
- Current client base remains stable (3 active clients)
- No major project completions next week (conservative estimate)
- Consulting services continue at current rate ($250/week)
- Client D project materializes within 2 weeks

---

### Recommendations

**Revenue Growth Opportunities:**
1. **Pursue More Large Projects (like Client B)**
   - Current: 1 large project/month
   - Potential: 2 large projects/month (+$2,500/month)
   - Action: Increase marketing to mid-size businesses, showcase Client B case study

2. **Increase Consulting Rate**
   - Current: $250/engagement
   - Potential: $350/engagement (+40%)
   - Action: Test higher rate with next 2 new clients

**Risk Mitigation:**
1. **Revenue Concentration Risk**
   - Impact: 77% revenue from single client this week
   - Mitigation: Diversify client base, aim for no client >40% of revenue

2. **Maintenance Revenue Decline**
   - Impact: -20% in maintenance services
   - Mitigation: Reach out to existing clients, offer maintenance packages

**Action Items:**
- [ ] Follow up with Client D on delayed project ($800 potential)
- [ ] Create Client B case study for marketing
- [ ] Contact 3 existing clients about maintenance packages
- [ ] Test $350 consulting rate with next 2 prospects
```

## Quality Criteria

- **Accuracy**: All calculations verified
- **Completeness**: All key metrics included
- **Insights**: Meaningful observations provided
- **Actionability**: Clear recommendations with next steps
- **Clarity**: Easy to understand for non-technical audience
- **Context**: Comparisons and trends provide context

## Important Notes

- **Data Source**: Revenue data from Odoo accounting system
- **Trend Calculation**: Uses moving averages and period-over-period comparison
- **Anomaly Detection**: Identifies values >2x or <0.5x average
- **Forecasting**: Based on historical trends, not guaranteed
- **Confidence Levels**: High (>80% confidence), Medium (60-80%), Low (<60%)

## Success Criteria

- ✅ Revenue data retrieved successfully
- ✅ All metrics calculated correctly
- ✅ Trends identified and explained
- ✅ Anomalies detected and analyzed
- ✅ Forecasts generated with confidence levels
- ✅ Recommendations are specific and actionable
- ✅ Report formatted clearly
- ✅ Task completed

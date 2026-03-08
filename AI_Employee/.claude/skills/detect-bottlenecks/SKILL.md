---
name: "detect-bottlenecks"
description: "Identify task bottlenecks, delays, and workflow inefficiencies by analyzing task completion times and patterns. Use when task requires identifying process improvements or understanding why work is delayed."
---

# Detect Bottlenecks Skill

## When to Use This Skill

Use this skill when:
- Task asks for bottleneck analysis
- Need to understand why tasks are delayed
- Identifying workflow inefficiencies
- Task mentions "bottlenecks", "delays", or "process improvements"
- Weekly/monthly operational review

## Procedure

### Step 1: Define Analysis Scope

1. Read task to identify:
   - **Time Period**: Last week, last month, or custom range
   - **Task Categories**: All tasks or specific categories (accounting, social media, client work)
   - **Threshold**: What constitutes a "delay" (e.g., >2x expected time)
   - **Focus**: Specific workflow or all workflows

### Step 2: Gather Task Data

```python
from src.utils.analytics_utils import detect_task_bottlenecks

analysis_params = {
    "start_date": "[YYYY-MM-DD]",
    "end_date": "[YYYY-MM-DD]",
    "task_categories": ["accounting", "social_media", "client_work"] or None,
    "delay_threshold": 2.0,  # 2x expected time
    "include_patterns": True
}

bottleneck_analysis = detect_task_bottlenecks(analysis_params)
```

**Data Sources:**
- `vault/Done/`: Completed tasks with timestamps
- `vault/Processing/`: In-progress tasks
- `vault/Needs_Action/`: Pending tasks
- Task metadata: created_at, started_at, completed_at, expected_duration

### Step 3: Analyze Task Performance

**Calculate Metrics:**
- Expected completion time vs actual time
- Tasks exceeding threshold (>2x expected)
- Average delay by category
- Recurring delay patterns
- Tasks stuck in specific stages

**Identify Patterns:**
- Which task types consistently delayed?
- Which stages cause most delays?
- Time-of-day or day-of-week patterns?
- Resource constraints (waiting for approval, external dependencies)

### Step 4: Generate Bottleneck Report

```markdown
## Task Bottleneck Analysis

**Period**: [Start Date] to [End Date]
**Generated**: [ISO timestamp]
**Tasks Analyzed**: [Count]

---

### Executive Summary

**Key Findings:**
- [Finding 1: e.g., "Approval workflow adds 24-hour average delay"]
- [Finding 2: e.g., "Social media tasks take 3x longer than expected"]
- [Finding 3: e.g., "5 tasks stuck in Processing for >48 hours"]

**Impact:**
- **Total Delay**: [Hours/Days] across all tasks
- **Efficiency Loss**: [%] of time spent on delays vs productive work
- **Tasks Affected**: [Count] tasks delayed beyond threshold

---

### Bottlenecks Identified

#### 1. [Bottleneck Name]
**Severity**: High/Medium/Low
**Impact**: [Number] tasks affected, [Hours] total delay

**Description:**
[What is causing the bottleneck - e.g., "Approval workflow requires manual review, causing 24-hour average delay"]

**Affected Tasks:**
- [Task 1]: Expected [Time], Actual [Time], Delay [Time]
- [Task 2]: Expected [Time], Actual [Time], Delay [Time]

**Root Cause:**
[Why this bottleneck exists - e.g., "Only one person can approve, creates queue"]

**Recommendation:**
[How to fix - e.g., "Add secondary approver or auto-approve under $50"]

**Expected Impact:**
[What improvement would result - e.g., "Reduce approval time by 80%, save 4 hours/week"]

---

#### 2. [Bottleneck Name]
[Same structure as above]

---

### Tasks Exceeding Threshold

**Threshold**: [2x] expected completion time

| Task | Category | Expected | Actual | Delay | Status |
|------|----------|----------|--------|-------|--------|
| [Task 1] | [Category] | [Time] | [Time] | [Difference] | [Done/Processing] |
| [Task 2] | [Category] | [Time] | [Time] | [Difference] | [Done/Processing] |

---

### Delay Patterns

**By Category:**
| Category | Avg Expected | Avg Actual | Avg Delay | Delay % |
|----------|--------------|------------|-----------|---------|
| Accounting | [Time] | [Time] | [Time] | [%] |
| Social Media | [Time] | [Time] | [Time] | [%] |
| Client Work | [Time] | [Time] | [Time] | [%] |

**By Stage:**
| Stage | Avg Time | Tasks | Bottleneck? |
|-------|----------|-------|-------------|
| Needs_Action → Processing | [Time] | [Count] | [Yes/No] |
| Processing → Pending_Approval | [Time] | [Count] | [Yes/No] |
| Pending_Approval → Approved | [Time] | [Count] | [Yes/No] |
| Approved → Done | [Time] | [Count] | [Yes/No] |

**By Time:**
- **Slowest Day**: [Day of week] - [Avg time]
- **Fastest Day**: [Day of week] - [Avg time]
- **Slowest Hour**: [Hour] - [Avg time]
- **Fastest Hour**: [Hour] - [Avg time]

---

### Stuck Tasks

**Tasks in Processing > 48 hours:**
| Task | Category | Time in Processing | Last Activity |
|------|----------|-------------------|---------------|
| [Task 1] | [Category] | [Hours] | [Timestamp] |
| [Task 2] | [Category] | [Hours] | [Timestamp] |

**Action Required:**
- [Task 1]: [Recommended action]
- [Task 2]: [Recommended action]

---

### Resource Constraints

**Identified Constraints:**
1. **[Constraint 1]**
   - Type: [Human approval/External dependency/System limitation]
   - Impact: [Description]
   - Frequency: [How often this blocks work]

2. **[Constraint 2]**
   - Type: [Human approval/External dependency/System limitation]
   - Impact: [Description]
   - Frequency: [How often this blocks work]

---

### Recommendations

**High Priority (Immediate Action):**
1. **[Recommendation 1]**
   - Problem: [What's wrong]
   - Solution: [How to fix]
   - Impact: [Expected improvement]
   - Effort: [Low/Medium/High]
   - Timeline: [When to implement]

2. **[Recommendation 2]**
   - Problem: [What's wrong]
   - Solution: [How to fix]
   - Impact: [Expected improvement]
   - Effort: [Low/Medium/High]
   - Timeline: [When to implement]

**Medium Priority (This Month):**
1. **[Recommendation 3]**
   [Same structure]

**Low Priority (Future Optimization):**
1. **[Recommendation 4]**
   [Same structure]

---

### Process Improvements

**Quick Wins (< 1 hour to implement):**
- [ ] [Improvement 1]
- [ ] [Improvement 2]

**Strategic Changes (Require planning):**
- [ ] [Improvement 3]
- [ ] [Improvement 4]

---

### Metrics to Track

**Monitor These Metrics Weekly:**
- Average task completion time by category
- Tasks exceeding 2x expected time
- Time spent in Pending_Approval stage
- Number of stuck tasks (>48 hours in Processing)

**Success Indicators:**
- Approval time reduced by [Target]%
- Tasks exceeding threshold reduced by [Target]%
- Average completion time improved by [Target]%
```

### Step 5: Update Task

```yaml
status: completed
bottleneck_analysis_generated: true
analysis_period: "[Start] to [End]"
tasks_analyzed: [Count]
bottlenecks_identified: [Count]
total_delay_hours: [Hours]
```

Move to `vault/Done/`

## Output Format

### Complete Bottleneck Analysis:

```markdown
---
id: bottleneck_analysis_20260304
type: analytics
status: completed
analysis_period: "2026-02-24 to 2026-03-02"
tasks_analyzed: 18
bottlenecks_identified: 3
total_delay_hours: 36
---

# Task Bottleneck Analysis

**Period**: February 24 - March 2, 2026 (1 week)
**Generated**: 2026-03-04T11:00:00Z
**Tasks Analyzed**: 18 completed tasks

---

### Executive Summary

**Key Findings:**
- Approval workflow adds 24-hour average delay (affects 8 tasks)
- Social media posts take 3x longer than expected due to content creation
- 2 tasks stuck in Processing for >48 hours (need attention)

**Impact:**
- **Total Delay**: 36 hours across all tasks
- **Efficiency Loss**: 28% of time spent waiting vs productive work
- **Tasks Affected**: 10 tasks (56%) delayed beyond 2x threshold

---

### Bottlenecks Identified

#### 1. Approval Workflow Delay
**Severity**: High
**Impact**: 8 tasks affected, 24 hours total delay

**Description:**
Tasks requiring approval (invoices >$100, social media posts) wait an average of 24 hours in Pending_Approval folder before human review.

**Affected Tasks:**
- Invoice Client B ($2,500): Expected 5 min, Actual 24.5 hours, Delay 24+ hours
- Facebook post: Expected 10 min, Actual 18 hours, Delay 18 hours
- Instagram post: Expected 10 min, Actual 22 hours, Delay 22 hours

**Root Cause:**
Single approver (business owner) reviews tasks once per day, typically in morning. Tasks created after morning review wait until next day.

**Recommendation:**
1. Add secondary approver for routine items
2. Auto-approve invoices under $500 (currently $100)
3. Implement approval notifications (email/WhatsApp) for urgent items

**Expected Impact:**
Reduce approval time by 75% (from 24 hours to 6 hours average), save 18 hours/week

---

#### 2. Social Media Content Creation Time
**Severity**: Medium
**Impact**: 6 tasks affected, 8 hours total delay

**Description:**
Social media posts take 3x longer than expected (90 min vs 30 min) due to content drafting, image selection, and caption refinement.

**Affected Tasks:**
- Facebook post 1: Expected 30 min, Actual 85 min, Delay 55 min
- Instagram post 1: Expected 30 min, Actual 95 min, Delay 65 min
- LinkedIn post 1: Expected 30 min, Actual 75 min, Delay 45 min

**Root Cause:**
No content templates or image library. Each post created from scratch.

**Recommendation:**
1. Create content templates for common post types
2. Build image library with pre-approved visuals
3. Batch content creation (create 3-5 posts at once)

**Expected Impact:**
Reduce content creation time by 50% (from 90 min to 45 min), save 3 hours/week

---

#### 3. External Dependency Delays
**Severity**: Low
**Impact**: 2 tasks affected, 4 hours total delay

**Description:**
Tasks waiting for external responses (client approvals, vendor confirmations) have no automated follow-up.

**Affected Tasks:**
- Client D project: Waiting 48 hours for client approval
- Vendor quote: Waiting 36 hours for vendor response

**Root Cause:**
No automated follow-up system. Manual tracking required.

**Recommendation:**
1. Implement automated follow-up reminders (24-hour, 48-hour)
2. Set clear deadlines with clients/vendors
3. Have backup options for time-sensitive items

**Expected Impact:**
Reduce external dependency delays by 40%, save 2 hours/week

---

[... rest of sections ...]

---

### Recommendations

**High Priority (Immediate Action):**
1. **Increase Auto-Approval Threshold**
   - Problem: Too many low-value items require manual approval
   - Solution: Raise threshold from $100 to $500 for invoices
   - Impact: 60% fewer approval requests, 12 hours/week saved
   - Effort: Low (5 min config change)
   - Timeline: Implement today

2. **Add Approval Notifications**
   - Problem: Approver doesn't know when items need review
   - Solution: Send WhatsApp notification when approval needed
   - Impact: Reduce approval time from 24h to 6h average
   - Effort: Medium (2 hours to implement)
   - Timeline: Implement this week

**Medium Priority (This Month):**
1. **Create Content Templates**
   - Problem: Social media posts take 3x longer than expected
   - Solution: Build 10 content templates for common post types
   - Impact: 50% faster content creation, 3 hours/week saved
   - Effort: Medium (4 hours to create templates)
   - Timeline: Complete by end of month
```

## Quality Criteria

- **Accuracy**: Task timing data is correct
- **Completeness**: All major bottlenecks identified
- **Actionability**: Recommendations are specific and implementable
- **Prioritization**: Issues ranked by impact and effort
- **Clarity**: Easy to understand for non-technical audience
- **Measurability**: Success metrics defined

## Important Notes

- **Data Source**: Task files in vault with timestamps
- **Threshold**: Default 2x expected time (configurable)
- **Severity Levels**: High (>10 tasks or >20 hours delay), Medium (5-10 tasks or 10-20 hours), Low (<5 tasks or <10 hours)
- **Root Cause Analysis**: Goes beyond symptoms to identify underlying issues
- **Recommendations**: Include effort estimate and expected impact

## Success Criteria

- ✅ Task data retrieved and analyzed
- ✅ Bottlenecks identified with severity
- ✅ Root causes determined
- ✅ Delay patterns analyzed
- ✅ Stuck tasks identified
- ✅ Recommendations prioritized
- ✅ Impact estimates provided
- ✅ Report formatted clearly
- ✅ Task completed

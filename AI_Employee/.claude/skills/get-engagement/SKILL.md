---
name: "get-engagement"
description: "Retrieve and summarize social media engagement metrics from Facebook and Instagram. Use when task requires analyzing post performance, engagement statistics, or social media activity reports."
---

# Get Engagement Skill

## When to Use This Skill

Use this skill when:
- Task asks for social media engagement summary
- Need to analyze post performance
- Generating social media reports
- Task mentions "engagement", "social media stats", or "post performance"
- Weekly/monthly social media review

## Procedure

### Step 1: Identify Scope

1. Read task to determine:
   - **Platform**: Facebook, Instagram, or both
   - **Time Period**: Last week, last month, specific date range
   - **Metrics Needed**: Likes, comments, shares, reach, etc.
   - **Specific Posts**: All posts or specific post IDs

### Step 2: Query Engagement Data

```python
from src.actions.social_media_actions import get_engagement_summary

query_params = {
    "platform": "facebook|instagram|both",
    "start_date": "[YYYY-MM-DD]",
    "end_date": "[YYYY-MM-DD]",
    "post_ids": ["id1", "id2"] or None  # None for all posts
}

engagement_data = get_engagement_summary(query_params)
```

### Step 3: Format Engagement Report

Create summary in task file:

```markdown
## Social Media Engagement Report

**Period**: [Start Date] to [End Date]
**Generated**: [ISO timestamp]
**Platforms**: [Facebook/Instagram/Both]

### Overall Summary
- **Total Posts**: [Count]
- **Total Engagement**: [Likes + Comments + Shares]
- **Average Engagement per Post**: [Total / Posts]
- **Top Performing Post**: [Post with highest engagement]

### Facebook Engagement
- **Posts Published**: [Count]
- **Total Likes**: [Count]
- **Total Comments**: [Count]
- **Total Shares**: [Count]
- **Reach**: [People reached]
- **Engagement Rate**: [Engagement / Reach × 100]%

#### Top Facebook Posts
| Date | Post Summary | Likes | Comments | Shares | Total |
|------|--------------|-------|----------|--------|-------|
| [Date] | [Brief text] | [#] | [#] | [#] | [#] |

### Instagram Engagement
- **Posts Published**: [Count]
- **Total Likes**: [Count]
- **Total Comments**: [Count]
- **Total Saves**: [Count]
- **Reach**: [Accounts reached]
- **Engagement Rate**: [Engagement / Reach × 100]%

#### Top Instagram Posts
| Date | Post Summary | Likes | Comments | Saves | Total |
|------|--------------|-------|----------|-------|-------|
| [Date] | [Brief text] | [#] | [#] | [#] | [#] |

### Insights & Recommendations

**What's Working:**
- [Observation 1: e.g., "Posts with questions get 2x more comments"]
- [Observation 2: e.g., "Visual content performs better on Instagram"]

**Opportunities:**
- [Recommendation 1: e.g., "Post more during 6-9 PM for higher engagement"]
- [Recommendation 2: e.g., "Use more video content (higher reach)"]

**Action Items:**
- [Action 1: Specific next step]
- [Action 2: Specific next step]
```

### Step 4: Update Task

```yaml
status: completed
engagement_report_generated: true
total_posts_analyzed: [Count]
total_engagement: [Count]
report_period: "[Start] to [End]"
```

Move to `vault/Done/`

### Step 5: Update Dashboard

Add engagement summary to Dashboard:

```markdown
### Social Media Performance ([Period])
- **Total Posts**: [Count]
- **Total Engagement**: [Count]
- **Top Platform**: [Facebook/Instagram]
- **Engagement Rate**: [%]
```

## Output Format

### Complete Engagement Report:

```markdown
---
id: engagement_report_20260304
type: social_media
status: completed
engagement_report_generated: true
total_posts_analyzed: 12
total_engagement: 847
report_period: "2026-02-25 to 2026-03-04"
---

# Social Media Engagement Report

## Social Media Engagement Report

**Period**: February 25 - March 4, 2026 (1 week)
**Generated**: 2026-03-04T15:00:00Z
**Platforms**: Facebook + Instagram

### Overall Summary
- **Total Posts**: 12 (6 Facebook, 6 Instagram)
- **Total Engagement**: 847 (likes, comments, shares, saves)
- **Average Engagement per Post**: 70.6
- **Top Performing Post**: Instagram post about automation success (156 engagements)

### Facebook Engagement
- **Posts Published**: 6
- **Total Likes**: 234
- **Total Comments**: 45
- **Total Shares**: 12
- **Reach**: 1,847 people
- **Engagement Rate**: 15.8%

#### Top Facebook Posts
| Date | Post Summary | Likes | Comments | Shares | Total |
|------|--------------|-------|----------|--------|-------|
| Mar 2 | "Just helped another business..." | 67 | 12 | 4 | 83 |
| Feb 28 | "Automation tip: Start small..." | 52 | 9 | 3 | 64 |
| Mar 1 | "Client success story..." | 48 | 8 | 2 | 58 |

### Instagram Engagement
- **Posts Published**: 6
- **Total Likes**: 412
- **Total Comments**: 89
- **Total Saves**: 55
- **Reach**: 2,134 accounts
- **Engagement Rate**: 26.1%

#### Top Instagram Posts
| Date | Post Summary | Likes | Comments | Saves | Total |
|------|--------------|-------|----------|-------|-------|
| Mar 3 | "From chaos to clarity..." | 98 | 34 | 24 | 156 |
| Mar 1 | "15 hours saved infographic" | 87 | 21 | 15 | 123 |
| Feb 27 | "Behind the scenes..." | 76 | 18 | 9 | 103 |

### Insights & Recommendations

**What's Working:**
- Posts with specific numbers/results get 2.3x more engagement
- Questions in captions drive 3x more comments
- Instagram visual content outperforms Facebook text posts
- Posting between 6-8 PM gets highest engagement

**Opportunities:**
- Increase Instagram posting frequency (currently 6/week, could do 7-10/week)
- Use more video content (only 1 video this week, videos get 40% more reach)
- Respond to comments within 1 hour (increases future engagement)
- Cross-promote top Instagram posts to Facebook

**Action Items:**
- Create 2 video posts next week (one per platform)
- Post daily on Instagram during peak hours (6-8 PM)
- Set up comment response automation for common questions
- Analyze top-performing content themes for content calendar
```

## Quality Criteria

- **Accuracy**: Metrics are correct and verified
- **Completeness**: All requested platforms and periods covered
- **Insights**: Actionable observations provided
- **Clarity**: Data presented in easy-to-understand format
- **Recommendations**: Specific, actionable next steps

## Important Notes

- **Data Source**: Engagement data comes from Facebook/Instagram watchers
- **Metrics Tracked**: Likes, comments, shares (FB), saves (IG), reach
- **Engagement Rate**: (Total Engagement / Reach) × 100
- **Top Posts**: Ranked by total engagement (all metrics combined)
- **Insights**: Based on data patterns, not assumptions
- **Recommendations**: Specific and actionable

## Success Criteria

- ✅ Engagement data retrieved successfully
- ✅ All requested platforms covered
- ✅ Time period matches request
- ✅ Metrics calculated correctly
- ✅ Top posts identified
- ✅ Insights provided
- ✅ Recommendations are actionable
- ✅ Report formatted clearly
- ✅ Task completed
- ✅ Dashboard updated

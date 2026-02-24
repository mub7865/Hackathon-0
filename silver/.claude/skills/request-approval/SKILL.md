---
name: "request-approval"
description: "Create structured approval requests for sensitive actions by documenting the action, rationale, risks, and expected outcomes. Use when a task requires human review before execution due to financial, legal, or reputational implications."
---

# Request Approval Skill

## When to Use This Skill

Use this skill when:
- Task involves sensitive actions requiring human oversight
- Financial commitments or amounts > $500
- Email/message to new contacts
- LinkedIn posting (always requires approval)
- Payment actions or refunds
- Contract terms or legal commitments
- Actions with reputational risk
- Anything that cannot be easily undone

## Procedure

### Step 1: Analyze Action Sensitivity

1. Read the task file completely
2. Identify the specific action that needs approval:
   - What exactly will be done?
   - Who will it affect?
   - What are the consequences?
3. Determine sensitivity category:
   - **Financial**: Money involved
   - **Reputational**: Public-facing communication
   - **Legal**: Contractual or compliance implications
   - **Relationship**: New contact or sensitive relationship
   - **Irreversible**: Cannot be undone easily

### Step 2: Document the Request

Create a comprehensive approval request in the task file:

```markdown
## Approval Request

**Action Type**: [Financial/Reputational/Legal/Relationship/Irreversible]
**Requested**: [ISO timestamp]
**Expires**: [ISO timestamp - 24 hours from request]

### Proposed Action
[Clear, specific description of what will be done]

### Rationale
[Why this action is needed - business justification]

### Details
- **Who**: [Who will be affected]
- **What**: [Specific action details]
- **When**: [Timing/deadline if applicable]
- **Amount**: [If financial - exact amount]
- **Platform**: [Email/WhatsApp/LinkedIn/etc.]

### Risks
- **Risk 1**: [Potential negative outcome]
  - Mitigation: [How to minimize this risk]
- **Risk 2**: [Another potential issue]
  - Mitigation: [How to handle]

### Expected Outcome
[What success looks like - specific and measurable]

### Alternative Options
1. [Alternative approach 1]
2. [Alternative approach 2]
3. [Do nothing - consequences]

### Recommendation
[Your recommendation with reasoning]

---

**To Approve**: Move this file to `vault/Approved/`
**To Reject**: Move this file to `vault/Rejected/`
**To Modify**: Edit the "Proposed Action" section and re-request

**Note**: This approval request expires in 24 hours. After expiration, task will be moved to vault/Needs_Action for re-evaluation.
```

### Step 3: Update Task Metadata

Update task frontmatter with approval details:

```yaml
requires_approval: true
approval_reason: "[Specific reason]"
approval_requested: [ISO timestamp]
approval_expires: [ISO timestamp + 24 hours]
approval_category: [financial/reputational/legal/relationship/irreversible]
status: pending_approval
```

### Step 4: Move to Pending Approval

1. Move task file to `vault/Pending_Approval/`
2. Log the approval request:
   ```
   [TIMESTAMP] [TASK_ID] APPROVAL_REQUESTED: [Category] - [Brief description]
   ```
3. Update Dashboard with pending approval count

### Step 5: Monitor Approval Status

The orchestrator will check for approved/rejected tasks:

**If moved to vault/Approved/:**
- Task will be executed
- Action will be logged
- Task will move to vault/Done/

**If moved to vault/Rejected/:**
- Task will be logged as rejected
- No action will be taken
- Task stays in vault/Rejected/ for record

**If expires (24 hours):**
- Task moves back to vault/Needs_Action/
- Status updated to "approval_expired"
- Requires re-evaluation

## Output Format

### Complete Approval Request Example:

```markdown
## Approval Request

**Action Type**: Financial + Reputational
**Requested**: 2026-02-06T18:00:00Z
**Expires**: 2026-02-07T18:00:00Z

### Proposed Action
Post to LinkedIn promoting our automation services with a special offer: "First month free for new clients (up to $1,500 value)".

### Rationale
We have capacity for 3 new clients this month. This promotion can help fill those slots quickly while building brand awareness. The offer is time-limited (this month only) to create urgency.

### Details
- **Who**: LinkedIn professional network (~500 connections)
- **What**: Promotional post with limited-time offer
- **When**: Post today, offer valid through end of month
- **Amount**: Up to $1,500 per client (3 clients max = $4,500 total potential cost)
- **Platform**: LinkedIn

### Risks
- **Risk 1**: Offer may attract price-sensitive clients who won't convert to paying customers
  - Mitigation: Include qualification criteria (minimum project scope)
- **Risk 2**: Current clients may feel they're not getting same value
  - Mitigation: Frame as "new client onboarding offer" not a discount
- **Risk 3**: May set expectation for future discounts
  - Mitigation: Clearly state "limited time, this month only"

### Expected Outcome
- 100+ post engagements
- 10-15 qualified inquiries
- 2-3 new client signups
- Increased brand visibility

### Alternative Options
1. **Smaller offer**: First week free instead of month (lower risk, lower reward)
2. **Referral program**: Offer discount to existing clients who refer (builds loyalty)
3. **Do nothing**: Continue with current lead generation (slower growth)

### Recommendation
Approve with modification: Change to "First 2 weeks free" to reduce financial exposure while still providing strong incentive. This limits potential cost to $750 per client ($2,250 total).

---

**To Approve**: Move this file to `vault/Approved/`
**To Reject**: Move this file to `vault/Rejected/`
**To Modify**: Edit the "Proposed Action" section and re-request

**Note**: This approval request expires in 24 hours. After expiration, task will be moved to vault/Needs_Action for re-evaluation.
```

## Quality Criteria

- **Clarity**: Action is described specifically, not vaguely
- **Completeness**: All relevant details included
- **Risk Assessment**: Potential issues identified with mitigations
- **Alternatives**: Other options presented for comparison
- **Measurability**: Expected outcomes are specific and measurable
- **Justification**: Clear business rationale provided
- **Actionability**: Human can make informed decision quickly

## Example Input

```markdown
---
id: task_linkedin_promo_20260206
source: file
type: linkedin
priority: high
---

# Task: LinkedIn Promotion Post

Create and post to LinkedIn about our new automation service package. Mention special pricing for early adopters.
```

## Example Output

Task moved to `vault/Pending_Approval/` with:

```yaml
---
id: task_linkedin_promo_20260206
source: file
type: linkedin
priority: high
requires_approval: true
approval_reason: "LinkedIn post with pricing information"
approval_requested: 2026-02-06T18:00:00Z
approval_expires: 2026-02-07T18:00:00Z
approval_category: reputational
status: pending_approval
---

[Full approval request as shown in Output Format above]
```

## Important Notes

- **Be specific**: Vague approval requests lead to delays
- **Include risks**: Show you've thought through potential issues
- **Provide alternatives**: Give human options to choose from
- **Set expiration**: Prevents stale approvals from being executed
- **Document reasoning**: Help human understand why approval needed
- **Make it actionable**: Human should be able to decide quickly
- **Consider urgency**: High-priority items need faster turnaround

## Success Criteria

Approval request is successful when:
- ✅ Action clearly described with all details
- ✅ Business rationale provided
- ✅ Risks identified with mitigations
- ✅ Expected outcomes specified
- ✅ Alternatives presented
- ✅ Recommendation included
- ✅ Task moved to Pending_Approval
- ✅ Metadata updated correctly
- ✅ Expiration set (24 hours)
- ✅ Action logged
- ✅ Dashboard updated

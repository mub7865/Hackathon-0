---
name: "facebook-post"
description: "Create and post content to Facebook using browser automation with human approval workflow. Use when task requires posting business updates, promotions, or engagement content to Facebook."
---

# Facebook Post Skill

## When to Use This Skill

Use this skill when:
- Task involves posting to Facebook
- Business update or announcement needs sharing
- Marketing content for Facebook audience
- Task mentions "Facebook post", "FB post", or "post to Facebook"
- Social media presence maintenance

**IMPORTANT**: ALL Facebook posts require human approval before publishing.

## Procedure

### Step 1: Understand Post Objective

1. Read task requirements
2. Identify post goal:
   - **Brand Awareness**: Share company updates
   - **Engagement**: Start conversations
   - **Promotion**: Highlight products/services
   - **Community Building**: Connect with audience
3. Read `vault/Company_Handbook.md` for brand voice

### Step 2: Draft Post Content

Create post following Facebook best practices:

**Content Guidelines:**
- **Length**: 40-80 words (optimal engagement)
- **Tone**: Conversational and authentic
- **First Line**: Hook attention immediately
- **Formatting**: Short paragraphs, emojis (1-3 max)
- **CTA**: Clear call-to-action
- **Hashtags**: 1-3 relevant tags (optional on Facebook)

**Avoid:**
- Overly promotional language
- Controversial topics
- Negative content
- Unverified claims

### Step 3: Create Approval Request

```markdown
## Facebook Post Draft (Awaiting Approval)

**Objective**: [Brand awareness/Engagement/Promotion]
**Target Audience**: [Who this is for]
**Draft Created**: [ISO timestamp]

### Post Content:

[Full post text with formatting and emojis]

### Media:
[Image/Video description if applicable]

### Expected Outcome:
- [Engagement target: likes, comments, shares]
- [Business goal: leads, awareness, etc.]

### Posting Schedule:
**Recommended Time**: [Best time based on audience activity]

---

**To Approve**: Move to vault/Approved/ to post
**To Reject**: Move to vault/Rejected/
```

### Step 4: Update Task Metadata

```yaml
requires_approval: true
approval_reason: "Facebook posts always require approval"
platform: facebook
post_objective: [objective]
status: pending_approval
```

### Step 5: Move to Pending Approval

Move task to `vault/Pending_Approval/`

### Step 6: Post-Approval Publishing

**When moved to vault/Approved/:**

1. Publish to Facebook:
   ```python
   from src.actions.social_media_actions import post_to_facebook

   result = post_to_facebook(post_data)
   ```

2. Log action:
   ```
   [TIMESTAMP] [TASK_ID] FACEBOOK_POST_PUBLISHED: [Brief summary]
   ```

3. Update task:
   ```yaml
   status: completed
   posted: true
   post_url: [Facebook post URL]
   posted_at: [ISO timestamp]
   ```

4. Move to `vault/Done/`

## Output Format

### Draft Post (Pending Approval):

```markdown
---
id: facebook_post_20260304
type: social_media
platform: facebook
requires_approval: true
status: pending_approval
---

# Facebook Post Draft

## Facebook Post (Awaiting Approval)

**Objective**: Brand Awareness + Engagement
**Target Audience**: Small business owners
**Draft Created**: 2026-03-04T10:00:00Z

### Post Content:

Just helped another small business save 15 hours per week through automation! 🚀

The secret? Start small. Automate one repetitive task, measure the impact, then scale.

What's one task you wish you could automate? Drop a comment below! 👇

#SmallBusiness #Automation #Productivity

### Expected Outcome:
- 50+ engagements (likes, comments, shares)
- 5-10 comments with automation questions
- Establish thought leadership

### Posting Schedule:
**Recommended Time**: Today at 2:00 PM (peak engagement time)

---

**To Approve**: Move to vault/Approved/ to post
**To Reject**: Move to vault/Rejected/
```

## Quality Criteria

- **Authenticity**: Genuine, not overly promotional
- **Engagement**: Encourages interaction
- **Clarity**: Easy to understand
- **Brand Alignment**: Matches company voice
- **Value**: Provides insight or benefit
- **CTA**: Clear next step for readers

## Success Criteria

- ✅ Post follows Facebook best practices
- ✅ Aligns with brand voice
- ✅ Clear objective identified
- ✅ Approval request created
- ✅ Task moved to Pending_Approval
- ✅ Expected outcomes specified
- ✅ Action logged

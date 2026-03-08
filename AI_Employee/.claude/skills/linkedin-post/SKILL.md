---
name: "linkedin-post"
description: "Draft professional LinkedIn posts for business promotion and sales generation, following brand voice and engagement best practices. Use when task requires creating LinkedIn content to generate business leads. ALWAYS requires human approval before posting."
---

# LinkedIn Post Skill

## When to Use This Skill

Use this skill when:
- Task involves creating LinkedIn content
- Goal is business promotion or sales generation
- Need to share company updates or achievements
- Want to establish thought leadership
- Task explicitly mentions LinkedIn posting

**IMPORTANT**: LinkedIn posts ALWAYS require human approval before posting.

## Procedure

### Step 1: Understand Post Objective

1. Read the task requirements carefully
2. Identify post goal:
   - **Lead Generation**: Attract potential clients
   - **Brand Awareness**: Share company values/mission
   - **Thought Leadership**: Share insights/expertise
   - **Product/Service Promotion**: Highlight offerings
   - **Engagement**: Start conversations
3. Read `vault/Company_Handbook.md` for:
   - Brand voice guidelines
   - Target audience
   - Key messaging points
   - Topics to avoid

### Step 2: Research Context

1. Check `vault/Dashboard.md` for recent business activities
2. Review `vault/Done/` for recent accomplishments
3. Identify relevant achievements or insights to share
4. Consider current business goals from Company_Handbook

### Step 3: Draft Post Content

Create post following LinkedIn best practices:

**Structure:**
```
[Hook - First line that grabs attention]

[Context - Brief background or story]

[Value - Key insight or benefit]

[Call to Action - What you want readers to do]

[Hashtags - 3-5 relevant tags]
```

**Content Guidelines:**
- **Length**: 150-300 words (optimal engagement)
- **Tone**: Professional but conversational
- **First Line**: Must hook attention (people decide in 2 seconds)
- **Formatting**: Use line breaks for readability
- **Emojis**: 1-2 maximum, only if brand-appropriate
- **Hashtags**: 3-5 relevant, industry-specific tags
- **CTA**: Clear action (comment, DM, visit website)

**Avoid:**
- Overly salesy language
- Jargon without explanation
- Negative or controversial topics
- Personal complaints
- Unverified claims

### Step 4: Optimize for Engagement

Check that post has:
- ✅ Attention-grabbing first line
- ✅ Clear value proposition
- ✅ Conversational tone
- ✅ Proper formatting (line breaks)
- ✅ Relevant hashtags
- ✅ Clear call-to-action
- ✅ No spelling/grammar errors
- ✅ Aligns with brand voice

### Step 5: Create Approval Request

**LinkedIn posts ALWAYS require approval.**

1. Create approval request in task file:
   ```markdown
   ## Draft LinkedIn Post (Awaiting Approval)

   **Objective**: [Lead generation/Brand awareness/etc.]
   **Target Audience**: [Who this is for]
   **Draft Created**: [timestamp]

   ### Post Content:
   [Full post text with formatting]

   ### Hashtags:
   #hashtag1 #hashtag2 #hashtag3

   ### Expected Outcome:
   [What success looks like - engagement, leads, etc.]

   ---
   **Approval Required**: Move to vault/Approved/ to post
   **To Reject**: Move to vault/Rejected/
   ```

2. Update task frontmatter:
   ```yaml
   requires_approval: true
   approval_reason: "LinkedIn posts always require approval"
   draft_ready: true
   post_objective: [objective]
   ```

3. Move task to `vault/Pending_Approval/`

4. Log approval request:
   ```
   [TIMESTAMP] [TASK_ID] LINKEDIN_POST_DRAFT: Awaiting approval - [objective]
   ```

### Step 6: Update Dashboard

Add to Recent Activity:
```
| [Time] | LinkedIn | Post Draft | Pending Approval | [Brief summary] |
```

## Output Format

### Draft Post in Approval Request:

```markdown
## Draft LinkedIn Post (Awaiting Approval)

**Objective**: Lead Generation
**Target Audience**: Small business owners seeking automation
**Draft Created**: 2026-02-06T16:00:00Z

### Post Content:

Just completed our 100th automation project! 🚀

Over the past year, we've helped small businesses save an average of 15 hours per week through intelligent automation.

The most common pain point? Manual data entry and repetitive email responses.

Our approach:
→ Identify high-impact repetitive tasks
→ Build custom automation workflows
→ Train teams on the new systems
→ Measure time savings

Result: Teams focus on growth, not busywork.

Curious about automation for your business? Drop a comment or DM me - happy to share insights.

#BusinessAutomation #Productivity #SmallBusiness #AI #Efficiency

### Expected Outcome:
- 50+ engagements (likes, comments)
- 5-10 DMs from potential clients
- Establish thought leadership in automation space

---
**Approval Required**: Move to vault/Approved/ to post
**To Reject**: Move to vault/Rejected/
```

## Quality Criteria

- **Hook**: First line makes you want to read more
- **Value**: Clear benefit or insight provided
- **Authenticity**: Genuine, not overly promotional
- **Clarity**: Easy to understand, no jargon
- **Formatting**: Readable with line breaks
- **CTA**: Clear next step for readers
- **Professionalism**: Maintains brand reputation
- **Relevance**: Aligns with business goals

## Example Input

```markdown
---
id: task_linkedin_promo_20260206
source: file
type: linkedin
priority: medium
---

# Task: Create LinkedIn Post

Create a LinkedIn post to promote our AI automation services and generate leads. Focus on recent success with client projects.
```

## Example Output

```markdown
## Draft LinkedIn Post (Awaiting Approval)

**Objective**: Lead Generation & Service Promotion
**Target Audience**: Business owners struggling with manual processes
**Draft Created**: 2026-02-06T16:00:00Z

### Post Content:

"We're spending 20 hours a week on emails" - a client told me last month.

Today? They spend 2 hours. The other 18? Growing their business.

Here's what we automated:
• Email triage and categorization
• Customer inquiry responses
• Invoice generation and follow-ups
• Meeting scheduling

The secret isn't replacing humans - it's freeing them to do what humans do best: build relationships and solve complex problems.

Automation isn't about doing less. It's about doing what matters more.

What's one task you wish you could automate? Let's discuss in the comments.

#BusinessAutomation #AIForBusiness #Productivity #SmallBusiness #Efficiency

### Expected Outcome:
- 100+ engagements
- 10-15 qualified leads via DM
- Position as automation expert

---
**Approval Required**: Move to vault/Approved/ to post
**To Reject**: Move to vault/Rejected/

**Note**: This post emphasizes value and results, not just features. The hook is relatable, and the CTA invites engagement.
```

## Important Notes

- **NEVER post to LinkedIn without approval** - this is a hard rule
- Always include expected outcomes in approval request
- Focus on value, not just promotion
- Use storytelling when possible (more engaging)
- First line is critical - spend time on it
- Keep paragraphs short (2-3 lines max)
- Test hashtags for relevance (not just popularity)
- Consider timing (business hours get more engagement)

## Success Criteria

LinkedIn post draft is successful when:
- ✅ Post follows best practices (hook, value, CTA)
- ✅ Aligns with brand voice from Company_Handbook
- ✅ Clear objective and target audience identified
- ✅ Proper formatting for readability
- ✅ Relevant hashtags included
- ✅ Approval request created with all details
- ✅ Task moved to Pending_Approval
- ✅ Expected outcomes specified
- ✅ Action logged

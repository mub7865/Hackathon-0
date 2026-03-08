---
name: "instagram-post"
description: "Create and post visual content to Instagram using browser automation with human approval workflow. Use when task requires posting business updates, visual content, or engagement posts to Instagram. REQUIRES IMAGE."
---

# Instagram Post Skill

## When to Use This Skill

Use this skill when:
- Task involves posting to Instagram
- Visual content or business update needs sharing
- Marketing content for Instagram audience
- Task mentions "Instagram post", "IG post", or "post to Instagram"
- Social media visual presence maintenance

**IMPORTANT**:
- ALL Instagram posts require human approval before publishing
- Instagram posts MUST include an image (required by platform)

## Procedure

### Step 1: Understand Post Objective

1. Read task requirements
2. Identify post goal:
   - **Brand Awareness**: Showcase company/products
   - **Engagement**: Visual storytelling
   - **Promotion**: Highlight offerings
   - **Community**: Connect with followers
3. Read `vault/Company_Handbook.md` for brand guidelines

### Step 2: Verify Image Availability

**Instagram requires an image - this is mandatory**

1. Check if image path is provided in task
2. Verify image exists and is accessible
3. Validate image format (JPG, PNG)
4. If no image: Request image or skip post

### Step 3: Draft Post Caption

Create caption following Instagram best practices:

**Content Guidelines:**
- **Length**: 125-150 characters (optimal) or longer for storytelling
- **Tone**: Visual, authentic, conversational
- **First Line**: Hook attention (shows in feed preview)
- **Formatting**: Line breaks for readability
- **Emojis**: 3-5 emojis (Instagram-friendly)
- **Hashtags**: 5-10 relevant tags (research trending tags)
- **CTA**: Clear call-to-action

**Avoid:**
- Text-heavy captions without visual appeal
- Too many hashtags (looks spammy)
- Controversial or negative content
- Unverified claims

### Step 4: Create Approval Request

```markdown
## Instagram Post Draft (Awaiting Approval)

**Objective**: [Brand awareness/Engagement/Promotion]
**Target Audience**: [Who this is for]
**Draft Created**: [ISO timestamp]

### Image:
**Path**: [Full path to image file]
**Description**: [What the image shows]

### Caption:

[Full caption text with formatting and emojis]

### Hashtags:
#hashtag1 #hashtag2 #hashtag3 #hashtag4 #hashtag5

### Expected Outcome:
- [Engagement target: likes, comments, saves]
- [Business goal: brand awareness, leads, etc.]

### Posting Schedule:
**Recommended Time**: [Best time based on audience activity]

---

**To Approve**: Move to vault/Approved/ to post
**To Reject**: Move to vault/Rejected/

**Note**: Image must be available at specified path for posting.
```

### Step 5: Update Task Metadata

```yaml
requires_approval: true
approval_reason: "Instagram posts always require approval"
platform: instagram
post_objective: [objective]
image_path: "[Full path to image]"
status: pending_approval
```

### Step 6: Move to Pending Approval

Move task to `vault/Pending_Approval/`

### Step 7: Post-Approval Publishing

**When moved to vault/Approved/:**

1. Verify image still exists
2. Publish to Instagram:
   ```python
   from src.actions.social_media_actions import post_to_instagram

   post_data = {
       "caption": "[Caption text]",
       "image_path": "[Path to image]",
       "hashtags": ["tag1", "tag2", ...]
   }

   result = post_to_instagram(post_data)
   ```

3. Log action:
   ```
   [TIMESTAMP] [TASK_ID] INSTAGRAM_POST_PUBLISHED: [Brief summary]
   ```

4. Update task:
   ```yaml
   status: completed
   posted: true
   post_url: [Instagram post URL if available]
   posted_at: [ISO timestamp]
   ```

5. Move to `vault/Done/`

## Output Format

### Draft Post (Pending Approval):

```markdown
---
id: instagram_post_20260304
type: social_media
platform: instagram
requires_approval: true
image_path: "D:/Hackathons/hackathon-0/silver/vault/images/automation_success.jpg"
status: pending_approval
---

# Instagram Post Draft

## Instagram Post (Awaiting Approval)

**Objective**: Brand Awareness + Engagement
**Target Audience**: Small business owners, entrepreneurs
**Draft Created**: 2026-03-04T10:00:00Z

### Image:
**Path**: D:/Hackathons/hackathon-0/silver/vault/images/automation_success.jpg
**Description**: Infographic showing "15 hours saved per week" with automation icons

### Caption:

From chaos to clarity ✨

We helped another small business automate their repetitive tasks. Result? 15 hours back every week. ⏰

That's 15 hours for:
→ Growing the business 📈
→ Connecting with clients 🤝
→ Actually taking a break 🌴

Automation isn't about replacing humans. It's about freeing them to do what they do best.

What would you do with 15 extra hours? 💭

### Hashtags:
#SmallBusiness #Automation #Productivity #BusinessGrowth #Entrepreneur #TimeManagement #WorkSmarter #BusinessTips #Efficiency #StartupLife

### Expected Outcome:
- 100+ likes
- 10-20 comments
- 5-10 saves (high-value metric)
- Establish thought leadership in automation space

### Posting Schedule:
**Recommended Time**: Today at 6:00 PM (peak Instagram engagement time)

---

**To Approve**: Move to vault/Approved/ to post
**To Reject**: Move to vault/Rejected/

**Note**: Image must be available at specified path for posting.
```

## Quality Criteria

- **Visual Appeal**: Image is high-quality and relevant
- **Caption Hook**: First line grabs attention
- **Authenticity**: Genuine, not overly promotional
- **Engagement**: Encourages interaction (questions, CTAs)
- **Hashtags**: Relevant and researched (not generic)
- **Brand Alignment**: Matches company visual identity
- **Value**: Provides insight or inspiration

## Important Notes

- **Image is MANDATORY** - Instagram posts cannot be text-only
- **Image format**: JPG or PNG (Instagram requirement)
- **Image size**: Recommended 1080x1080 (square) or 1080x1350 (portrait)
- **Caption length**: First 125 characters show in feed (make them count)
- **Hashtags**: 5-10 is optimal (30 max but looks spammy)
- **Timing**: Post during peak engagement hours (6-9 PM typically)
- **Screen time popup**: Automation handles Instagram's screen time limit popup
- **Session persistence**: Uses saved Instagram session for posting

## Success Criteria

- ✅ Post follows Instagram best practices
- ✅ Image is available and valid format
- ✅ Caption has strong hook (first line)
- ✅ Hashtags are relevant and researched
- ✅ Aligns with brand visual identity
- ✅ Clear objective identified
- ✅ Approval request created
- ✅ Task moved to Pending_Approval
- ✅ Expected outcomes specified
- ✅ Action logged

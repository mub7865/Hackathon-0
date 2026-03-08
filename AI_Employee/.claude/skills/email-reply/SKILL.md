---
name: "email-reply"
description: "Draft professional email replies based on Company Handbook tone guidelines, considering context and relationship with sender. Use when processing email tasks that require responses to known contacts."
---

# Email Reply Skill

## When to Use This Skill

Use this skill when:
- Task type is `email` from Gmail watcher
- Email requires a response
- Sender is a known contact (not first-time communication)
- Task is classified as SIMPLE (not sensitive)
- Company_Handbook.md has tone/style guidelines

## Procedure

### Step 1: Analyze Email Context

1. Read the original email from task file:
   - Sender email address
   - Subject line
   - Email body content
   - Any attachments mentioned
2. Read `vault/Company_Handbook.md` for:
   - Tone guidelines (professional, friendly, formal)
   - Response templates
   - Signature format
3. Check if sender is known:
   - Search `vault/Done/` for previous emails from this address
   - If found = known contact (safe to reply)
   - If not found = new contact (requires approval)

### Step 2: Determine Response Type

Classify the email request:

**INFORMATION REQUEST**: Sender asking for data/details
- Response: Provide requested information clearly

**ACTION REQUEST**: Sender asking you to do something
- Response: Confirm action or explain timeline

**QUESTION**: Sender has a question
- Response: Answer directly and completely

**ACKNOWLEDGMENT**: Sender sharing information
- Response: Acknowledge receipt and next steps

### Step 3: Draft Reply

Create reply following this structure:

```
Subject: Re: [Original Subject]

[Greeting based on relationship]

[Opening line - acknowledge their message]

[Main content - address their request/question]

[Closing - next steps or call to action]

[Sign-off]
[Your name/title from Company_Handbook]
```

**Tone Guidelines from Company_Handbook:**
- Professional and courteous
- Concise (avoid jargon)
- Action-oriented phrasing
- Use active voice
- Address user directly

### Step 4: Validate Reply Quality

Check that reply has:
- ✅ Clear subject line
- ✅ Appropriate greeting
- ✅ Addresses all points from original email
- ✅ Specific next steps or timeline
- ✅ Professional tone matching Company_Handbook
- ✅ Proper signature
- ✅ No spelling/grammar errors

### Step 5: Execute or Request Approval

**If sender is KNOWN contact:**
1. Log the reply to `vault/Logs/email-actions-[date].log`:
   ```
   [TIMESTAMP] [EMAIL_ID] REPLY_SENT: To [sender] - [subject]
   ```
2. Save reply to task file under "## Reply Sent" section
3. Update task frontmatter: `status: done`, `reply_sent: [timestamp]`
4. Move task to `vault/Done/`

**If sender is NEW contact:**
1. Add reply as draft to task file under "## Draft Reply"
2. Update frontmatter:
   ```yaml
   requires_approval: true
   approval_reason: "New contact - first email reply"
   draft_ready: true
   ```
3. Move to `vault/Pending_Approval/`
4. DO NOT send email yet

### Step 6: Update Dashboard

Add to Recent Activity:
```
| [Time] | Gmail | Email Reply | Sent/Pending | To: [sender name] |
```

## Output Format

### For Known Contacts (Auto-sent):
```markdown
## Reply Sent

**To**: sender@example.com
**Subject**: Re: Original Subject
**Sent**: 2026-02-06T15:30:00Z

[Full reply text]

---
Status: Sent automatically (known contact)
```

### For New Contacts (Approval Required):
```markdown
## Draft Reply (Awaiting Approval)

**To**: newsender@example.com
**Subject**: Re: Original Subject
**Draft Created**: 2026-02-06T15:30:00Z

[Full reply text]

---
Status: Pending approval (new contact)
Reason: First communication with this sender
```

## Quality Criteria

- **Completeness**: All points from original email addressed
- **Clarity**: Response is clear and unambiguous
- **Tone**: Matches Company_Handbook guidelines
- **Professionalism**: No casual language unless appropriate
- **Actionability**: Clear next steps provided
- **Accuracy**: Information provided is correct
- **Brevity**: Concise without being curt

## Example Input

```markdown
---
id: email_abc123_20260206
source: gmail
type: email
email_from: client@example.com
email_subject: Invoice Request
---

## Email Content

**From**: client@example.com
**Subject**: Invoice Request

Hi,

Can you send me the invoice for January services?

Thanks,
John
```

## Example Output (Known Contact)

```markdown
## Reply Sent

**To**: client@example.com
**Subject**: Re: Invoice Request
**Sent**: 2026-02-06T15:30:00Z

Hi John,

Thank you for reaching out. I'll send you the January invoice right away.

The invoice for January services ($1,500) will be in your inbox within the next hour. It covers the consulting work we completed from January 1-31.

Please let me know if you have any questions about the charges.

Best regards,
[Your Name]
[Your Title]

---
Status: Sent automatically (known contact)
Log: 2026-02-06 15:30:00 email_abc123 REPLY_SENT: To client@example.com - Invoice Request
```

## Important Notes

- ALWAYS check if sender is known before auto-sending
- NEVER send to new contacts without approval
- Follow Company_Handbook tone guidelines strictly
- Keep replies concise but complete
- Include clear next steps
- Log every reply sent

## Success Criteria

Email reply is successful when:
- ✅ All points from original email addressed
- ✅ Tone matches Company_Handbook guidelines
- ✅ Known/new contact check performed
- ✅ Reply sent (known) or approval requested (new)
- ✅ Action logged
- ✅ Task moved to appropriate folder
- ✅ Dashboard updated

---
name: "whatsapp-reply"
description: "Draft professional WhatsApp replies to urgent business messages, maintaining appropriate tone for the platform while following Company Handbook guidelines. Use when processing WhatsApp tasks with urgent keywords that require responses."
---

# WhatsApp Reply Skill

## When to Use This Skill

Use this skill when:
- Task type is `whatsapp` from WhatsApp watcher
- Message contains urgent keywords (urgent, asap, invoice, payment, help)
- Message requires a business response
- Sender is a known contact or client

**IMPORTANT**: WhatsApp replies with commitments (promises, deadlines, payments) require approval.

## Procedure

### Step 1: Analyze Message Context

1. Read the WhatsApp message from task file:
   - Sender name/number
   - Message text
   - Timestamp
   - Whether it's from a group or individual
   - Keywords that triggered the watcher
2. Read `vault/Company_Handbook.md` for:
   - WhatsApp communication guidelines
   - Response tone (professional but friendly)
   - Escalation rules
3. Check message urgency level:
   - **HIGH**: Contains "urgent", "asap", "emergency"
   - **MEDIUM**: Contains "invoice", "payment", "help"
   - **LOW**: General inquiry

### Step 2: Classify Message Type

Determine what the message is about:

**INFORMATION REQUEST**: Asking for details/status
- Response: Provide information clearly and concisely

**URGENT ISSUE**: Problem that needs immediate attention
- Response: Acknowledge and provide timeline

**PAYMENT/INVOICE**: Financial matter
- Response: Confirm details (REQUIRES APPROVAL if commitment)

**GENERAL INQUIRY**: Question about services/products
- Response: Answer and offer to help further

**COMPLAINT**: Issue with service/product
- Response: Apologize, acknowledge, propose solution

### Step 3: Draft Reply

Create reply following WhatsApp best practices:

**Structure:**
```
[Greeting - Hi [Name]]

[Acknowledgment - Thanks for reaching out / I understand]

[Response - Direct answer to their question/concern]

[Next Steps - What happens next]

[Closing - Let me know if you need anything else]
```

**WhatsApp-Specific Guidelines:**
- **Tone**: Professional but conversational (less formal than email)
- **Length**: Keep it brief (WhatsApp is for quick communication)
- **Formatting**: Use line breaks, avoid long paragraphs
- **Emojis**: 1-2 if appropriate for relationship (✅ 👍 for confirmations)
- **Response Time**: Acknowledge quickly, even if full answer takes time
- **Clarity**: Be direct and clear (no corporate jargon)

### Step 4: Determine if Approval Needed

**REQUIRES APPROVAL if reply includes:**
- Financial commitments (payment amounts, invoice promises)
- Specific deadlines or delivery dates
- Pricing information
- Contract terms or agreements
- Refunds or compensation
- New service offerings

**SAFE TO SEND if reply is:**
- Acknowledging receipt
- Providing general information
- Answering simple questions
- Confirming already-agreed details
- Offering to help

### Step 5: Execute or Request Approval

**If SAFE (no commitments):**
1. Log the reply to `vault/Logs/whatsapp-actions-[date].log`:
   ```
   [TIMESTAMP] [TASK_ID] WHATSAPP_REPLY_SENT: To [sender] - [brief summary]
   ```
2. Save reply to task file under "## Reply Sent" section
3. Update task frontmatter: `status: done`, `reply_sent: [timestamp]`
4. Move task to `vault/Done/`

**If REQUIRES APPROVAL (has commitments):**
1. Add reply as draft to task file under "## Draft Reply"
2. Update frontmatter:
   ```yaml
   requires_approval: true
   approval_reason: "[Specific reason - e.g., 'Contains payment commitment']"
   draft_ready: true
   commitment_type: "[payment/deadline/pricing/etc.]"
   ```
3. Move to `vault/Pending_Approval/`
4. DO NOT send message yet

### Step 6: Update Dashboard

Add to Recent Activity:
```
| [Time] | WhatsApp | Reply | Sent/Pending | [Sender name] - [Brief summary] |
```

## Output Format

### For Safe Messages (Auto-sent):
```markdown
## Reply Sent

**To**: John Doe (+1234567890)
**Sent**: 2026-02-06T17:00:00Z
**Message Type**: Information Request

Hi John,

Thanks for reaching out!

The project status: We're on track for delivery next week as planned. I'll send you a detailed update by Friday.

Let me know if you need anything else! 👍

---
Status: Sent automatically (no commitments made)
Log: 2026-02-06 17:00:00 whatsapp_abc123 REPLY_SENT: To John Doe - Project status update
```

### For Messages Requiring Approval:
```markdown
## Draft Reply (Awaiting Approval)

**To**: Sarah Client (+9876543210)
**Draft Created**: 2026-02-06T17:00:00Z
**Message Type**: Payment Request
**Commitment**: Invoice delivery promise

Hi Sarah,

Thanks for the reminder!

I'll send you the January invoice by end of day today. The amount will be $1,500 for the consulting services.

Let me know if you have any questions!

---
Status: Pending approval
Reason: Contains payment amount and delivery deadline
Commitment Type: Invoice delivery + amount disclosure
```

## Quality Criteria

- **Clarity**: Message is clear and unambiguous
- **Brevity**: Concise without being curt (WhatsApp style)
- **Tone**: Professional but friendly (not stiff)
- **Responsiveness**: Addresses the urgent concern directly
- **Actionability**: Clear next steps provided
- **Appropriateness**: Matches relationship with sender
- **Safety**: No unauthorized commitments made

## Example Input

```markdown
---
id: whatsapp_xyz789_20260206
source: whatsapp
type: whatsapp
status: pending
priority: high
created: 2026-02-06T16:45:00Z
sender_name: John Client
message_text: "Hi! This is urgent - can you send me the invoice for last month? Need it ASAP for accounting."
keywords_matched: ["urgent", "asap", "invoice"]
---

## WhatsApp Message

**From**: John Client
**Time**: 2026-02-06 16:45:00
**Keywords**: urgent, asap, invoice

Message:
"Hi! This is urgent - can you send me the invoice for last month? Need it ASAP for accounting."
```

## Example Output (Requires Approval)

```markdown
## Draft Reply (Awaiting Approval)

**To**: John Client
**Draft Created**: 2026-02-06T16:50:00Z
**Message Type**: Invoice Request (Urgent)
**Commitment**: Invoice delivery promise

Hi John,

Got it - I understand the urgency!

I'll prepare and send you last month's invoice within the next 2 hours. It'll be for $1,500 covering the consulting work from January 1-31.

You'll have it in your email before end of business today. ✅

Let me know if you need anything else!

---
Status: Pending approval
Reason: Contains specific delivery timeline (2 hours) and amount ($1,500)
Commitment Type: Deadline commitment + financial disclosure

**Approval Required**: Move to vault/Approved/ to send
**To Reject**: Move to vault/Rejected/ and I'll draft alternative response
```

## Important Notes

- **Speed matters on WhatsApp** - acknowledge quickly even if full answer takes time
- **Be conversational** - WhatsApp is less formal than email
- **Use emojis sparingly** - only if appropriate for relationship
- **Keep it brief** - long messages are hard to read on mobile
- **NEVER make commitments without approval** - deadlines, amounts, promises
- **Check Company_Handbook** for specific WhatsApp guidelines
- **Consider relationship** - adjust tone based on how well you know sender

## Success Criteria

WhatsApp reply is successful when:
- ✅ Urgent concern addressed directly
- ✅ Tone is professional but friendly
- ✅ Message is brief and clear
- ✅ Commitment check performed
- ✅ Reply sent (safe) or approval requested (commitments)
- ✅ Action logged
- ✅ Task moved to appropriate folder
- ✅ Dashboard updated

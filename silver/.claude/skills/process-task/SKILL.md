---
name: "process-task"
description: "Analyze task files from vault/Needs_Action folder, classify them as simple/complex/sensitive, and route them appropriately by creating plans, executing actions, or requesting approval. Use when orchestrator detects new task files that need autonomous processing."
---

# Process Task Skill

## When to Use This Skill

Use this skill when:
- New task files appear in `vault/Needs_Action/` folder
- Orchestrator triggers task processing
- You need to autonomously handle incoming tasks from watchers (Gmail, WhatsApp, LinkedIn)
- Tasks need classification and routing based on complexity and sensitivity

## Procedure

### Step 1: Read Task File

1. Read the task file from `vault/Needs_Action/[filename].md`
2. Parse YAML frontmatter to extract:
   - `type` (email, whatsapp, linkedin, file, etc.)
   - `priority` (high, medium, low)
   - `source` (gmail, whatsapp, linkedin, file)
   - `created` timestamp
   - Any other metadata
3. Extract the main content body
4. Read `vault/Company_Handbook.md` for processing rules

### Step 2: Classify Task

Analyze the task and classify into ONE category:

**SIMPLE TASKS** (Execute directly):
- Reading/summarizing documents
- Simple information requests
- File organization
- Status updates
- Non-sensitive email replies to known contacts

**COMPLEX TASKS** (Create Plan.md first):
- Multi-step workflows (3+ steps)
- Business analysis or reports
- Tasks requiring multiple tools/actions
- Project planning
- Research tasks

**SENSITIVE TASKS** (Require human approval):
- Financial amounts > $500
- Email sending to NEW contacts
- LinkedIn posting (always sensitive)
- WhatsApp replies with commitments
- External API calls
- Payment actions
- Legal/contractual matters

### Step 3: Route Task

Based on classification, take appropriate action:

#### A. For SIMPLE Tasks:

1. Execute the action directly
2. Log the action to `vault/Logs/actions-[date].log`:
   ```
   [TIMESTAMP] [TASK_ID] SIMPLE_TASK_EXECUTED: [brief description]
   ```
3. Move task file to `vault/Done/[filename].md`
4. Update task frontmatter: `status: done`, `processed: [timestamp]`

#### B. For COMPLEX Tasks:

1. Create `vault/Plans/PLAN_[task-id]_[date].md` with:
   ```markdown
   ---
   task_id: [original task id]
   created: [timestamp]
   status: planning
   ---

   # Plan: [Task Title]

   ## Objective
   [Clear goal statement]

   ## Steps
   1. [ ] [Step 1 with specific action]
   2. [ ] [Step 2 with specific action]
   3. [ ] [Step 3 with specific action]

   ## Expected Outcome
   [What success looks like]

   ## Resources Needed
   - [List any files, data, or tools needed]
   ```
2. Execute the plan steps sequentially
3. Log each step completion
4. Move original task to `vault/Done/`
5. Move plan to `vault/Done/` when complete

#### C. For SENSITIVE Tasks:

1. Add approval metadata to task file:
   ```yaml
   requires_approval: true
   approval_reason: "[Why approval needed]"
   approval_requested: [timestamp]
   ```
2. Move task file to `vault/Pending_Approval/[filename].md`
3. Log approval request:
   ```
   [TIMESTAMP] [TASK_ID] APPROVAL_REQUESTED: [reason]
   ```
4. DO NOT execute the action
5. Wait for human to move file to `vault/Approved/`

### Step 4: Update Dashboard

After processing, update `vault/Dashboard.md`:
1. Increment task counters
2. Update "Recent Activity" section with:
   ```
   | [Time] | [Source] | [Type] | [Status] | [Summary] |
   ```
3. Update timestamp

## Output Format

### For Simple Tasks:
- Task file moved to `vault/Done/`
- Action logged
- Dashboard updated

### For Complex Tasks:
- Plan.md created in `vault/Plans/`
- Plan executed
- Both task and plan moved to `vault/Done/`
- Dashboard updated

### For Sensitive Tasks:
- Task file moved to `vault/Pending_Approval/`
- Approval metadata added
- Dashboard updated
- NO action taken yet

## Quality Criteria

- **Accuracy**: Correct classification (simple/complex/sensitive)
- **Completeness**: All required fields filled
- **Clarity**: Plans are actionable with specific steps
- **Safety**: Sensitive tasks NEVER executed without approval
- **Logging**: Every action logged with timestamp and details
- **Consistency**: Follow Company_Handbook.md rules

## Example Input

```markdown
---
id: email_abc123_20260206
source: gmail
type: email
status: pending
priority: high
created: 2026-02-06T10:30:00Z
email_from: client@example.com
email_subject: Invoice Request
---

## Email Content

**From**: client@example.com
**Subject**: Invoice Request

Hi, can you send me the invoice for January?

## Suggested Actions
- [ ] Generate invoice
- [ ] Send to client
```

## Example Output (Sensitive - Approval Required)

Task moved to `vault/Pending_Approval/EMAIL_abc123_20260206.md` with updated frontmatter:

```yaml
requires_approval: true
approval_reason: "Email sending to client requires approval"
approval_requested: 2026-02-06T10:35:00Z
```

Log entry:
```
2026-02-06 10:35:00 email_abc123 APPROVAL_REQUESTED: Email sending to client@example.com
```

## Important Notes

- ALWAYS read Company_Handbook.md before processing
- NEVER execute sensitive actions without approval
- ALWAYS log every action taken
- Plans must be specific and actionable
- Update Dashboard after every task
- If unsure about classification, default to SENSITIVE

## Success Criteria

Task processing is successful when:
- ✅ Task correctly classified
- ✅ Appropriate action taken (execute/plan/approve)
- ✅ Task file moved to correct folder
- ✅ All actions logged
- ✅ Dashboard updated
- ✅ No sensitive actions executed without approval

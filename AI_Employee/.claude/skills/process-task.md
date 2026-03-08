# Process Task Skill

**Description:** Analyze tasks from Needs_Action folder, determine if they need approval, and execute or route accordingly.

**Trigger:** When orchestrator detects new tasks in /Needs_Action

---

## Instructions

When this skill is invoked, follow these steps:

### 1. Read Task File

- Read the task file from vault/Needs_Action/
- Parse YAML frontmatter for metadata
- Extract task content

### 2. Analyze Task

Determine task complexity and sensitivity:

**Simple Tasks (No Plan.md needed):**
- Email replies to known contacts
- File organization
- Simple information requests
- Document reading

**Complex Tasks (Create Plan.md):**
- Multi-step workflows
- Business analysis
- Report generation
- Tasks requiring multiple tools/actions

**Sensitive Tasks (Require Approval):**
- Financial amounts > $500
- Email sending to new contacts
- LinkedIn posting
- External API calls
- Payment actions

### 3. Route Task

Based on analysis:

**A. Simple + Safe → Execute Directly**
```
1. Perform the action
2. Log the result
3. Move task file to vault/Done/
4. Update Dashboard.md
```

**B. Complex + Safe → Create Plan First**
```
1. Create Plan.md in vault/Plans/ with:
   - Task summary
   - Step-by-step breakdown
   - Expected outcome
2. Execute steps
3. Move task to vault/Done/
4. Update Dashboard.md
```

**C. Sensitive → Request Approval**
```
1. Add approval reasons to task file
2. Move to vault/Pending_Approval/
3. Wait for human to move to vault/Approved/
4. Then execute (using MCP if needed)
5. Move to vault/Done/
```

### 4. Execution Guidelines

**For Email Tasks:**
- Use Gmail MCP server (if configured)
- Draft reply based on Company_Handbook.md tone
- For sensitive: move to Pending_Approval
- For safe: send and log

**For LinkedIn Tasks:**
- Use Browser MCP server (if configured)
- Draft post based on business context
- ALWAYS require approval (move to Pending_Approval)
- After approval: post and log

**For File Tasks:**
- Use built-in file operations
- Safe to execute directly
- Log actions taken

**For Analysis Tasks:**
- Read relevant files (Dashboard, Company_Handbook, etc.)
- Generate report/summary
- Save to appropriate location
- Update Dashboard

### 5. Logging

Always log actions to vault/Logs/:
```
[TIMESTAMP] [TASK_ID] [ACTION] [STATUS] [DETAILS]
```

### 6. Error Handling

If task fails:
1. Log error details
2. Move task to vault/Needs_Action/Failed/
3. Create error report in task file
4. Update Dashboard with error count

---

## Example Usage

```bash
# Orchestrator triggers this skill
claude --skill process-task --task-file "vault/Needs_Action/EMAIL_12345.md"
```

Or in Ralph Wiggum loop:
```bash
claude /ralph-loop "Use process-task skill to handle all tasks in Needs_Action folder until empty" --max-iterations 10
```

---

## Required Context

This skill needs access to:
- vault/Needs_Action/ (input)
- vault/Pending_Approval/ (routing)
- vault/Done/ (output)
- vault/Plans/ (complex tasks)
- vault/Logs/ (logging)
- vault/Dashboard.md (updates)
- vault/Company_Handbook.md (rules)

---

## MCP Servers Used

- **Gmail MCP**: For email sending (if configured)
- **Browser MCP**: For LinkedIn posting (if configured)
- **Filesystem**: Built-in, for file operations

---

## Success Criteria

Task is complete when:
- Task file moved to Done/ or Pending_Approval/
- Dashboard.md updated
- Action logged
- If complex: Plan.md created
- If sensitive: Approval request filed

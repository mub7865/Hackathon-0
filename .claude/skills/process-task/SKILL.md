---
name: process-task
description: Process a single task file with AI analysis following Company Handbook rules
version: 1.0.0
author: Bronze AI Assistant
---

# Process Task Skill

Analyzes a single task file from the Needs_Action folder and generates comprehensive AI summary with key points and action items.

## Purpose

This skill provides reusable intelligence for processing task files. It reads the Company Handbook rules, analyzes task content, and generates structured summaries with appropriate emojis and flags.

## Input

- **task_file_path** (required): Full path to the task markdown file
- **vault_path** (optional): Path to vault directory (default: bronze/vault)

## Output

Returns a structured result with:
- `status`: "success" or "error"
- `summary`: Brief summary of the task
- `processed_at`: ISO timestamp
- `error_message`: Error details (if failed)

## Processing Logic

### Step 1: Read Company Handbook
```
Read: {vault_path}/Company_Handbook.md
Extract: Processing rules, custom flags, tone preferences
```

### Step 2: Read Task File
```
Read: {task_file_path}
Extract: Original content from "## Original Content" section
Parse: Frontmatter metadata (type, priority, created date)
```

### Step 3: Analyze Content

Apply these rules from Company Handbook:

**Summary Rules:**
- Exactly 3 bullet points
- 150-200 words total
- Highlight key dates and amounts in bold
- Action-oriented phrasing

**Custom Flags:**
- 💰 Amount > $500
- 🚨💰 Amount > $10,000
- 🚨 Deadline < 3 days
- ⚠️ Deadline < 7 days
- 📝 Meeting notes
- 👤 Client communication
- 🏢 Internal communication
- 📄 Legal document
- 📊 Financial document

**Tone:**
- Professional and courteous
- Concise language
- Active voice
- Direct addressing

### Step 4: Generate AI Analysis

Create this structure:

```markdown
## AI Analysis

**Summary**:
- [Concise bullet point with key information]
- [Second bullet point with important details]
- [Third bullet point with actionable insight]

**Key Points**:
- [Emoji] **Important detail 1** (with context)
- [Emoji] **Important detail 2** (with context)
- [Emoji] **Important detail 3** (with context)

## Action Items

- [ ] [Specific action with deadline if applicable]
- [ ] [Second action with owner if known]
- [ ] [Third action with priority indicator]

---

**Processed by**: Claude AI Assistant
**Processed at**: {ISO_TIMESTAMP}
**Status**: ✅ Complete
```

### Step 5: Update Task File

```
Edit: {task_file_path}
Action: Append AI Analysis section after original content
Preserve: All original content and frontmatter
```

### Step 6: Return Result

```json
{
  "status": "success",
  "summary": "Brief one-line summary",
  "processed_at": "2026-01-19T15:30:00Z",
  "key_flags": ["💰", "🚨"],
  "action_items_count": 3
}
```

## Error Handling

If processing fails:

1. **File Not Found**
   - Return error status
   - Message: "Task file not found at {path}"
   - Do not create log file

2. **Invalid Format**
   - Return error status
   - Message: "Task file missing required sections"
   - Log to vault/Logs/error-{timestamp}.md

3. **Handbook Missing**
   - Use default rules
   - Log warning
   - Continue processing

4. **Write Failure**
   - Return error status
   - Message: "Failed to update task file"
   - Original file remains unchanged

## Usage Examples

### Example 1: Basic Usage
```
Invoke skill: process-task
Parameters:
  task_file_path: bronze/vault/Needs_Action/TASK_meeting_20260119.md
  vault_path: bronze/vault

Result:
  status: success
  summary: Q1 planning meeting with $50,000 budget allocation
  processed_at: 2026-01-19T15:30:00Z
```

### Example 2: Error Handling
```
Invoke skill: process-task
Parameters:
  task_file_path: bronze/vault/Needs_Action/invalid.md

Result:
  status: error
  error_message: Task file not found at bronze/vault/Needs_Action/invalid.md
```

## Integration with Orchestrator

This skill is designed to be called by orchestrator agents:

```
Orchestrator workflow:
1. Discover pending tasks in Needs_Action/
2. For each task:
   - Invoke process-task skill
   - Check result status
   - If success: move to Done/
   - If error: log and continue
3. Update Dashboard with results
```

## Performance

- Average processing time: 3-5 seconds per task
- Handles files up to 10MB
- Supports all text-based formats (.txt, .md, .pdf text)

## Dependencies

- Company_Handbook.md must exist in vault
- Task files must have "## Original Content" section
- Vault directory must be accessible

## Version History

- v1.0.0 (2026-01-19): Initial release
  - Basic task processing
  - Company Handbook integration
  - Custom flags support
  - Error handling

## Notes

- This skill is stateless and thread-safe
- Can be invoked multiple times concurrently
- Always preserves original content
- Follows Company Handbook rules strictly
- Returns structured results for orchestration

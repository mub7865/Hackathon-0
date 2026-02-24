---
name: "create-plan"
description: "Generate detailed execution plans for complex multi-step tasks by breaking them into actionable steps with clear objectives and success criteria. Use when a task requires multiple coordinated actions or involves business analysis."
---

# Create Plan Skill

## When to Use This Skill

Use this skill when:
- Task is classified as COMPLEX (3+ steps required)
- Task involves business analysis or reporting
- Task requires coordination of multiple actions
- Task needs structured breakdown before execution
- Uncertainty exists about best approach

## Procedure

### Step 1: Analyze Task Requirements

1. Read the original task file completely
2. Identify the core objective
3. List all required actions
4. Identify dependencies between actions
5. Determine resources needed (files, data, tools)
6. Check Company_Handbook.md for relevant rules

### Step 2: Create Plan Structure

Create file: `vault/Plans/PLAN_[task-id]_[YYYYMMDD].md`

Use this template:

```markdown
---
task_id: [original task id]
task_source: [gmail/whatsapp/linkedin/file]
created: [ISO timestamp]
status: planning
estimated_steps: [number]
---

# Plan: [Clear, Descriptive Title]

## Objective
[One sentence: What success looks like]

## Context
[Brief background from original task]

## Steps

1. [ ] **[Action Verb] [Specific Action]**
   - Details: [What exactly to do]
   - Resources: [Files/data needed]
   - Output: [What this produces]

2. [ ] **[Next Action]**
   - Details: [Specifics]
   - Resources: [What's needed]
   - Output: [Result]

[Continue for all steps...]

## Expected Outcome
[Concrete deliverable or result]

## Success Criteria
- [ ] [Measurable criterion 1]
- [ ] [Measurable criterion 2]
- [ ] [Measurable criterion 3]

## Resources Needed
- [File paths, data sources, tools]

## Potential Issues
- [Risk 1]: [Mitigation]
- [Risk 2]: [Mitigation]

## Notes
[Any additional context or considerations]
```

### Step 3: Validate Plan Quality

Check that plan has:
- ✅ Clear, actionable steps (not vague)
- ✅ Specific outputs for each step
- ✅ Measurable success criteria
- ✅ Identified resources
- ✅ Logical step ordering
- ✅ Realistic scope (not too ambitious)

### Step 4: Link to Original Task

1. Update original task file frontmatter:
   ```yaml
   plan_created: [timestamp]
   plan_file: PLAN_[task-id]_[date].md
   status: planned
   ```
2. Keep original task in Needs_Action until plan execution starts

### Step 5: Log Plan Creation

Add to `vault/Logs/actions-[date].log`:
```
[TIMESTAMP] [TASK_ID] PLAN_CREATED: [plan filename] - [number] steps
```

## Output Format

### Plan File Structure:
- YAML frontmatter with metadata
- Clear objective statement
- Numbered, checkboxed steps
- Expected outcome
- Success criteria
- Resources list
- Risk mitigation

### Updated Task File:
- Links to plan file
- Status updated to "planned"

## Quality Criteria

- **Specificity**: Steps are concrete, not vague ("Send email to X" not "Handle communication")
- **Actionability**: Each step can be executed immediately
- **Completeness**: All necessary steps included
- **Ordering**: Steps in logical sequence
- **Measurability**: Success criteria are objective
- **Realism**: Plan is achievable with available resources

## Example Input

Task: "Analyze Q4 business performance and create report"

## Example Output

```markdown
---
task_id: task_q4_analysis_20260206
task_source: file
created: 2026-02-06T14:30:00Z
status: planning
estimated_steps: 5
---

# Plan: Q4 2025 Business Performance Analysis

## Objective
Generate comprehensive Q4 performance report with revenue analysis, bottlenecks, and recommendations.

## Context
Request to analyze Q4 business performance for strategic planning.

## Steps

1. [ ] **Gather Q4 Financial Data**
   - Details: Read all transaction logs from vault/Accounting/Q4_2025/
   - Resources: Monthly transaction files (Oct, Nov, Dec)
   - Output: Consolidated revenue and expense data

2. [ ] **Calculate Key Metrics**
   - Details: Compute total revenue, expenses, profit margin, growth rate
   - Resources: Q3 data for comparison
   - Output: Metrics table with Q3 vs Q4 comparison

3. [ ] **Identify Bottlenecks**
   - Details: Analyze vault/Done/ for delayed tasks, check average completion time
   - Resources: Task completion logs
   - Output: List of bottlenecks with impact assessment

4. [ ] **Generate Recommendations**
   - Details: Based on metrics and bottlenecks, propose 3-5 actionable improvements
   - Resources: Company_Handbook.md for business goals
   - Output: Prioritized recommendation list

5. [ ] **Create Final Report**
   - Details: Compile all sections into structured markdown report
   - Resources: All outputs from previous steps
   - Output: vault/Reports/Q4_2025_Performance_Report.md

## Expected Outcome
Complete Q4 performance report with metrics, analysis, and recommendations saved to vault/Reports/

## Success Criteria
- [ ] All Q4 financial data included
- [ ] Metrics calculated with Q3 comparison
- [ ] At least 3 bottlenecks identified
- [ ] 3-5 actionable recommendations provided
- [ ] Report saved in proper format

## Resources Needed
- vault/Accounting/Q4_2025/*.md
- vault/Accounting/Q3_2025/*.md (for comparison)
- vault/Done/ (for task analysis)
- vault/Company_Handbook.md (for goals)

## Potential Issues
- Missing transaction data: Check with user if files incomplete
- Unclear bottlenecks: Focus on tasks >3 days completion time
- Too many recommendations: Prioritize by impact

## Notes
This is a strategic analysis - focus on actionable insights, not just data presentation.
```

## Important Notes

- Plans should be detailed enough to execute without ambiguity
- Each step should produce a concrete output
- Success criteria must be measurable
- Always consider what could go wrong
- Plans are living documents - can be updated during execution

## Success Criteria

Plan creation is successful when:
- ✅ Plan file created in vault/Plans/
- ✅ All required sections completed
- ✅ Steps are specific and actionable
- ✅ Success criteria are measurable
- ✅ Original task linked to plan
- ✅ Plan logged

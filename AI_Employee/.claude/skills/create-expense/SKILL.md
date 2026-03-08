---
name: "create-expense"
description: "Record business expenses in Odoo accounting system with automatic approval workflow for amounts over $100. Use when task involves recording business costs, vendor payments, or operational expenses."
---

# Create Expense Skill

## When to Use This Skill

Use this skill when:
- Business expense needs to be recorded
- Vendor payment or bill received
- Operational costs incurred (software, services, supplies)
- Task mentions "expense", "cost", "bill", or "vendor payment"
- Need to track business spending

**IMPORTANT**: Expenses over $100 require human approval before posting to Odoo.

## Procedure

### Step 1: Extract Expense Details

1. Read the task file completely
2. Identify required expense information:
   - **Vendor/Supplier Name**: Who was paid
   - **Amount**: Expense amount (must be > 0)
   - **Category**: Type of expense (software, office, marketing, etc.)
   - **Description**: What was purchased/paid for
   - **Date**: Expense date (default: today)
   - **Receipt/Invoice**: Reference number (optional)

3. Validate required fields:
   - Vendor name is specified
   - Amount is a positive number
   - Category is valid business expense
   - Description is clear

### Step 2: Check Company Handbook

1. Read `vault/Company_Handbook.md` for:
   - Approved expense categories
   - Spending limits by category
   - Vendor approval list
   - Receipt requirements
   - Tax deductibility rules

2. Verify expense is within policy

### Step 3: Determine Approval Requirement

**Approval Threshold: $100**

- **Amount ≤ $100**: Auto-approve, post directly to Odoo
- **Amount > $100**: Requires human approval

### Step 4A: If Amount ≤ $100 (Auto-Approve)

1. Record expense in Odoo:
   ```python
   from src.actions.accounting_actions import process_expense_request

   expense_data = {
       "vendor_name": "[Vendor]",
       "amount": [Amount],
       "category": "[Category]",
       "description": "[Description]",
       "date": "[YYYY-MM-DD]"
   }
   ```

2. Log the action:
   ```
   [TIMESTAMP] [TASK_ID] EXPENSE_RECORDED: [Vendor] - $[Amount] - [Category] - Auto-approved
   ```

3. Update task status:
   ```yaml
   status: completed
   expense_recorded: true
   expense_amount: [Amount]
   odoo_expense_id: [ID from Odoo]
   auto_approved: true
   ```

4. Move task to `vault/Done/`

5. Update Dashboard:
   ```markdown
   | [Time] | Accounting | Expense Recorded | $[Amount] | [Vendor] - [Category] |
   ```

### Step 4B: If Amount > $100 (Requires Approval)

1. Create approval request:
   ```markdown
   ## Expense Approval Request

   **Action Type**: Financial
   **Amount**: $[Amount]
   **Requested**: [ISO timestamp]
   **Expires**: [ISO timestamp + 24 hours]

   ### Expense Details
   - **Vendor**: [Vendor Name]
   - **Amount**: $[Amount]
   - **Category**: [Software/Office/Marketing/etc.]
   - **Description**: [What was purchased]
   - **Date**: [Date]
   - **Receipt/Invoice**: [Reference number]

   ### Business Justification
   [Why this expense is necessary - business need, ROI, etc.]

   ### Expected Outcome
   - Expense posted to Odoo accounting system
   - Cost tracked in appropriate category
   - Tax deduction documented (if applicable)
   - Budget impact recorded

   ### Budget Impact
   - **Category Budget**: $[Monthly/Annual budget]
   - **Spent This Period**: $[Already spent]
   - **This Expense**: $[Amount]
   - **Remaining**: $[Budget - Spent - This]

   ---

   **To Approve**: Move this file to `vault/Approved/`
   **To Reject**: Move this file to `vault/Rejected/`
   **To Modify**: Edit the expense details and re-request
   ```

2. Update task frontmatter:
   ```yaml
   requires_approval: true
   approval_reason: "Expense amount exceeds $100 threshold"
   approval_category: financial
   expense_amount: [Amount]
   vendor_name: "[Vendor]"
   expense_category: "[Category]"
   status: pending_approval
   ```

3. Move to `vault/Pending_Approval/`

4. Log and update Dashboard

## Output Format

### Auto-Approved Expense (≤ $100):

```markdown
---
id: expense_software_20260304
type: accounting
status: completed
expense_recorded: true
expense_amount: 29.99
vendor_name: "GitHub"
expense_category: "software"
odoo_expense_id: "EXP/2026/0156"
auto_approved: true
---

# Expense Recorded: GitHub Pro Subscription

## Expense Details ✓

**Vendor**: GitHub
**Amount**: $29.99
**Category**: Software/SaaS
**Expense ID**: EXP/2026/0156
**Status**: Posted to Odoo (Auto-approved)

### Description
Monthly GitHub Pro subscription for code repositories and collaboration.

**Tax Deductible**: Yes (Business software expense)
```

## Quality Criteria

- **Accuracy**: Amount and vendor correct
- **Categorization**: Proper expense category
- **Justification**: Clear business purpose
- **Compliance**: Follows company expense policy
- **Documentation**: Receipt/invoice referenced
- **Timeliness**: Recorded promptly

## Success Criteria

- ✅ All required fields validated
- ✅ Amount is positive number
- ✅ Vendor and category specified
- ✅ Approval workflow followed
- ✅ Expense posted to Odoo
- ✅ Action logged
- ✅ Dashboard updated

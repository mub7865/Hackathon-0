---
name: "create-invoice"
description: "Create professional invoices in Odoo accounting system with automatic approval workflow for amounts over $100. Use when task requires generating client invoices for services or products delivered."
---

# Create Invoice Skill

## When to Use This Skill

Use this skill when:
- Task involves creating a client invoice
- Services or products have been delivered
- Payment needs to be requested from a client
- Task mentions "invoice", "bill", or "payment request"
- Need to record revenue in accounting system

**IMPORTANT**: Invoices over $100 require human approval before posting to Odoo.

## Procedure

### Step 1: Extract Invoice Details

1. Read the task file completely
2. Identify required invoice information:
   - **Client Name**: Who is being invoiced
   - **Amount**: Total invoice amount (must be > 0)
   - **Description**: What services/products were provided
   - **Date**: Invoice date (default: today)
   - **Due Date**: Payment due date (optional)
   - **Items**: Line items with quantities and prices (optional)

3. Validate required fields:
   - Client name is specified
   - Amount is a positive number
   - Description is clear and professional

### Step 2: Check Company Handbook

1. Read `vault/Company_Handbook.md` for:
   - Standard payment terms (e.g., Net 30)
   - Invoice numbering format
   - Company billing information
   - Tax rates or additional charges
   - Client-specific pricing or terms

2. Apply company standards to invoice

### Step 3: Determine Approval Requirement

**Approval Threshold: $100**

- **Amount ≤ $100**: Auto-approve, post directly to Odoo
- **Amount > $100**: Requires human approval

### Step 4A: If Amount ≤ $100 (Auto-Approve)

1. Create invoice in Odoo using accounting actions:
   ```python
   from src.actions.accounting_actions import process_invoice_request

   invoice_data = {
       "client_name": "[Client Name]",
       "amount": [Amount],
       "description": "[Description]",
       "date": "[YYYY-MM-DD]",
       "due_date": "[YYYY-MM-DD]"
   }
   ```

2. Log the action:
   ```
   [TIMESTAMP] [TASK_ID] INVOICE_CREATED: [Client] - $[Amount] - Auto-approved
   ```

3. Update task status:
   ```yaml
   status: completed
   invoice_created: true
   invoice_amount: [Amount]
   odoo_invoice_id: [ID from Odoo]
   auto_approved: true
   ```

4. Move task to `vault/Done/`

5. Update Dashboard:
   ```markdown
   | [Time] | Accounting | Invoice Created | $[Amount] | [Client] |
   ```

### Step 4B: If Amount > $100 (Requires Approval)

1. Create approval request in task file:
   ```markdown
   ## Invoice Approval Request

   **Action Type**: Financial
   **Amount**: $[Amount]
   **Requested**: [ISO timestamp]
   **Expires**: [ISO timestamp + 24 hours]

   ### Invoice Details
   - **Client**: [Client Name]
   - **Amount**: $[Amount]
   - **Description**: [Services/products provided]
   - **Invoice Date**: [Date]
   - **Due Date**: [Due date or payment terms]

   ### Line Items
   | Item | Quantity | Unit Price | Total |
   |------|----------|------------|-------|
   | [Item 1] | [Qty] | $[Price] | $[Total] |
   | [Item 2] | [Qty] | $[Price] | $[Total] |

   **Subtotal**: $[Subtotal]
   **Tax**: $[Tax if applicable]
   **Total**: $[Total Amount]

   ### Rationale
   [Why this invoice is being created - project completion, milestone reached, etc.]

   ### Expected Outcome
   - Invoice posted to Odoo accounting system
   - Client receives invoice notification
   - Payment tracked in accounts receivable
   - Revenue recorded for this period

   ---

   **To Approve**: Move this file to `vault/Approved/`
   **To Reject**: Move this file to `vault/Rejected/`
   **To Modify**: Edit the invoice details and re-request

   **Note**: This approval request expires in 24 hours.
   ```

2. Update task frontmatter:
   ```yaml
   requires_approval: true
   approval_reason: "Invoice amount exceeds $100 threshold"
   approval_requested: [ISO timestamp]
   approval_expires: [ISO timestamp + 24 hours]
   approval_category: financial
   invoice_amount: [Amount]
   client_name: "[Client]"
   status: pending_approval
   ```

3. Move task to `vault/Pending_Approval/`

4. Log approval request:
   ```
   [TIMESTAMP] [TASK_ID] INVOICE_APPROVAL_REQUESTED: [Client] - $[Amount]
   ```

5. Update Dashboard:
   ```markdown
   | [Time] | Accounting | Invoice Pending | $[Amount] | [Client] - Awaiting Approval |
   ```

### Step 5: Post-Approval Processing

**When task is moved to vault/Approved/:**

1. Create invoice in Odoo:
   ```python
   from src.actions.accounting_actions import process_invoice_request

   # Invoice data from approved task
   result = process_invoice_request(task_data)
   ```

2. Log the action:
   ```
   [TIMESTAMP] [TASK_ID] INVOICE_CREATED: [Client] - $[Amount] - Approved by human
   ```

3. Update task with Odoo invoice ID:
   ```yaml
   status: completed
   invoice_created: true
   odoo_invoice_id: [ID from Odoo]
   approved_by: human
   approved_at: [ISO timestamp]
   ```

4. Move task to `vault/Done/`

5. Update Dashboard with completion

## Output Format

### Auto-Approved Invoice (≤ $100):

```markdown
---
id: invoice_client_a_20260304
source: whatsapp
type: accounting
priority: medium
status: completed
invoice_created: true
invoice_amount: 75.00
client_name: "Client A"
odoo_invoice_id: "INV/2026/0042"
auto_approved: true
created_at: 2026-03-04T10:00:00Z
completed_at: 2026-03-04T10:01:23Z
---

# Invoice: Client A - Website Updates

## Invoice Created ✓

**Client**: Client A
**Amount**: $75.00
**Invoice ID**: INV/2026/0042
**Status**: Posted to Odoo (Auto-approved)

### Services Provided
- Website content updates (3 hours)
- Bug fixes and testing (1 hour)

**Total**: $75.00

### Action Log
- [2026-03-04T10:00:15Z] Invoice created in Odoo
- [2026-03-04T10:00:18Z] Client notification sent
- [2026-03-04T10:01:23Z] Task completed
```

### Approval Required Invoice (> $100):

```markdown
---
id: invoice_client_b_20260304
source: file
type: accounting
priority: high
requires_approval: true
approval_reason: "Invoice amount exceeds $100 threshold"
approval_requested: 2026-03-04T10:00:00Z
approval_expires: 2026-03-05T10:00:00Z
approval_category: financial
invoice_amount: 2500.00
client_name: "Client B"
status: pending_approval
---

# Invoice: Client B - Full Website Redesign

## Invoice Approval Request

**Action Type**: Financial
**Amount**: $2,500.00
**Requested**: 2026-03-04T10:00:00Z
**Expires**: 2026-03-05T10:00:00Z

### Invoice Details
- **Client**: Client B
- **Amount**: $2,500.00
- **Description**: Complete website redesign and development
- **Invoice Date**: 2026-03-04
- **Due Date**: 2026-04-03 (Net 30)

### Line Items
| Item | Quantity | Unit Price | Total |
|------|----------|------------|-------|
| Design mockups | 1 | $500.00 | $500.00 |
| Frontend development | 40 hrs | $40.00 | $1,600.00 |
| Backend integration | 10 hrs | $40.00 | $400.00 |

**Total**: $2,500.00

### Rationale
Project completed as per contract. All deliverables approved by client. Ready to invoice per payment terms (50% upfront received, 50% due on completion).

### Expected Outcome
- Invoice posted to Odoo accounting system
- Client receives invoice via email
- Payment tracked in accounts receivable
- $2,500 revenue recorded for Q1 2026

---

**To Approve**: Move this file to `vault/Approved/`
**To Reject**: Move this file to `vault/Rejected/`
**To Modify**: Edit the invoice details and re-request

**Note**: This approval request expires in 24 hours.
```

## Quality Criteria

- **Accuracy**: All amounts and calculations are correct
- **Completeness**: All required invoice fields present
- **Clarity**: Description clearly states what was provided
- **Professionalism**: Invoice follows business standards
- **Compliance**: Follows company billing policies
- **Traceability**: Linked to original work/project
- **Timeliness**: Invoice created promptly after delivery

## Example Input

```markdown
---
id: task_invoice_client_a_20260304
source: whatsapp
type: accounting
priority: medium
---

# Task: Create Invoice for Client A

Client A's website updates are complete. Create invoice for:
- 3 hours of content updates
- 1 hour of bug fixes
Total: $75 (hourly rate $18.75)
```

## Example Output

Task moved to `vault/Done/` with invoice created:

```yaml
---
id: task_invoice_client_a_20260304
source: whatsapp
type: accounting
priority: medium
status: completed
invoice_created: true
invoice_amount: 75.00
client_name: "Client A"
odoo_invoice_id: "INV/2026/0042"
auto_approved: true
created_at: 2026-03-04T10:00:00Z
completed_at: 2026-03-04T10:01:23Z
---

# Invoice Created ✓

**Client**: Client A
**Amount**: $75.00
**Invoice ID**: INV/2026/0042
**Status**: Posted to Odoo

[Invoice details as shown above]
```

## Important Notes

- **$100 threshold is strict** - amounts over $100 ALWAYS require approval
- **Validate client name** - must match existing Odoo customer or create new
- **Check payment terms** - apply company standard or client-specific terms
- **Include tax if applicable** - check Company_Handbook for tax requirements
- **Log all actions** - maintain audit trail for financial transactions
- **Update Dashboard** - keep business owner informed of invoicing activity
- **Handle errors gracefully** - if Odoo connection fails, queue for retry

## Success Criteria

Invoice creation is successful when:
- ✅ All required invoice fields validated
- ✅ Amount is positive number
- ✅ Client name is specified
- ✅ Description is clear and professional
- ✅ Approval workflow followed correctly (auto or manual)
- ✅ Invoice posted to Odoo (or approval requested)
- ✅ Odoo invoice ID captured
- ✅ Action logged with timestamp
- ✅ Task status updated correctly
- ✅ Dashboard updated with invoice activity
- ✅ Audit trail maintained

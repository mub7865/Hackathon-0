---
name: "record-payment"
description: "Record client payments in Odoo accounting system with automatic approval workflow for amounts over $100. Use when task involves recording received payments, matching to invoices, or updating accounts receivable."
---

# Record Payment Skill

## When to Use This Skill

Use this skill when:
- Client payment has been received
- Need to record payment against an invoice
- Bank transfer or payment notification received
- Task mentions "payment received", "paid", or "payment confirmation"
- Need to update accounts receivable

**IMPORTANT**: Payments over $100 require human approval before posting to Odoo.

## Procedure

### Step 1: Extract Payment Details

1. Read the task file completely
2. Identify required payment information:
   - **Client Name**: Who made the payment
   - **Amount**: Payment amount received (must be > 0)
   - **Payment Method**: Bank transfer, cash, check, credit card, etc.
   - **Payment Date**: When payment was received (default: today)
   - **Invoice Reference**: Which invoice this payment is for (optional)
   - **Transaction ID**: Bank reference or transaction number (optional)

3. Validate required fields:
   - Client name is specified
   - Amount is a positive number
   - Payment method is valid
   - Payment date is reasonable (not future date)

### Step 2: Check Company Handbook

1. Read `vault/Company_Handbook.md` for:
   - Accepted payment methods
   - Payment processing policies
   - Bank account information for verification
   - Client-specific payment terms

2. Verify payment method is accepted

### Step 3: Determine Approval Requirement

**Approval Threshold: $100**

- **Amount ≤ $100**: Auto-approve, post directly to Odoo
- **Amount > $100**: Requires human approval

### Step 4A: If Amount ≤ $100 (Auto-Approve)

1. Record payment in Odoo using accounting actions:
   ```python
   from src.actions.accounting_actions import process_payment_request

   payment_data = {
       "client_name": "[Client Name]",
       "amount": [Amount],
       "payment_method": "[Method]",
       "payment_date": "[YYYY-MM-DD]",
       "invoice_reference": "[Invoice ID]",
       "transaction_id": "[Transaction ID]"
   }
   ```

2. Log the action:
   ```
   [TIMESTAMP] [TASK_ID] PAYMENT_RECORDED: [Client] - $[Amount] - Auto-approved
   ```

3. Update task status:
   ```yaml
   status: completed
   payment_recorded: true
   payment_amount: [Amount]
   odoo_payment_id: [ID from Odoo]
   auto_approved: true
   ```

4. Move task to `vault/Done/`

5. Update Dashboard:
   ```markdown
   | [Time] | Accounting | Payment Received | $[Amount] | [Client] |
   ```

### Step 4B: If Amount > $100 (Requires Approval)

1. Create approval request in task file:
   ```markdown
   ## Payment Approval Request

   **Action Type**: Financial
   **Amount**: $[Amount]
   **Requested**: [ISO timestamp]
   **Expires**: [ISO timestamp + 24 hours]

   ### Payment Details
   - **Client**: [Client Name]
   - **Amount**: $[Amount]
   - **Payment Method**: [Bank transfer/Cash/Check/Card]
   - **Payment Date**: [Date]
   - **Invoice Reference**: [Invoice ID if applicable]
   - **Transaction ID**: [Bank reference number]

   ### Verification
   - ✅ Amount matches expected payment
   - ✅ Payment method is accepted
   - ✅ Client identity verified
   - ✅ Bank transaction confirmed (if applicable)

   ### Rationale
   [Why this payment is being recorded - invoice payment, advance payment, etc.]

   ### Expected Outcome
   - Payment posted to Odoo accounting system
   - Invoice marked as paid (if applicable)
   - Accounts receivable updated
   - Cash flow recorded for this period

   ### Risks
   - **Risk**: Payment could be fraudulent or incorrect
     - Mitigation: Verify bank transaction and client identity
   - **Risk**: Payment amount doesn't match invoice
     - Mitigation: Document discrepancy and follow up with client

   ---

   **To Approve**: Move this file to `vault/Approved/`
   **To Reject**: Move this file to `vault/Rejected/`
   **To Modify**: Edit the payment details and re-request

   **Note**: This approval request expires in 24 hours.
   ```

2. Update task frontmatter:
   ```yaml
   requires_approval: true
   approval_reason: "Payment amount exceeds $100 threshold"
   approval_requested: [ISO timestamp]
   approval_expires: [ISO timestamp + 24 hours]
   approval_category: financial
   payment_amount: [Amount]
   client_name: "[Client]"
   status: pending_approval
   ```

3. Move task to `vault/Pending_Approval/`

4. Log approval request:
   ```
   [TIMESTAMP] [TASK_ID] PAYMENT_APPROVAL_REQUESTED: [Client] - $[Amount]
   ```

5. Update Dashboard:
   ```markdown
   | [Time] | Accounting | Payment Pending | $[Amount] | [Client] - Awaiting Approval |
   ```

### Step 5: Post-Approval Processing

**When task is moved to vault/Approved/:**

1. Record payment in Odoo:
   ```python
   from src.actions.accounting_actions import process_payment_request

   result = process_payment_request(task_data)
   ```

2. Log the action:
   ```
   [TIMESTAMP] [TASK_ID] PAYMENT_RECORDED: [Client] - $[Amount] - Approved by human
   ```

3. Update task with Odoo payment ID:
   ```yaml
   status: completed
   payment_recorded: true
   odoo_payment_id: [ID from Odoo]
   approved_by: human
   approved_at: [ISO timestamp]
   ```

4. Move task to `vault/Done/`

5. Update Dashboard with completion

## Output Format

### Auto-Approved Payment (≤ $100):

```markdown
---
id: payment_client_a_20260304
source: whatsapp
type: accounting
priority: medium
status: completed
payment_recorded: true
payment_amount: 75.00
client_name: "Client A"
odoo_payment_id: "PAY/2026/0123"
auto_approved: true
created_at: 2026-03-04T14:00:00Z
completed_at: 2026-03-04T14:01:15Z
---

# Payment Received: Client A

## Payment Recorded ✓

**Client**: Client A
**Amount**: $75.00
**Payment ID**: PAY/2026/0123
**Status**: Posted to Odoo (Auto-approved)

### Payment Details
- **Method**: Bank Transfer
- **Date**: 2026-03-04
- **Invoice**: INV/2026/0042
- **Transaction ID**: TXN789456123

**Status**: Invoice INV/2026/0042 marked as PAID

### Action Log
- [2026-03-04T14:00:12Z] Payment recorded in Odoo
- [2026-03-04T14:00:15Z] Invoice updated to PAID status
- [2026-03-04T14:01:15Z] Task completed
```

### Approval Required Payment (> $100):

```markdown
---
id: payment_client_b_20260304
source: email
type: accounting
priority: high
requires_approval: true
approval_reason: "Payment amount exceeds $100 threshold"
approval_requested: 2026-03-04T14:00:00Z
approval_expires: 2026-03-05T14:00:00Z
approval_category: financial
payment_amount: 2500.00
client_name: "Client B"
status: pending_approval
---

# Payment Received: Client B - $2,500

## Payment Approval Request

**Action Type**: Financial
**Amount**: $2,500.00
**Requested**: 2026-03-04T14:00:00Z
**Expires**: 2026-03-05T14:00:00Z

### Payment Details
- **Client**: Client B
- **Amount**: $2,500.00
- **Payment Method**: Bank Transfer
- **Payment Date**: 2026-03-04
- **Invoice Reference**: INV/2026/0098
- **Transaction ID**: WIRE20260304789

### Verification
- ✅ Amount matches invoice INV/2026/0098 ($2,500.00)
- ✅ Payment method: Bank transfer (accepted)
- ✅ Client identity verified via email confirmation
- ✅ Bank transaction confirmed in business account

### Rationale
Final payment for website redesign project (Invoice INV/2026/0098). Client paid via bank transfer as agreed. This completes the project payment (50% upfront already received, this is remaining 50%).

### Expected Outcome
- Payment posted to Odoo accounting system
- Invoice INV/2026/0098 marked as PAID
- Accounts receivable cleared for Client B
- $2,500 cash inflow recorded for Q1 2026

### Risks
- **Risk**: Bank transfer could be reversed or fraudulent
  - Mitigation: Wait 2-3 business days for bank clearance before marking invoice as paid
- **Risk**: Payment amount discrepancy
  - Mitigation: Amount verified to match invoice exactly

---

**To Approve**: Move this file to `vault/Approved/`
**To Reject**: Move this file to `vault/Rejected/`
**To Modify**: Edit the payment details and re-request

**Note**: This approval request expires in 24 hours.
```

## Quality Criteria

- **Accuracy**: Payment amount matches received amount
- **Verification**: Payment source and method verified
- **Completeness**: All required payment fields present
- **Traceability**: Linked to invoice or client account
- **Timeliness**: Payment recorded promptly after receipt
- **Reconciliation**: Matches bank statement or payment notification
- **Compliance**: Follows company payment policies

## Example Input

```markdown
---
id: task_payment_client_a_20260304
source: whatsapp
type: accounting
priority: medium
---

# Task: Record Payment from Client A

Client A just transferred $75 for invoice INV/2026/0042. Bank transfer received today.
Transaction ID: TXN789456123
```

## Example Output

Task moved to `vault/Done/` with payment recorded:

```yaml
---
id: task_payment_client_a_20260304
source: whatsapp
type: accounting
priority: medium
status: completed
payment_recorded: true
payment_amount: 75.00
client_name: "Client A"
odoo_payment_id: "PAY/2026/0123"
invoice_reference: "INV/2026/0042"
auto_approved: true
created_at: 2026-03-04T14:00:00Z
completed_at: 2026-03-04T14:01:15Z
---

# Payment Recorded ✓

**Client**: Client A
**Amount**: $75.00
**Payment ID**: PAY/2026/0123
**Status**: Posted to Odoo

[Payment details as shown above]
```

## Important Notes

- **$100 threshold is strict** - amounts over $100 ALWAYS require approval
- **Verify payment source** - ensure payment is legitimate before recording
- **Match to invoice** - link payment to specific invoice when possible
- **Check for overpayment/underpayment** - document any discrepancies
- **Wait for bank clearance** - for large amounts, wait for bank confirmation
- **Log all actions** - maintain audit trail for financial transactions
- **Update Dashboard** - keep business owner informed of payment activity
- **Handle errors gracefully** - if Odoo connection fails, queue for retry

## Success Criteria

Payment recording is successful when:
- ✅ All required payment fields validated
- ✅ Amount is positive number
- ✅ Client name is specified
- ✅ Payment method is valid and accepted
- ✅ Payment date is reasonable (not future)
- ✅ Approval workflow followed correctly (auto or manual)
- ✅ Payment posted to Odoo (or approval requested)
- ✅ Odoo payment ID captured
- ✅ Invoice updated if applicable
- ✅ Action logged with timestamp
- ✅ Task status updated correctly
- ✅ Dashboard updated with payment activity
- ✅ Audit trail maintained

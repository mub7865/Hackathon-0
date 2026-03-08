---
name: "query-transactions"
description: "Query and retrieve financial transactions from Odoo accounting system. Use when task requires viewing transaction history, generating financial reports, or analyzing business finances."
---

# Query Transactions Skill

## When to Use This Skill

Use this skill when:
- Need to view financial transaction history
- Task asks for revenue/expense summary
- Generating financial reports
- Checking payment status
- Analyzing business finances
- Task mentions "show transactions", "financial report", or "accounting summary"

## Procedure

### Step 1: Understand Query Requirements

1. Read task to identify:
   - **Time Period**: Date range (this week, last month, Q1, etc.)
   - **Transaction Type**: Invoices, payments, expenses, or all
   - **Client/Vendor**: Specific party or all
   - **Amount Range**: Min/max amounts (optional)
   - **Status**: Paid, unpaid, overdue (optional)

### Step 2: Query Odoo

```python
from src.utils.odoo_methods import search_transactions

query_params = {
    "start_date": "[YYYY-MM-DD]",
    "end_date": "[YYYY-MM-DD]",
    "transaction_type": "invoice|payment|expense|all",
    "client_name": "[Client]" or None,
    "status": "paid|unpaid|overdue" or None
}

transactions = search_transactions(query_params)
```

### Step 3: Format Results

Create summary in task file:

```markdown
## Financial Transactions Report

**Period**: [Start Date] to [End Date]
**Generated**: [ISO timestamp]

### Summary
- **Total Revenue**: $[Total invoices]
- **Total Expenses**: $[Total expenses]
- **Net Income**: $[Revenue - Expenses]
- **Outstanding**: $[Unpaid invoices]

### Transactions

#### Invoices
| Date | Client | Amount | Status | Invoice ID |
|------|--------|--------|--------|------------|
| [Date] | [Client] | $[Amount] | [Paid/Unpaid] | [ID] |

#### Payments
| Date | Client | Amount | Method | Payment ID |
|------|--------|--------|--------|------------|
| [Date] | [Client] | $[Amount] | [Method] | [ID] |

#### Expenses
| Date | Vendor | Amount | Category | Expense ID |
|------|--------|--------|----------|------------|
| [Date] | [Vendor] | $[Amount] | [Category] | [ID] |
```

### Step 4: Update Task

```yaml
status: completed
query_executed: true
transactions_found: [Count]
total_revenue: [Amount]
total_expenses: [Amount]
```

Move to `vault/Done/`

## Success Criteria

- ✅ Query parameters validated
- ✅ Transactions retrieved from Odoo
- ✅ Results formatted clearly
- ✅ Summary calculations correct
- ✅ Task completed

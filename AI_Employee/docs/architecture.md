# Atlas Architecture

**Version:** 1.0
**Last Updated:** March 6, 2026
**Status:** Production Ready

---

## Overview

Atlas is an autonomous AI employee system that combines communication automation with business operations capabilities: automated accounting, weekly CEO briefings, and resilient error recovery. The system maintains the human-in-the-loop philosophy while adding autonomous financial management.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Gold Tier System                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   Watchers   │───▶│ Orchestrator │───▶│   Actions    │      │
│  │              │    │              │    │              │      │
│  │ - Gmail      │    │ - Task Queue │    │ - Accounting │      │
│  │ - WhatsApp   │    │ - Ralph Loop │    │ - Briefing   │      │
│  │ - LinkedIn   │    │ - Scheduler  │    │ - Email      │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                    │                    │              │
│         ▼                    ▼                    ▼              │
│  ┌─────────────────────────────────────────────────────┐      │
│  │              Vault (File-Based State)                 │      │
│  │                                                        │      │
│  │  Needs_Action/ → Pending_Approval/ → Approved/ → Done/│      │
│  │                                                        │      │
│  │  Briefings/  |  Logs/  |  Dashboard.md               │      │
│  └──────────────────────────────────────────────────────┘      │
│         │                    │                    │              │
│         ▼                    ▼                    ▼              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │  Odoo ERP    │    │  Gmail API   │    │  WhatsApp    │      │
│  │  (JSON-RPC)  │    │              │    │  (Playwright)│      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. Orchestrator (`src/orchestrator/`)

**Purpose:** Central coordination of all system activities

**Components:**
- `orchestrator.py` - Main orchestration loop (5-minute cycles)
- `accounting_orchestrator.py` - Accounting task processor
- `ralph_wiggum.py` - Multi-step task completion engine

**Responsibilities:**
- Scan vault folders for new tasks
- Route tasks to appropriate action handlers
- Manage task lifecycle (Needs_Action → Done)
- Update Dashboard.md with system status
- Handle stuck tasks (max 10 iterations)

**Key Features:**
- **Ralph Wiggum Loop:** Autonomous multi-step task completion
  - Max 10 iterations per task
  - Automatic approval detection
  - Stuck task flagging
  - Error history tracking

### 2. Actions (`src/actions/`)

**Purpose:** Execute business operations with approval workflow

**Modules:**

#### Accounting Actions (`accounting_actions.py`)
- `process_invoice_request()` - Create customer invoices
- `process_payment_request()` - Record customer payments
- `process_expense_request()` - Track vendor bills
- `process_approved_transaction()` - Execute approved transactions
- **Approval Threshold:** $100 (configurable)

#### Briefing Actions (`briefing_actions.py`)
- `generate_briefing()` - Aggregate weekly data
- `render_briefing_markdown()` - Format report
- `save_briefing()` - Write to vault/Briefings/
- **Schedule:** Sunday 11:00 PM (manual trigger available)

### 3. Models (`src/models/`)

**Purpose:** Domain entities with business logic

**Entities:**

#### Business Transaction (`transaction.py`)
```python
@dataclass
class BusinessTransaction:
    transaction_id: str
    transaction_type: TransactionType  # INVOICE, PAYMENT, EXPENSE
    amount: float
    party: str  # Customer/vendor
    status: TransactionStatus  # DRAFT → APPROVED → POSTED → PAID
    approval_threshold: float = 100.00
    audit_trail: List[Dict]
```

#### CEO Briefing (`briefing.py`)
```python
@dataclass
class CEOBriefing:
    briefing_id: str
    period_start: date
    period_end: date
    revenue_summary: RevenueSummary
    expense_summary: ExpenseSummary
    task_metrics: TaskMetrics
    bottlenecks: List[Bottleneck]
    recommendations: List[Recommendation]
```

#### Multi-Step Task (`task_utils.py`)
```python
@dataclass
class MultiStepTask:
    task_id: str
    current_iteration: int
    max_iterations: int = 10
    sub_tasks: List[SubTask]
    status: TaskStatus
    error_history: List[Dict]
```

### 4. Utilities (`src/utils/`)

**Purpose:** Shared infrastructure and integrations

**Key Utilities:**

#### Odoo Client (`odoo_client.py`)
- JSON-RPC 2.0 protocol
- Authentication with session management
- Rate limiting (100 req/min)
- CRUD operations (create, read, search_read, write, unlink)

#### Odoo Methods (`odoo_methods.py`)
- `create_invoice()` - Create account.move (out_invoice)
- `record_payment()` - Create account.payment (inbound)
- `create_expense()` - Create account.move (in_invoice)
- `search_transactions()` - Query with filters
- `get_weekly_summary()` - Aggregate financial data

#### Analytics (`analytics_utils.py`)
- `calculate_revenue_summary()` - Revenue by source, WoW change
- `calculate_expense_summary()` - Expenses by category
- `calculate_task_metrics()` - Completion stats
- `detect_bottlenecks()` - Tasks >150% expected duration
- `analyze_subscriptions()` - Recurring cost analysis
- `generate_recommendations()` - Proactive suggestions

#### Retry Handler (`retry_handler.py`)
- `@with_retry` decorator - Exponential backoff (1-2-4 seconds)
- Circuit breaker pattern (5 consecutive failures)
- Error classification (transient, permanent, authentication)
- Action queue for graceful degradation

#### Error Utils (`error_utils.py`)
- Error classification by type
- Error logging to vault/Logs/errors.json
- Human alert detection
- Error recovery recommendations

#### Dashboard Utils (`dashboard_utils.py`)
- Update task statistics
- Update orchestrator status
- Add activity entries
- Real-time system visibility

### 5. MCP Servers (`src/mcp/`)

**Purpose:** Expose operations as MCP tools for Claude Code

#### Accounting Server (`accounting_server.py`)
**Tools:**
- `create_invoice` - Create customer invoice
- `record_payment` - Record customer payment
- `create_expense` - Create vendor bill
- `search_transactions` - Query financial data
- `get_weekly_summary` - Revenue/expense summary
- `get_pending_approvals` - List pending transactions
- `approve_transaction` - Approve and execute

---

## Data Flow

### 1. Accounting Workflow

```
Task File Created
    ↓
Orchestrator Detects (5-min cycle)
    ↓
Parse Transaction Details
    ↓
Validate Data (amount > 0, party exists, etc.)
    ↓
Check Approval Threshold
    ├─ Amount ≤ $100 → Execute Immediately
    │   ↓
    │   Authenticate with Odoo
    │   ↓
    │   Create Invoice/Payment/Expense
    │   ↓
    │   Post to Odoo (make official)
    │   ↓
    │   Move to Done/
    │
    └─ Amount > $100 → Require Approval
        ↓
        Move to Pending_Approval/
        ↓
        Wait for Human Approval
        ↓
        Move to Approved/
        ↓
        Execute Transaction
        ↓
        Move to Done/
```

### 2. CEO Briefing Workflow

```
Sunday 11:00 PM (or Manual Trigger)
    ↓
Calculate Week Dates (Monday-Sunday)
    ↓
Authenticate with Odoo
    ↓
Query Transactions (current + previous week)
    ↓
Calculate Revenue Summary
    ├─ Total revenue
    ├─ Revenue by source
    └─ Week-over-week % change
    ↓
Calculate Expense Summary
    ├─ Total expenses
    └─ Expenses by category
    ↓
Read Completed Tasks (vault/Done/)
    ├─ Count completed
    ├─ Average completion time
    └─ Tasks requiring approval
    ↓
Detect Bottlenecks (actual > 150% expected)
    ↓
Analyze Subscriptions (recurring charges)
    ↓
Generate Recommendations
    ├─ Revenue alerts (>20% change)
    ├─ Profitability warnings
    ├─ Operational efficiency
    └─ Cost optimization
    ↓
Render Markdown Report
    ↓
Save to vault/Briefings/YYYY-MM-DD_briefing.md
    ↓
Update Dashboard.md
```

### 3. Error Recovery Workflow

```
Operation Fails
    ↓
Classify Error Type
    ├─ Transient (network, timeout) → Retry
    ├─ Permanent (not found, invalid) → Alert Human
    └─ Authentication (expired token) → Alert Human
    ↓
If Transient:
    ↓
    Retry with Exponential Backoff
    ├─ Attempt 1: Wait 1 second
    ├─ Attempt 2: Wait 2 seconds
    └─ Attempt 3: Wait 4 seconds
    ↓
    If Still Failing:
        ↓
        Circuit Breaker Opens (after 5 consecutive)
        ↓
        Queue Action for Later
        ↓
        Alert Human
```

---

## Approval Workflow

### Threshold-Based Approval

**Configuration:** `config/odoo_config.yaml`
```yaml
approval_threshold: 100.00  # USD
```

**Logic:**
- **Amount ≤ $100:** Automatic execution
- **Amount > $100:** Human approval required

**Workflow States:**
```
needs_action → pending_approval → approved → done
                      ↓
                  (rejected) → cancelled
```

**Approval Process:**
1. Task file moved to `Pending_Approval/`
2. Frontmatter updated with approval metadata
3. Human reviews and approves (via MCP tool or manual)
4. Task moved to `Approved/`
5. Transaction executed in Odoo
6. Task moved to `Done/`

---

## Error Recovery

### Retry Strategy

**Exponential Backoff:**
- Base delay: 1 second
- Max delay: 60 seconds
- Exponential base: 2.0
- Jitter: Random 50-100% of calculated delay

**Example:**
```
Attempt 1: Fail → Wait 1.0s
Attempt 2: Fail → Wait 2.0s
Attempt 3: Fail → Wait 4.0s
Max Attempts Reached → Alert Human
```

### Circuit Breaker

**Thresholds:**
- Open after: 5 consecutive failures
- Timeout: 5 minutes
- Close after: 3 consecutive successes

**States:**
```
Closed (Normal) → Open (Failing) → Half-Open (Testing) → Closed
```

### Graceful Degradation

**Action Queue:**
- When service unavailable, queue actions
- Retry when service recovers
- Stored in `vault/Logs/action_queue.json`

---

## Security

### Credentials Management

**Storage:** `.env` file (not committed to git)
```bash
ODOO_URL=http://localhost:8069
ODOO_DB=AI_Employee_hackathon_0
ODOO_USERNAME=***
ODOO_PASSWORD=***
```

**Access Control:**
- Odoo credentials required for all financial operations
- Session-based authentication (no password in logs)
- Audit trail for all transactions

### Audit Trail

**Transaction Audit:**
```python
audit_trail = [
    {
        'timestamp': '2026-02-26T14:30:00',
        'action': 'created',
        'user': 'system',
        'details': 'Invoice request received'
    },
    {
        'timestamp': '2026-02-26T14:35:00',
        'action': 'approved',
        'user': 'CEO',
        'details': 'Approved via MCP tool'
    },
    {
        'timestamp': '2026-02-26T14:36:00',
        'action': 'posted',
        'user': 'system',
        'details': 'Posted to Odoo: INV/2026/0042'
    }
]
```

### Input Validation

**Transaction Validation:**
- Amount > 0
- Party (customer/vendor) required
- Description required
- Category required for expenses
- Date format validation

---

## Performance

### Orchestrator Cycle

**Frequency:** 5 minutes (configurable)

**Cycle Time Breakdown:**
- Scan vault folders: ~100ms
- Parse task files: ~50ms per file
- Process accounting tasks: ~2-5s per task (Odoo API)
- Update dashboard: ~50ms

**Optimization:**
- Parallel task processing where possible
- Cached Odoo authentication (session reuse)
- Rate limiting to prevent API throttling

### Odoo Integration

**Rate Limits:**
- Max 100 requests/minute (configurable)
- Automatic rate limiting enforcement
- Request queuing when limit reached

**Response Times:**
- Authentication: ~2-3s
- Create invoice: ~3-5s
- Search transactions: ~1-2s
- Weekly summary: ~5-10s

---

## Deployment

### Prerequisites

1. **Odoo Community Edition v19+**
   - Accounting module installed
   - Database configured
   - Test data created

2. **Python 3.13+**
   - Dependencies: `pip install -r requirements.txt`
   - Key packages: odoorpc, requests, playwright, pyyaml

3. **Environment Configuration**
   - `.env` file with Odoo credentials
   - `config/odoo_config.yaml` with approval threshold

### Running the System

**Manual Briefing Generation:**
```bash
python generate_briefing.py
```

**Accounting Orchestrator:**
```bash
python src/orchestrator/accounting_orchestrator.py
```

**MCP Server:**
```bash
python src/mcp/accounting_server.py
```

---

## Monitoring

### Dashboard

**Location:** `vault/Dashboard.md`

**Metrics:**
- Task counts (Needs Action, Pending Approval, Done)
- Orchestrator status (cycle count, last run)
- Today's processing stats
- Recent activity log

### Logs

**Error Logs:** `vault/Logs/errors.json`
- Error classification
- Retry attempts
- Resolution status
- Stack traces

**Action Queue:** `vault/Logs/action_queue.json`
- Queued actions when services unavailable
- Retry status

---

## Future Enhancements

### Phase 4: Social Media (Not Implemented)
- Facebook/Instagram posting automation
- Engagement monitoring
- Approval workflow for posts

### Potential Improvements
- Real-time notifications (email/Slack alerts)
- Mobile app for approvals
- Advanced analytics dashboard
- Multi-currency support
- Budget tracking and forecasting
- Integration with additional ERPs (QuickBooks, Xero)

---

## Troubleshooting

### Common Issues

**1. Odoo Connection Failed**
- Check Odoo is running: `curl http://localhost:8069`
- Verify credentials in `.env`
- Check database name matches

**2. Authentication Error**
- Verify username/password correct
- Check user has Accounting access in Odoo
- Try manual login via browser

**3. Transaction Not Posted**
- Check amount validation (must be > 0)
- Verify party (customer/vendor) exists in Odoo
- Check Odoo logs for validation errors

**4. Briefing Generation Failed**
- Ensure Odoo accessible
- Check vault/Done/ folder exists
- Verify date range is valid (7 days)

---

## References

- [Odoo JSON-RPC API Documentation](https://www.odoo.com/documentation/19.0/developer/reference/external_api.html)
- [Specification](../specs/001-autonomous-employee/spec.md)
- [Implementation Plan](../specs/001-autonomous-employee/plan.md)
- [Tasks](../specs/001-autonomous-employee/tasks.md)

# Configuration Guide - Atlas AI Employee

Complete configuration reference for all Atlas components.

---

## Table of Contents

1. [Environment Variables](#environment-variables)
2. [Odoo Configuration](#odoo-configuration)
3. [PM2 Configuration](#pm2-configuration)
4. [Vault Structure](#vault-structure)
5. [Advanced Settings](#advanced-settings)

---

## Environment Variables

### Required Variables

Create a `.env` file in the `silver/` directory:

```env
# Vault Configuration (Required)
VAULT_PATH=./vault

# Anthropic API (Required for AI processing)
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

### Odoo Integration (Optional)

```env
# Odoo Connection
ODOO_URL=http://localhost:8069
ODOO_DB=your_database_name
ODOO_USERNAME=admin
ODOO_PASSWORD=your_secure_password

# Odoo API Settings
ODOO_TIMEOUT=30
ODOO_RETRY_ATTEMPTS=3
```

### Gmail Integration (Optional)

```env
# Gmail API Credentials
GMAIL_CREDENTIALS_PATH=./.credentials/gmail-credentials.json
GMAIL_TOKEN_PATH=./.credentials/gmail-token.pickle

# Gmail Watcher Settings
GMAIL_CHECK_INTERVAL=120  # seconds
GMAIL_MAX_RESULTS=10
```

### WhatsApp Integration (Optional)

```env
# WhatsApp Session
WHATSAPP_SESSION=./sessions/whatsapp_session

# WhatsApp Watcher Settings
WHATSAPP_CHECK_INTERVAL=30  # seconds
WHATSAPP_HEADLESS=true
```

### LinkedIn Integration (Optional)

```env
# LinkedIn Credentials
LINKEDIN_EMAIL=your_email@example.com
LINKEDIN_PASSWORD=your_secure_password

# LinkedIn Session
LINKEDIN_SESSION=./sessions/linkedin_session

# LinkedIn Watcher Settings
LINKEDIN_CHECK_INTERVAL=120  # seconds
LINKEDIN_HEADLESS=true
```

### System Settings

```env
# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
LOG_FILE=./vault/Logs/system.log

# Orchestrator
ORCHESTRATOR_CYCLE_INTERVAL=300  # seconds (5 minutes)
MAX_TASK_ITERATIONS=10

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60  # seconds

# Security
APPROVAL_THRESHOLD=100.00  # USD
SESSION_TIMEOUT=3600  # seconds
```

---

## Odoo Configuration

### Configuration File

Edit `silver/config/odoo_config.yaml`:

```yaml
# Odoo Connection Settings
connection:
  url: "http://localhost:8069"
  database: "your_database"
  username: "admin"
  timeout: 30

# Approval Workflow
approval:
  threshold: 100.00  # Transactions above this require manual approval
  auto_approve_below: true
  notification_email: "admin@example.com"

# Rate Limiting
rate_limits:
  max_requests_per_minute: 100
  max_concurrent_requests: 5
  retry_attempts: 3
  retry_delay: 2  # seconds

# Transaction Settings
transactions:
  default_currency: "USD"
  default_payment_term: "immediate"
  invoice_prefix: "INV"
  payment_prefix: "PAY"
  expense_prefix: "EXP"

# Audit Trail
audit:
  enabled: true
  log_all_transactions: true
  retention_days: 365

# Briefing Settings
briefing:
  schedule: "Sunday 23:00"  # Weekly briefing time
  timezone: "UTC"
  include_charts: false
  email_recipients: []
```

### Odoo Modules Required

Ensure these modules are installed in Odoo:

- **Accounting** (`account`)
- **Invoicing** (`account_invoicing`)
- **Contacts** (`contacts`)
- **Sales** (`sale_management`) - Optional

---

## PM2 Configuration

### Ecosystem File

Edit `silver/ecosystem.config.js`:

```javascript
module.exports = {
  apps: [
    {
      name: 'atlas-orchestrator',
      script: 'run_orchestrator.py',
      interpreter: 'path/to/venv/Scripts/python.exe',
      cwd: 'path/to/silver',
      env: {
        PYTHONPATH: 'path/to/silver',
        VAULT_PATH: 'path/to/silver/vault'
      },
      error_file: 'logs/orchestrator-error.log',
      out_file: 'logs/orchestrator-out.log',
      time: true,
      autorestart: true,
      max_restarts: 10,
      min_uptime: '10s'
    },
    {
      name: 'atlas-file-watcher',
      script: 'src/watchers/file_watcher.py',
      interpreter: 'path/to/venv/Scripts/python.exe',
      cwd: 'path/to/silver',
      env: {
        PYTHONPATH: 'path/to/silver',
        VAULT_PATH: 'path/to/silver/vault'
      },
      error_file: 'logs/file-watcher-error.log',
      out_file: 'logs/file-watcher-out.log',
      time: true,
      autorestart: true
    }
    // Add other watchers as needed
  ]
};
```

### PM2 Commands

```bash
# Start all services
pm2 start ecosystem.config.js

# Save configuration
pm2 save

# Setup auto-start on boot
pm2 startup

# Monitor services
pm2 monit

# View logs
pm2 logs

# Restart services
pm2 restart all
```

---

## Vault Structure

### Required Folders

```
vault/
├── Needs_Action/       # New tasks detected by watchers
├── Pending_Approval/   # Tasks requiring human approval
├── Approved/           # Approved tasks ready for execution
├── Done/               # Completed tasks
├── Rejected/           # Rejected tasks
├── Logs/               # System logs and error logs
├── Briefings/          # Weekly CEO briefings
└── Dashboard.md        # Real-time system status
```

### Task File Format

All task files use YAML frontmatter + Markdown body:

```yaml
---
status: needs_action
id: unique_task_id
source: gmail|whatsapp|linkedin|manual
type: invoice|payment|expense|email|general
priority: low|medium|high|urgent
created_at: 2026-03-06T12:00:00Z
---

# Task Title

Task description and details go here.

## Additional Information

- Item 1
- Item 2
```

### Dashboard Format

`vault/Dashboard.md` is auto-updated by the orchestrator:

```markdown
# Atlas Dashboard

**Last Updated:** 2026-03-06 12:00:00

## Task Statistics
- Needs Action: 0
- Pending Approval: 2
- Done: 150

## Orchestrator Status
- Status: Running
- Last Cycle: 2026-03-06 11:55:00
- Cycle Time: 4.2s

## Recent Activity
- [12:00] Invoice created for Client A ($500)
- [11:45] Payment recorded from Client B ($1,200)
- [11:30] Expense logged: Office supplies ($45)
```

---

## Advanced Settings

### Custom Action Handlers

Create custom action handlers in `src/actions/`:

```python
# src/actions/custom_action.py
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def process_custom_task(task_file: Path) -> dict:
    """
    Process a custom task type.

    Args:
        task_file: Path to task file

    Returns:
        dict: Result with status and details
    """
    logger.info(f"Processing custom task: {task_file.name}")

    # Your custom logic here

    return {
        "status": "success",
        "message": "Custom task completed"
    }
```

Register in `src/orchestrator/orchestrator.py`:

```python
from src.actions.custom_action import process_custom_task

# In orchestrator's task routing
if task_type == "custom":
    result = process_custom_task(task_file)
```

### Custom Watchers

Create custom watchers in `src/watchers/`:

```python
# src/watchers/custom_watcher.py
import time
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def watch_custom_source():
    """Watch a custom data source for new tasks."""
    vault_path = Path("./vault")

    while True:
        try:
            # Check your custom source
            # Create task files in vault/Needs_Action/

            logger.info("Custom watcher cycle complete")
            time.sleep(60)  # Check every minute

        except Exception as e:
            logger.error(f"Custom watcher error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    watch_custom_source()
```

Add to `ecosystem.config.js`:

```javascript
{
  name: 'atlas-custom-watcher',
  script: 'src/watchers/custom_watcher.py',
  // ... other settings
}
```

### Security Hardening

#### Input Validation

All user inputs are validated in `src/utils/security_utils.py`:

```python
from src.utils.security_utils import (
    validate_amount,
    validate_date,
    validate_party_name,
    sanitize_file_path
)

# Validate transaction amount
amount = validate_amount(user_input)  # Raises ValueError if invalid

# Validate date
date = validate_date(user_date)  # Raises ValueError if invalid

# Sanitize party name (prevent XSS)
party = validate_party_name(user_name)

# Sanitize file paths (prevent directory traversal)
safe_path = sanitize_file_path(user_path, vault_path)
```

#### Rate Limiting

Configure in `config/odoo_config.yaml`:

```yaml
rate_limits:
  max_requests_per_minute: 100
  max_concurrent_requests: 5
  retry_attempts: 3
```

#### Credentials Security

- Never commit `.env` file
- Use environment variables for all secrets
- Rotate API keys regularly
- Use read-only Odoo user when possible

---

## Troubleshooting

### Configuration Issues

**Problem:** Services won't start

```bash
# Check environment variables
cat .env

# Verify Python path
which python
python --version

# Check PM2 configuration
pm2 describe atlas-orchestrator
```

**Problem:** Odoo connection fails

```bash
# Test Odoo connection
curl http://localhost:8069

# Test authentication
python -c "from src.utils.odoo_client import OdooClient; OdooClient().authenticate()"

# Check Odoo logs
# (Odoo logs location depends on installation)
```

**Problem:** Tasks not processing

```bash
# Check orchestrator logs
pm2 logs atlas-orchestrator --lines 50

# Check vault permissions
ls -la vault/

# Verify task file format
cat vault/Needs_Action/task_file.md
```

---

## Performance Tuning

### Orchestrator Cycle Time

Adjust in `.env`:

```env
# Faster cycles (more responsive, higher CPU)
ORCHESTRATOR_CYCLE_INTERVAL=60  # 1 minute

# Slower cycles (less responsive, lower CPU)
ORCHESTRATOR_CYCLE_INTERVAL=600  # 10 minutes
```

### Watcher Intervals

Adjust in `.env`:

```env
# Gmail (API rate limits apply)
GMAIL_CHECK_INTERVAL=120  # 2 minutes recommended

# WhatsApp (browser automation, resource intensive)
WHATSAPP_CHECK_INTERVAL=30  # 30 seconds minimum

# LinkedIn (API rate limits apply)
LINKEDIN_CHECK_INTERVAL=120  # 2 minutes recommended
```

### Memory Optimization

In `ecosystem.config.js`:

```javascript
{
  name: 'atlas-orchestrator',
  max_memory_restart: '500M',  // Restart if memory exceeds 500MB
  // ...
}
```

---

## Backup Configuration

### Automated Backups

Create backup script `scripts/backup.sh`:

```bash
#!/bin/bash

BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup vault
tar -czf "$BACKUP_DIR/vault_$DATE.tar.gz" vault/

# Backup configuration
cp .env "$BACKUP_DIR/env_$DATE.backup"
cp config/odoo_config.yaml "$BACKUP_DIR/odoo_config_$DATE.yaml"

# Keep only last 30 days
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete
```

Schedule with cron:

```bash
# Daily backup at 2 AM
0 2 * * * /path/to/silver/scripts/backup.sh
```

---

## Next Steps

- **Quick Start**: See [QUICK_START.md](QUICK_START.md)
- **Architecture**: See [architecture.md](architecture.md)
- **Deployment**: See [deployment-checklist.md](deployment-checklist.md)

---

**Configuration Complete!** Your Atlas system is ready to use.

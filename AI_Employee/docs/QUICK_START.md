# Quick Start Guide - Atlas AI Employee

Get Atlas up and running in 30 minutes.

---

## Prerequisites

Before you begin, ensure you have:

- **Python 3.13+** installed
- **Node.js 18+** and npm installed
- **Git** installed
- **Chrome/Chromium** browser installed
- **Windows 10+** or **Linux/macOS**

---

## Installation

### 1. Clone Repository

```bash
git clone <your-repo-url>
cd hackathon-0/silver
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 4. Install PM2 (Process Manager)

```bash
npm install -g pm2
```

---

## Configuration

### 1. Create Environment File

Copy the example environment file:

```bash
cp .env.example .env
```

### 2. Configure Basic Settings

Edit `.env` file with your settings:

```env
# Vault Configuration
VAULT_PATH=./vault

# Anthropic API (for AI processing)
ANTHROPIC_API_KEY=your_api_key_here

# Odoo Configuration (optional for accounting)
ODOO_URL=http://localhost:8069
ODOO_DB=your_database_name
ODOO_USERNAME=admin
ODOO_PASSWORD=your_password
```

### 3. Create Vault Structure

```bash
mkdir -p vault/Needs_Action
mkdir -p vault/Pending_Approval
mkdir -p vault/Approved
mkdir -p vault/Done
mkdir -p vault/Rejected
mkdir -p vault/Logs
mkdir -p vault/Briefings
```

Create Dashboard file:

```bash
echo "# Atlas Dashboard" > vault/Dashboard.md
```

---

## Start the System

### Option 1: Start All Services (Recommended)

```bash
pm2 start ecosystem.config.js
pm2 status
```

You should see all services running:
- `atlas-orchestrator`
- `atlas-gmail-watcher` (if Gmail configured)
- `atlas-whatsapp-watcher` (if WhatsApp configured)
- `atlas-linkedin-watcher` (if LinkedIn configured)
- `atlas-file-watcher`

### Option 2: Start Individual Services

```bash
# Start orchestrator only
python run_orchestrator.py

# Start file watcher only
python src/watchers/file_watcher.py --vault ./vault
```

---

## Test the System

### 1. Create a Test Task

Create a file in `vault/Needs_Action/test_task.md`:

```yaml
---
status: needs_action
id: test_task_001
source: manual
type: general
priority: low
created_at: 2026-03-06T12:00:00Z
---

# Test Task

This is a test task to verify the system is working.

Please acknowledge this task.
```

### 2. Check Processing

Wait 5 minutes (orchestrator cycle time) and check:

```bash
# View orchestrator logs
pm2 logs atlas-orchestrator --lines 20

# Check if task moved to Done
ls vault/Done/
```

### 3. View Dashboard

```bash
cat vault/Dashboard.md
```

You should see task statistics updated.

---

## Next Steps

### For Communication Monitoring

1. **Gmail Setup**: See [GMAIL_OAUTH_SETUP_STEPS.md](GMAIL_OAUTH_SETUP_STEPS.md)
2. **WhatsApp Setup**: See [WHATSAPP_MCP_SETUP.md](WHATSAPP_MCP_SETUP.md)
3. **LinkedIn Setup**: Configure credentials in `.env`

### For Accounting Integration

1. **Install Odoo**: See [Odoo Setup Guide](https://www.odoo.com/documentation)
2. **Configure Odoo**: See `config/odoo_config.yaml`
3. **Test Integration**: Create test invoice in `vault/Needs_Action/`

### For Production Deployment

1. **Security Review**: See [deployment-checklist.md](deployment-checklist.md)
2. **Configure Backups**: Set up vault backup schedule
3. **Monitor Logs**: Use `pm2 logs` and `pm2 monit`

---

## Common Commands

```bash
# View all services
pm2 status

# View logs
pm2 logs
pm2 logs atlas-orchestrator

# Restart services
pm2 restart all
pm2 restart atlas-orchestrator

# Stop services
pm2 stop all

# Delete services
pm2 delete all

# Save PM2 configuration
pm2 save

# Setup PM2 to start on boot
pm2 startup
```

---

## Troubleshooting

### Services Won't Start

```bash
# Check Python version
python --version  # Should be 3.13+

# Check if port is in use
netstat -ano | findstr :8069  # Windows
lsof -i :8069  # Linux/Mac

# Check logs for errors
pm2 logs --err
```

### Tasks Not Processing

```bash
# Check orchestrator is running
pm2 status | grep orchestrator

# Check vault permissions
ls -la vault/

# Manually trigger orchestrator
python run_orchestrator.py
```

### Need Help?

- Check [Troubleshooting Guide](architecture.md#troubleshooting)
- Review [Architecture Documentation](architecture.md)
- Check logs in `vault/Logs/`

---

## What's Next?

- **Daily Operations**: See [DAILY_OPERATIONS.md](../DAILY_OPERATIONS.md)
- **Architecture**: See [architecture.md](architecture.md)
- **Advanced Configuration**: See [Configuration Guide](CONFIGURATION.md)

---

**System Status**: ✅ Ready to use!

**Support**: Check documentation or review logs for issues.

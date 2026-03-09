# Atlas - Autonomous AI Employee System

> An intelligent, autonomous system that monitors communications (Gmail, WhatsApp, LinkedIn), manages business accounting, and generates weekly intelligence reports - all with human-in-the-loop oversight.

[![Status](https://img.shields.io/badge/status-production-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.13+-blue)]()
[![License](https://img.shields.io/badge/license-MIT-blue)]()

---

## 📖 Overview

Atlas is an autonomous AI employee system that acts as your digital assistant, monitoring multiple communication channels, managing business finances, and providing weekly intelligence reports. The system operates 24/7 with human oversight for sensitive decisions.

### Key Capabilities

**Communication Monitoring:**
- Multi-Channel Monitoring: Gmail, WhatsApp Web, and LinkedIn
- AI-Powered Processing: Drafts contextual responses using AI analysis
- Human-in-the-Loop: Requires approval for sensitive actions
- Automated Execution: Sends emails, WhatsApp messages, and LinkedIn posts

**Business Operations:**
- Automated Accounting: Tracks invoices, payments, and expenses in Odoo ERP
- Approval Workflow: $100 threshold for automatic vs. manual approval
- Weekly CEO Briefing: Automated business intelligence reports every Sunday
- Error Recovery: Resilient retry logic with exponential backoff
- Multi-Step Tasks: Autonomous task completion with Ralph Wiggum loop

---

## 🚀 Quick Start

### Prerequisites

- Python 3.13+
- Node.js 18+ (for PM2)
- Chrome/Chromium browser
- Odoo Community Edition (optional, for accounting features)

### Installation

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 2. Install dependencies
pip install -r requirements.txt
playwright install chromium

# 3. Install PM2
npm install -g pm2

# 4. Configure environment
cp .env.example .env
# Edit .env with your settings

# 5. Create vault structure
mkdir -p vault/{Needs_Action,Pending_Approval,Approved,Done,Rejected,Logs,Briefings}
echo "# Atlas Dashboard" > vault/Dashboard.md

# 6. Start the system
pm2 start ecosystem.config.js
pm2 status
```

**📚 Detailed Setup Guide:** [docs/QUICK_START.md](docs/QUICK_START.md)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│              Communication Channels                  │
│  Gmail API  │  WhatsApp Web  │  LinkedIn  │  Files  │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
            ┌────────────────┐
            │    Watchers    │  (PM2 Services)
            └────────┬───────┘
                     │
                     ▼
            ┌────────────────┐
            │ Needs_Action/  │
            └────────┬───────┘
                     │
                     ▼
            ┌────────────────┐
            │  Orchestrator  │  (AI Processing)
            └────────┬───────┘
                     │
                     ▼
            ┌────────────────┐
            │Pending_Approval│ ← Human Review
            └────────┬───────┘
                     │
                     ▼
            ┌────────────────┐
            │   Approved/    │
            └────────┬───────┘
                     │
                     ▼
            ┌────────────────┐
            │    Execute     │  (Actions)
            └────────┬───────┘
                     │
                     ▼
            ┌────────────────┐
            │     Done/      │
            └────────────────┘
```

**📚 Detailed Architecture:** [docs/architecture.md](docs/architecture.md)

---

## ✨ Features

### Communication Monitoring
- 📧 **Gmail Integration**: Monitors inbox every 2 minutes via Gmail API
- 💬 **WhatsApp Automation**: Detects messages via WhatsApp Web (Playwright)
- 🔗 **LinkedIn Tracking**: Monitors notifications and messages
- 📁 **File Watching**: Processes manually created task files

### Business Accounting
- 💰 **Invoice Management**: Automatically creates customer invoices in Odoo
- 💳 **Payment Tracking**: Records customer payments with audit trail
- 📊 **Expense Recording**: Tracks vendor bills and subscriptions
- ✅ **Approval Workflow**: Transactions >$100 require human approval
- 🔍 **Transaction Search**: Query financial data by date, type, or partner
- 📈 **Odoo Integration**: Full JSON-RPC integration with Odoo Community Edition

### CEO Briefing
- 📊 **Weekly Reports**: Automated business intelligence every Sunday 11 PM
- 💵 **Financial Summary**: Revenue, expenses, net profit, profit margin
- 📈 **Trend Analysis**: Week-over-week revenue comparison (>20% alerts)
- ⏱️ **Bottleneck Detection**: Identifies tasks taking longer than expected
- 💡 **Cost Optimization**: Subscription analysis and recommendations
- 🎯 **Proactive Recommendations**: High/medium/low priority suggestions

### Intelligent Processing
- 🤖 **AI Draft Generation**: Creates contextual replies using AI
- 🏷️ **Task Classification**: Categorizes tasks by sensitivity and priority
- 📝 **Metadata Extraction**: Automatically extracts sender, subject, and context
- 🔍 **Keyword Detection**: Identifies urgent or sensitive content

### Workflow Management
- ✅ **Approval Workflow**: Routes sensitive tasks for human review
- 🔄 **Automated Execution**: Sends approved messages automatically
- 📊 **Real-time Dashboard**: Displays system status and statistics
- 📈 **Progress Tracking**: Monitors task lifecycle from detection to completion
- 🔁 **Ralph Wiggum Loop**: Autonomous multi-step task completion (max 10 iterations)
- 🛡️ **Error Recovery**: Exponential backoff retry (3 attempts, circuit breaker)

---

## 🛠️ Tech Stack

### Core Technologies
- **Python 3.13+** - Main programming language
- **PM2** - Process manager for 24/7 operation
- **Playwright** - Browser automation for WhatsApp Web
- **Gmail API** - Email monitoring and sending
- **Anthropic Claude** - AI processing and draft generation
- **Odoo Community Edition** - ERP system for accounting

### Key Libraries
- `playwright` - Browser automation
- `google-auth` - Gmail API authentication
- `odoorpc` - Odoo JSON-RPC client
- `pyyaml` - Configuration management
- `python-dotenv` - Environment variable management

### Infrastructure
- **File-based Storage** - Markdown files with YAML frontmatter
- **Obsidian Vault** - Task management and review interface
- **PM2 Ecosystem** - Service orchestration and monitoring

---

## 📁 Project Structure

```
silver/
├── src/
│   ├── orchestrator/          # Main orchestration logic
│   │   ├── orchestrator.py    # Core orchestrator (5-min cycles)
│   │   ├── accounting_orchestrator.py
│   │   └── ralph_wiggum.py    # Multi-step task engine
│   ├── actions/               # Business operations
│   │   ├── accounting_actions.py
│   │   ├── briefing_actions.py
│   │   ├── social_media_actions.py
│   │   ├── linkedin_action.py
│   │   └── whatsapp_action.py
│   ├── models/                # Domain entities
│   │   ├── transaction.py
│   │   ├── briefing.py
│   │   └── social_post.py
│   ├── utils/                 # Utilities
│   │   ├── odoo_client.py
│   │   ├── security_utils.py
│   │   ├── retry_handler.py
│   │   └── dashboard_utils.py
│   └── watchers/              # Channel monitors
│       ├── gmail_watcher.py
│       ├── whatsapp_watcher.py
│       ├── linkedin_watcher.py
│       └── file_watcher.py
├── vault/                     # Task management
│   ├── Needs_Action/         # New tasks
│   ├── Pending_Approval/     # Awaiting human review
│   ├── Approved/             # Ready for execution
│   ├── Done/                 # Completed tasks
│   ├── Logs/                 # System logs
│   ├── Briefings/            # Weekly reports
│   └── Dashboard.md          # Real-time status
├── docs/                      # Documentation
│   ├── QUICK_START.md        # Setup guide
│   ├── architecture.md       # System architecture
│   ├── CONFIGURATION.md      # Config reference
│   ├── GMAIL_OAUTH_SETUP_STEPS.md
│   └── WHATSAPP_MCP_SETUP.md
├── config/
│   └── odoo_config.yaml      # Odoo settings
├── ecosystem.config.js       # PM2 configuration
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

---

## 📚 Documentation

### Getting Started
- **[Quick Start Guide](docs/QUICK_START.md)** - Get up and running in 30 minutes
- **[Configuration Guide](docs/CONFIGURATION.md)** - Complete configuration reference
- **[Architecture Overview](docs/architecture.md)** - System design and components

### Integration Guides
- **[Gmail Setup](docs/GMAIL_OAUTH_SETUP_STEPS.md)** - OAuth configuration step-by-step
- **[WhatsApp Setup](docs/WHATSAPP_MCP_SETUP.md)** - Browser automation setup
- **[MCP Setup Guide](docs/MCP_SETUP_GUIDE.md)** - Model Context Protocol servers
- **[MCP Status](docs/MCP_STATUS.md)** - Current MCP server status

### Operations
- **[Daily Operations](DAILY_OPERATIONS.md)** - Day-to-day usage guide
- **[Troubleshooting](docs/architecture.md#troubleshooting)** - Common issues and solutions

---

## 💻 Usage

### Daily Operations

**Morning Routine** (5 minutes)
```bash
# Check system status
pm2 status

# Review pending approvals
ls -la vault/Pending_Approval/

# Check dashboard
cat vault/Dashboard.md
```

**Throughout the Day**
- Monitor `vault/Pending_Approval/` for tasks requiring review
- Approve tasks by moving them to `vault/Approved/`
- System automatically executes approved tasks every 5 minutes

**Evening Routine**
```bash
# Review completed tasks
ls -lt vault/Done/ | head -20

# Check for errors
pm2 logs --err --lines 50
```

For detailed operations guide, see [DAILY_OPERATIONS.md](DAILY_OPERATIONS.md)

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file with the following:

```env
# Vault Configuration
VAULT_PATH=./vault

# Anthropic API (Required)
ANTHROPIC_API_KEY=your_api_key_here

# Odoo Configuration (Optional)
ODOO_URL=http://localhost:8069
ODOO_DB=your_database_name
ODOO_USERNAME=admin
ODOO_PASSWORD=your_password

# Gmail API (Optional)
GMAIL_CREDENTIALS_PATH=./.credentials/gmail-credentials.json
GMAIL_TOKEN_PATH=./.credentials/gmail-token.pickle

# WhatsApp Session (Optional)
WHATSAPP_SESSION=./sessions/whatsapp_session

# LinkedIn Credentials (Optional)
LINKEDIN_EMAIL=your_email@example.com
LINKEDIN_PASSWORD=your_password
```

**📚 Full Configuration Guide:** [docs/CONFIGURATION.md](docs/CONFIGURATION.md)

### PM2 Services

The system runs 7 PM2 services:

| Service | Description | Interval |
|---------|-------------|----------|
| `atlas-orchestrator` | Main task processor | 5 minutes |
| `atlas-gmail-watcher` | Gmail monitor | 2 minutes |
| `atlas-whatsapp-watcher` | WhatsApp monitor | 30 seconds |
| `atlas-linkedin-watcher` | LinkedIn monitor | 2 minutes |
| `atlas-file-watcher` | File monitor | 15 seconds |
| `atlas-facebook-watcher` | Facebook monitor | 2 minutes |
| `atlas-instagram-watcher` | Instagram monitor | 2 minutes |

---

## 📊 System Management

### Start/Stop Services

```bash
# Start all services
pm2 start ecosystem.config.js

# Stop all services
pm2 stop all

# Restart all services
pm2 restart all

# View status
pm2 status

# View logs
pm2 logs
pm2 logs atlas-orchestrator

# Monitor resources
pm2 monit
```

### Common Commands

```bash
# Save PM2 configuration
pm2 save

# Setup auto-start on boot
pm2 startup

# Delete all services
pm2 delete all

# Flush logs
pm2 flush
```

---

## 🔒 Security

### Credential Handling

**All credentials are stored securely:**
- Environment variables in `.env` file (not committed to git)
- OAuth tokens in `.credentials/` directory (gitignored)
- Browser sessions in `sessions/` directory (gitignored)
- No hardcoded credentials in source code

### Security Features

- Input validation on all user inputs
- XSS and SQL injection prevention
- Rate limiting on API endpoints (100 req/min)
- Audit trail for all transactions
- Human approval for sensitive actions (>$100)
- Exponential backoff retry logic
- Circuit breaker for repeated failures

---

## 🐛 Troubleshooting

### Services Won't Start

```bash
# Check Python version
python --version  # Should be 3.13+

# Check PM2 status
pm2 status

# View error logs
pm2 logs --err --lines 100

# Restart specific service
pm2 restart atlas-orchestrator
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

### Odoo Connection Failures

```bash
# Test Odoo connection
curl http://localhost:8069

# Verify credentials
cat .env | grep ODOO

# Test authentication
python -c "from src.utils.odoo_client import OdooClient; OdooClient().authenticate()"
```

**📚 Full Troubleshooting Guide:** [docs/architecture.md#troubleshooting](docs/architecture.md#troubleshooting)

---

## 📈 Performance

### System Metrics

- **Orchestrator Cycle Time**: <30 seconds
- **Odoo API Response**: <5 seconds per transaction
- **Memory Usage**: ~50MB per service
- **CPU Usage**: <10% average
- **Disk Usage**: ~10MB/day growth

### Optimization Tips

- Adjust `ORCHESTRATOR_CYCLE_INTERVAL` in `.env` for faster/slower cycles
- Use `max_memory_restart` in PM2 config to prevent memory leaks
- Enable log rotation to prevent disk fill
- Monitor with `pm2 monit` for resource usage

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 License

MIT License - See [LICENSE](LICENSE) file for details

---

## 👥 Author

**Muhammad Ubaid Ansari**
- Email: muhammadubaidansari145@gmail.com
- LinkedIn: [Muhammad Ubaid Ansari](https://linkedin.com/in/your-profile)

---

## 🙏 Acknowledgments

- **Anthropic** - For Claude AI and Claude Code
- **Odoo Community** - For the excellent open-source ERP
- **Panaversity** - For organizing the hackathon
- **Open Source Community** - For the amazing tools and libraries

---

## 📞 Support

**Need Help?**
- 📖 Check [Documentation](docs/)
- 🐛 Report Issues
- 💬 Ask Questions

---

**Built with ❤️ for the Personal AI Employee Hackathon 0**

**Version:** 1.0 | **Status:** ✅ Production Ready | **Tier:** 🏆 Gold

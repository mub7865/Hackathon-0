# Bronze Tier AI Assistant

**Personal AI Employee Hackathon 0 - Bronze Tier Submission**

A file-based task processing system that uses Claude Code for AI-powered analysis. Files are dropped in an Inbox folder, processed by Claude Code on-demand, and organized in an Obsidian vault with automatic dashboard updates.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![Bronze Tier](https://img.shields.io/badge/Tier-Bronze-cd7f32.svg)](https://github.com/mub7865/Hackathon-0)

**Repository**: https://github.com/mub7865/Hackathon-0

---

## ✨ Features

- **🔍 Automatic File Detection**: Python watcher monitors Inbox folder (WSL compatible)
- **🤖 AI-Powered Analysis**: Claude Code generates summaries with emoji flags
- **📊 Obsidian Dashboard**: Central dashboard showing all processed tasks
- **📝 Custom Rules**: Define processing preferences in Company Handbook
- **🔒 Local-First**: All data stays on your machine, complete privacy
- **👤 Human-in-the-Loop**: Manual trigger required (Bronze tier compliant)
- **🧹 Cleanup Script**: Automated Inbox management after processing
- **💻 WSL Compatible**: Uses PollingObserver for Windows Subsystem for Linux

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.13+**
- **Obsidian** (free): https://obsidian.md
- **Claude Code** (CLI tool): https://claude.com/claude-code

### Installation

```bash
# 1. Clone repository
git clone https://github.com/mub7865/Hackathon-0.git
cd Hackathon-0

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate     # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Open vault in Obsidian
# Launch Obsidian → "Open folder as vault" → Select vault/ directory
```

### Daily Workflow

**See [QUICK_START.md](QUICK_START.md) for detailed guide.**

```bash
# 1. Start watcher (keep running)
cd /path/to/Hackathon-0
source venv/bin/activate
python src/watcher/file_watcher.py --vault ./vault

# 2. Drop files in vault/Inbox/

# 3. Wait 10-15 seconds (watcher detects files)

# 4. Process tasks (HITL trigger)
/process-tasks

# 5. View results in Obsidian (Dashboard.md)

# 6. Cleanup Inbox (optional)
python src/utils/cleanup_inbox.py --vault ./vault --execute
```

---

## 📁 Project Structure

```
bronze/
├── src/
│   ├── watcher/              # File monitoring system
│   │   ├── file_watcher.py   # Main watcher (PollingObserver)
│   │   ├── file_handler.py   # Event handler
│   │   └── task_creator.py   # Task file creator
│   ├── utils/                # Utilities
│   │   ├── cleanup_inbox.py  # Inbox cleanup script
│   │   ├── file_parser.py    # File content extraction
│   │   ├── logger.py         # Logging system
│   │   └── yaml_handler.py   # YAML frontmatter parser
│   ├── models/               # Data models
│   │   ├── task_file.py      # Task file model
│   │   ├── dashboard.py      # Dashboard model
│   │   └── handbook.py       # Handbook model
│   └── cli/                  # CLI tools
│       └── main.py           # Vault management
├── vault/                    # Obsidian vault
│   ├── Inbox/               # 👈 DROP FILES HERE
│   ├── Needs_Action/        # Pending tasks (auto-created)
│   ├── Done/                # Completed tasks (auto-moved)
│   ├── Logs/                # Error logs
│   ├── Dashboard.md         # 👈 OPEN IN OBSIDIAN
│   └── Company_Handbook.md  # 👈 EDIT YOUR RULES
├── tests/
│   └── fixtures/            # Test files
├── requirements.txt         # Python dependencies
├── README.md               # This file
└── QUICK_START.md          # Detailed workflow guide
```

---

## 🎯 How It Works

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   BRONZE TIER WORKFLOW                  │
└─────────────────────────────────────────────────────────┘

1. DROP FILES
   User: cp files/*.txt vault/Inbox/

2. WATCHER DETECTS (Python Script)
   Watcher: Monitors Inbox (PollingObserver for WSL)
   Creates: Task files in Needs_Action/
   Original: Stays in Inbox (archive)

3. MANUAL TRIGGER (HITL)
   User: /process-tasks

4. CLAUDE PROCESSES (AI Analysis)
   Claude: Reads Company_Handbook.md
   Claude: Analyzes each task
   Claude: Adds AI summary + emoji flags + action items
   Claude: Moves tasks to Done/
   Original: Still in Inbox

5. CLEANUP (Optional)
   User: python src/utils/cleanup_inbox.py --vault ./vault --execute
   Removes: Processed files from Inbox
   Keeps: Task files in Done/ (permanent record)
```

### Workflow Details

**Inbox → Needs_Action → Done**

1. **File Detection**: Watcher detects new files in Inbox (10-15 seconds)
2. **Task Creation**: Creates task file in Needs_Action with YAML frontmatter
3. **Manual Trigger**: User runs `/process-tasks` (Human-in-the-Loop)
4. **AI Analysis**: Claude reads Company Handbook and generates:
   - 3-bullet summary (150-200 words)
   - Emoji flags (💰 >$500, 🚨 urgent, 📝 notes, 👤 clients)
   - Key points with context
   - Action items as checkboxes
5. **Task Completion**: Task moved to Done/, Dashboard updated
6. **Cleanup**: Optional script removes processed files from Inbox

---

## 🛠️ Configuration

### Company Handbook

Edit `vault/Company_Handbook.md` to customize:

```markdown
## Custom Flags
- Amount > $500 → 💰 High-value
- Amount > $10,000 → 🚨💰 Critical
- Deadline < 3 days → 🚨 Urgent
- Contains 'meeting' → 📝 Meeting notes
- Contains client name → 👤 Client communication

## Summarization Rules
- Exactly 3 bullet points
- 150-200 words total
- Highlight dates and amounts in bold
- Action-oriented phrasing

## Tone & Style
- Professional and courteous
- Concise language
- Active voice
- Direct addressing
```

Changes apply immediately to the next processed task.

---

## 📊 Supported File Types

- **Text**: `.txt`, `.md`
- **Documents**: `.pdf`
- **Images**: `.png`, `.jpg`, `.jpeg`
- **Max size**: 10MB

---

## 🧪 Testing

### Manual Test

```bash
# 1. Start watcher
python src/watcher/file_watcher.py --vault ./vault

# 2. Drop test file
cp tests/fixtures/sample.txt vault/Inbox/

# 3. Wait 15 seconds

# 4. Process
/process-tasks

# 5. Verify
ls vault/Done/
cat vault/Dashboard.md
```

### Cleanup Test

```bash
# Dry run (safe - shows what would be deleted)
python src/utils/cleanup_inbox.py --vault ./vault

# Actual cleanup
python src/utils/cleanup_inbox.py --vault ./vault --execute
```

---

## 🐛 Troubleshooting

### Watcher Not Detecting Files

```bash
# Check if watcher is running
ps aux | grep file_watcher

# Check logs
cat vault/Logs/file_watcher-*.log

# Restart watcher
pkill -f file_watcher
python src/watcher/file_watcher.py --vault ./vault
```

### Dashboard Not Updating

```bash
# Rebuild manually
python src/cli/main.py rebuild-dashboard --path ./vault

# Refresh Obsidian (close and reopen Dashboard.md)
```

### Files Not Processing

- Check file type (must be .txt, .md, .pdf, .png, .jpg, .jpeg)
- Check file size (must be < 10MB)
- Check logs: `cat vault/Logs/file_handler-*.log`

---

## 🏗️ Architecture Principles

### Bronze Tier Requirements

✅ **Obsidian vault with Dashboard** - `vault/Dashboard.md`
✅ **Working Watcher script** - `src/watcher/file_watcher.py`
✅ **Claude Code integration** - `/process-tasks` command
✅ **Folder structure** - Inbox, Needs_Action, Done
✅ **AI as Agent Skills** - `.claude/skills/process-task/`
✅ **Human-in-the-Loop** - Manual trigger required

### Design Philosophy

1. **Local-First**: All data stays on your machine
2. **File-Based**: Markdown files with YAML frontmatter
3. **Human-in-the-Loop**: Manual approval for processing
4. **Simplicity**: Beginner-friendly, no complex setup
5. **Privacy**: No external API calls (except Claude Code)

---

## 📚 Documentation

- **[QUICK_START.md](QUICK_START.md)** - Detailed daily workflow guide
- **[GITHUB_SETUP.md](GITHUB_SETUP.md)** - Repository setup instructions
- **[Company_Handbook.md](vault/Company_Handbook.md)** - Processing rules
- **[Dashboard.md](vault/Dashboard.md)** - Task overview

---

## 🗺️ Roadmap

### Bronze Tier (Current) ✅
- File drop and processing
- Dashboard visibility
- Custom rules via handbook
- Error handling and logging
- WSL compatibility
- Cleanup script

### Silver Tier (Future)
- Email integration (Gmail API)
- WhatsApp monitoring
- Automated scheduling
- MCP servers for external actions
- Pending_Approval workflow

### Gold Tier (Future)
- Multi-agent coordination
- Advanced analytics
- Real-time notifications
- Cross-domain integration

---

## 🤝 Contributing

This is a hackathon submission project. For issues or suggestions:

1. Check existing documentation
2. Review logs in `vault/Logs/`
3. Open an issue on GitHub

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🙏 Credits

**Built for**: Personal AI Employee Hackathon 0
**Methodology**: Spec-Driven Development (SDD-RI)
**Powered by**: Claude Code (Anthropic)
**Community**: https://agentfactory.panaversity.org/

---

## 📞 Support

- **Repository**: https://github.com/mub7865/Hackathon-0
- **Issues**: Check `vault/Logs/` for error messages
- **Documentation**: See QUICK_START.md for detailed guide

---

**Ready to use!** 🚀

Start with: `python src/watcher/file_watcher.py --vault ./vault`

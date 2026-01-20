# Bronze Tier AI Assistant

A beginner-friendly AI assistant that processes files dropped into a local folder, analyzes their content using Claude AI, and presents results in an organized Obsidian vault dashboard.

## Features

- **Automatic File Processing**: Drop files in Inbox/, AI processes them automatically
- **Multiple File Types**: Supports .txt, .md, .pdf, .png, .jpg, .jpeg
- **AI-Powered Summaries**: Claude generates concise summaries with key points
- **Dashboard Visibility**: Central dashboard showing all processed tasks
- **Custom Rules**: Define your own processing preferences in Company Handbook
- **Local-First**: All data stays on your machine, complete privacy
- **Manual Testing**: Simple validation approach for beginners

## Quick Start

### Prerequisites

- Python 3.13+
- Obsidian (free download from https://obsidian.md)
- Claude API key (from https://console.anthropic.com/)

### Installation

1. **Clone or download this project**:
   ```bash
   cd bronze/
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env and add your Claude API key
   ```

4. **Initialize vault**:
   ```bash
   python src/cli/main.py init-vault --path ./vault
   ```

5. **Open vault in Obsidian**:
   - Launch Obsidian
   - Click "Open folder as vault"
   - Select the `vault/` directory

6. **Start file watcher**:
   ```bash
   python src/watcher/file_watcher.py --vault ./vault
   ```

7. **Test the system**:
   - Drop a text file in `vault/Inbox/`
   - Wait 30 seconds for detection
   - Run: `claude code` and execute `/process-tasks`
   - Check `vault/Done/` for the processed file with AI summary
   - Open Dashboard.md in Obsidian to see stats

## Project Structure

```
bronze/
├── src/
│   ├── watcher/          # File monitoring system
│   ├── skills/           # Claude Code Agent Skills
│   ├── models/           # Data models (Task, Dashboard, Handbook)
│   ├── utils/            # Utilities (YAML, logging, file parsing)
│   └── cli/              # Command-line interface
├── vault/                # Obsidian vault
│   ├── Inbox/           # Drop files here
│   ├── Needs_Action/    # Pending tasks (auto-created)
│   ├── Done/            # Completed tasks (auto-moved)
│   ├── Logs/            # Error logs
│   ├── Dashboard.md     # Status overview
│   └── Company_Handbook.md  # Your processing rules
├── tests/
│   ├── fixtures/        # Test files
│   └── scenarios/       # Manual test plans
├── requirements.txt     # Python dependencies
├── .env.example         # Environment template
└── README.md           # This file
```

## Usage

### Daily Workflow

1. **Start watcher** (if not running):
   ```bash
   python src/watcher/file_watcher.py --vault ./vault
   ```

2. **Drop files** into `vault/Inbox/` throughout the day

3. **Process tasks** periodically:
   ```bash
   claude code
   /process-tasks
   ```

4. **Review results** in Obsidian Dashboard and Done/ folder

### Customization

Edit `vault/Company_Handbook.md` to customize:
- Summary length and format
- Custom flags (e.g., "flag amounts > $500")
- Tone and style preferences
- Domain-specific rules

Changes apply immediately to the next processed task.

## Architecture

**File-Based State Management**: All data stored as markdown files with YAML frontmatter. No database required.

**Workflow**:
1. User drops file in Inbox/
2. Watcher detects file → creates task in Needs_Action/
3. User runs /process-tasks skill
4. Claude AI reads task → generates summary
5. Task moved to Done/ with summary
6. Dashboard updated with stats

**Key Components**:
- **File Watcher**: Python watchdog monitoring Inbox/
- **Agent Skill**: Claude Code skill for AI processing
- **Data Models**: TaskFile, Dashboard, Handbook
- **Utilities**: YAML parser, file parser, logger

## Manual Testing

Bronze tier uses manual validation (no automated tests):

1. **Test file processing**:
   ```bash
   cp tests/fixtures/sample.txt vault/Inbox/
   # Wait 30 seconds, then process
   ```

2. **Test dashboard updates**:
   - Process 3 files
   - Open Dashboard.md
   - Verify counts and recent activity

3. **Test custom rules**:
   - Add rule to Company_Handbook.md
   - Process a file
   - Verify rule applied in summary

See `tests/scenarios/` for detailed test plans.

## Troubleshooting

### Watcher not detecting files
- Check watcher is running: `ps aux | grep file_watcher`
- Verify file type is supported
- Check file size < 10MB
- Check logs: `cat vault/Logs/watcher-*.log`

### Claude API errors
- Verify API key in .env
- Check internet connection
- Check rate limits at console.anthropic.com

### Dashboard not updating
- Refresh Obsidian (close and reopen Dashboard.md)
- Check Dashboard.md exists
- Manually rebuild: `python src/cli/main.py rebuild-dashboard`

## Development

### Constitution Principles

This project follows 5 core principles:
1. **Local-First Architecture**: All data stays local
2. **File-Based Communication**: Markdown files as protocol
3. **Human-in-the-Loop**: Manual approval for actions
4. **Simplicity & Maintainability**: Beginner-friendly code
5. **Manual Testing & Validation**: User verification

See `.specify/memory/constitution.md` for details.

### SDD-RI Methodology

This project was built using Spec-Driven Development:
- Constitution → Spec → Plan → Tasks → Implementation
- All design documents in `specs/001-bronze-file-assistant/`

## Roadmap

**Bronze Tier** (Current): ✅
- File drop and processing
- Dashboard visibility
- Custom rules
- Error handling

**Silver Tier** (Future):
- Email integration (Gmail API)
- WhatsApp monitoring
- Automated scheduling
- MCP servers for external actions

**Gold Tier** (Future):
- Multi-agent coordination
- Advanced analytics
- Mobile app
- Real-time notifications

## License

MIT License - See LICENSE file for details

## Support

- **Documentation**: See `specs/001-bronze-file-assistant/quickstart.md`
- **Issues**: Check `vault/Logs/` for error messages
- **Community**: https://agentfactory.panaversity.org/

## Credits

Built following the SDD-RI methodology from Panaversity Agent Factory.

Powered by Claude AI (Anthropic).

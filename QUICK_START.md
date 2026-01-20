# Bronze Tier AI Assistant - Quick Start Guide

**5-Minute Setup | Beginner-Friendly | Local-First**

---

## 🚀 Quick Setup (Choose One)                    
### Option A: View in Obsidian (No Dependencies)

**Time**: 2 minutes

1. **Download Obsidian**: https://obsidian.md (Free)
2. **Open Obsidian** → "Open folder as vault"
3. **Select folder**: `D:\Hackathons\hackathon-0\bronze\vault\`
4. **View Dashboard**: Click `Dashboard.md` in left sidebar
5. **Explore**: Click wikilinks to navigate

**What you'll see**:
- Dashboard with statistics (currently 0 tasks)
- Company Handbook with custom rules
- Empty folders (Inbox, Needs_Action, Done, Logs)

---

### Option B: Full Functional Setup (With Dependencies)

**Time**: 30 minutes
```bash
# Step 1: Navigate to bronze folder
cd D:\Hackathons\hackathon-0\bronze\

# Step 2: Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate     # Windows

# Step 3: Install dependencies
pip install -r requirements.txt

# Step 4: Setup environment
cp .env.example .env
# Edit .env and add: ANTHROPIC_API_KEY=your-key-here

# Step 5: Initialize vault (already done, but you can rebuild)
python src/cli/main.py rebuild-dashboard --path ./vault

# Step 6: Start watcher (in one terminal)
python src/watcher/file_watcher.py --vault ./vault

# Step 7: Drop test file (in another terminal)
cp tests/fixtures/sample.txt vault/Inbox/
sleep 35

# Step 8: Process tasks
python src/skills/process_tasks.py --vault ./vault

# Step 9: View results
cat vault/Dashboard.md
ls vault/Done/
```

---
## 📁 Folder Structure

```
bronze/vault/
├── Inbox/              👈 DROP FILES HERE
├── Needs_Action/       👈 Pending tasks (auto-created)
├── Done/               👈 Completed tasks (auto-moved)
├── Logs/               👈 Error logs
├── Dashboard.md        👈 OPEN THIS IN OBSIDIAN
└── Company_Handbook.md 👈 Edit your custom rules
```

---

## 🎯 Daily Workflow

### 1. Start Watcher (Once per day)
```bash
cd /mnt/d/Hackathons/hackathon-0/bronze
source venv/bin/activate
python src/watcher/file_watcher.py --vault ./vault
```

**Keep this terminal running!** The watcher monitors Inbox folder continuously.

### 2. Drop Files
- Drag files to `vault/Inbox/` folder
- Supported: .txt, .md, .pdf, .png, .jpg, .jpeg
- Max size: 10MB

### 3. Wait 10-15 Seconds
- Watcher detects files automatically (using PollingObserver for WSL)
- Task files created in `Needs_Action/`
- Original files stay in Inbox (archive)

### 4. Process Tasks (Manual Trigger - HITL)
```bash
# In Claude Code terminal or new terminal
/process-tasks
```

**What happens:**
- Claude reads Company_Handbook.md for rules
- Claude analyzes each task in Needs_Action/
- Claude generates AI summaries with emoji flags
- Claude extracts action items
- Claude moves tasks to Done/
- Original files remain in Inbox

### 5. View in Obsidian
- Open `Dashboard.md`
- Click wikilinks to see task details
- Review AI summaries and action items

### 6. Cleanup Inbox (Optional)
```bash
# Dry run first (safe - shows what would be deleted)
python src/utils/cleanup_inbox.py --vault ./vault

# Actual cleanup (deletes processed files from Inbox)
python src/utils/cleanup_inbox.py --vault ./vault --execute
```

**Note:** Task files with AI analysis remain safely in Done/ folder

---

## 🔧 Common Commands

```bash
# Initialize vault
python src/cli/main.py init-vault --path ./vault

# Rebuild dashboard
python src/cli/main.py rebuild-dashboard --path ./vault

# Start watcher
python src/watcher/file_watcher.py --vault ./vault

# Process tasks
python src/skills/process_tasks.py --vault ./vault

# Check watcher status
ps aux | grep file_watcher  # Linux/Mac
tasklist | findstr python   # Windows

# View logs
cat vault/Logs/file_watcher-*.log
cat vault/Logs/task_processor-*.log
```

---

## 📊 What You'll See in Obsidian

### Dashboard.md
- **Today's Summary**: Task counts (completed, pending, failed)
- **Recent Activity**: Last 10 tasks with wikilinks
- **Statistics**: Success rate, avg time, most common type
- **Quick Links**: Navigate to folders and handbook

### Task Files (in Done/)
- **YAML Frontmatter**: Metadata (ID, status, timestamps, flags)
- **Original Content**: Preserved exactly as dropped
- **AI Analysis**: Summary, key points, action items
- **Custom Flags**: 💰 High-value, ⚡ Urgent, 🔒 Confidential

### Company Handbook
- **Summarization Rules**: How to format summaries
- **Tone & Style**: Writing preferences
- **Custom Flags**: Conditions for auto-flagging
- **Preferences**: User-specific settings

---

## 🎨 Customization

### Edit Company Handbook

1. Open `vault/Company_Handbook.md` in Obsidian
2. Edit rules:
   ```markdown
   ## Custom Flags
   - Amount > $1000 → 💰 High-value
   - Contains 'urgent' → ⚡ Urgent
   - Contains 'meeting' → 📅 Meeting
   ```
3. Save (Ctrl+S)
4. Next task will use new rules automatically

### Add Custom Rules

```markdown
### Summarization
- Use 5 bullet points instead of 3
- Always extract dates and amounts
- Highlight client names in bold

### Special Instructions
- Flag amounts over $10,000 with 🚨
- Extract all email addresses
- Note any deadlines
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

# Refresh Obsidian
# Close and reopen Dashboard.md
```

### Files Not Processing
```bash
# Check file type (must be .txt, .md, .pdf, .png, .jpg, .jpeg)
# Check file size (must be < 10MB)
# Check logs
cat vault/Logs/task_processor-*.log
```

---

## 📖 Documentation

- **README.md**: Complete user guide (228 lines)
- **TROUBLESHOOTING.md**: Problem solving (736 lines)
- **TESTING_REPORT.md**: Test results (21/21 passed)
- **tests/scenarios/**: 36 detailed test cases

---

## 🎯 Success Criteria

✅ **You're successful when**:
1. Obsidian opens vault without errors
2. Dashboard shows current statistics
3. Files dropped in Inbox are detected
4. Tasks appear in Needs_Action within 30 seconds
5. Processing moves tasks to Done
6. Dashboard updates automatically
7. Wikilinks navigate correctly

---

## 🚀 Next Steps

### Immediate (Today)
1. ✅ Open vault in Obsidian
2. ✅ View Dashboard and Handbook
3. ✅ Explore folder structure

### Short-term (This Week)
1. Install dependencies (if needed)
2. Add Claude API key
3. Test with sample files
4. Customize handbook rules

### Long-term (Next Month)
1. Process real files daily
2. Refine custom rules
3. Build workflow habits
4. Consider Silver Tier features

---

## 💡 Tips & Tricks

### Obsidian Tips
- **Ctrl+P**: Command palette (search everything)
- **Ctrl+O**: Quick file switcher
- **Ctrl+Click**: Open link in new pane
- **Ctrl+E**: Toggle edit/preview mode

### Workflow Tips
- Process tasks in batches (morning/evening)
- Review Dashboard daily
- Update handbook rules weekly
- Archive old tasks monthly

### Performance Tips
- Keep Inbox clean (files auto-move)
- Archive Done/ tasks periodically
- Monitor log file sizes
- Restart watcher weekly

---

## 🆘 Getting Help

1. **Check Documentation**: README.md, TROUBLESHOOTING.md
2. **View Logs**: vault/Logs/*.log
3. **Test Scenarios**: tests/scenarios/*.md
4. **Community**: https://agentfactory.panaversity.org/

---

## 📊 Project Stats

- **Code**: 1,927 lines (17 Python files)
- **Documentation**: 2,677 lines (6 files)
- **Tests**: 21/21 passed (100%)
- **Implementation**: 80/80 tasks (100%)
- **Status**: ✅ CODE COMPLETE

---

**Last Updated**: 2026-01-19
**Version**: Bronze Tier v1.0
**License**: MIT

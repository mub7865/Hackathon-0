# MCP Servers - Current Status & Quick Reference

## 📊 Current Status

| MCP Server | Status | Configuration | Authentication | Ready to Use |
|------------|--------|---------------|----------------|--------------|
| **Filesystem** | ✅ Active | Complete | Not needed | ✅ Yes |
| **Browser (Puppeteer)** | ⚠️ Configured | Complete | Not needed | ⚠️ Interactive only |
| **Gmail** | ⚠️ Configured | Complete | ⚠️ Required | ❌ Needs OAuth |
| **WhatsApp (Twilio)** | ❌ Not configured | Template ready | ⚠️ Required | ❌ Needs setup |

---

## ✅ Filesystem MCP (WORKING)

**Purpose:** File operations within vault folder

**Configuration:**
```json
{
  "filesystem": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/vault"]
  }
}
```

**Status:** ✅ Fully operational
**Test:** Create task in Needs_Action/ → Cron processes it → Moves to Done/

---

## ⚠️ Browser MCP (CONFIGURED)

**Purpose:** Web automation (LinkedIn posting, web scraping)

**Configuration:**
```json
{
  "browser": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-puppeteer"],
    "env": {
      "HEADLESS": "${HEADLESS:-true}"
    }
  }
}
```

**Status:** ⚠️ Only works in interactive Claude Code sessions
**Limitation:** Not available in cron/batch mode (--print flag)
**Use Case:** Manual LinkedIn posting when you run `ccr code` interactively

**How to Use:**
```bash
# Start interactive session
ccr code

# Then ask Claude to use Browser MCP
> "Open LinkedIn and post: 'Hello from AI!'"
```

---

## ⚠️ Gmail MCP (NEEDS OAUTH)

**Purpose:** Send and read emails via Gmail API

**Configuration:**
```json
{
  "gmail": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-gmail"],
    "env": {
      "GMAIL_CREDENTIALS_PATH": "${GMAIL_CREDENTIALS_PATH}",
      "GMAIL_TOKEN_PATH": "${GMAIL_TOKEN_PATH}"
    }
  }
}
```

**Status:** ⚠️ Configured but needs OAuth authentication

**Required Files:**
- `.credentials/gmail-credentials.json` (from Google Cloud Console)
- `.credentials/gmail-token.json` (generated after first auth)

**Setup Required:**
1. Create Google Cloud Project
2. Enable Gmail API
3. Create OAuth credentials (Desktop app)
4. Download credentials JSON
5. Move to `.credentials/gmail-credentials.json`
6. Run first-time authentication: `ccr code "List my emails"`

**Detailed Guide:** See `docs/GMAIL_MCP_SETUP.md`

---

## ❌ WhatsApp MCP (NOT CONFIGURED)

**Purpose:** Send and receive WhatsApp messages

**Recommended Option:** Twilio WhatsApp API

**Why Twilio:**
- Free trial ($15 credit)
- Easy setup (30 minutes)
- Reliable and production-ready
- ~$0.005 per message

**Setup Required:**
1. Create Twilio account (free trial)
2. Enable WhatsApp sandbox
3. Get Account SID and Auth Token
4. Add to `.env` file
5. Create Twilio MCP wrapper (`.mcp-servers/twilio-whatsapp/`)
6. Add to `mcp.json`

**Detailed Guide:** See `docs/WHATSAPP_MCP_SETUP.md`

---

## 🔐 Environment Variables

**File:** `.env` (NOT committed to git)

**Current Configuration:**
```bash
# Claude Code Router
ANTHROPIC_BASE_URL=http://127.0.0.1:3456
ANTHROPIC_AUTH_TOKEN=test
NO_PROXY=127.0.0.1
API_TIMEOUT_MS=600000

# Gmail MCP
GMAIL_CREDENTIALS_PATH=/path/to/.credentials/gmail-credentials.json
GMAIL_TOKEN_PATH=/path/to/.credentials/gmail-token.json

# WhatsApp (Twilio) - Not configured yet
WHATSAPP_API_KEY=
WHATSAPP_PHONE_NUMBER=

# Browser MCP
HEADLESS=true

# Twilio (for WhatsApp)
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
```

**Template:** `.env.example` (safe to commit)

---

## 📋 Setup Checklist

### Immediate (Already Done) ✅
- [x] Filesystem MCP configured and working
- [x] Browser MCP configured (interactive mode only)
- [x] Gmail MCP configured (needs OAuth)
- [x] Environment variables structure created
- [x] .gitignore updated to exclude secrets
- [x] Documentation created

### Required for Gmail (30 minutes) ⚠️
- [ ] Create Google Cloud Project
- [ ] Enable Gmail API
- [ ] Configure OAuth consent screen
- [ ] Create OAuth credentials
- [ ] Download credentials JSON
- [ ] Move to `.credentials/gmail-credentials.json`
- [ ] Run first-time authentication
- [ ] Test with sample email task

### Optional for WhatsApp (30 minutes) ⚠️
- [ ] Create Twilio account (free trial)
- [ ] Enable WhatsApp sandbox
- [ ] Get API credentials
- [ ] Add to `.env` file
- [ ] Create Twilio MCP wrapper
- [ ] Add to `mcp.json`
- [ ] Test with sample WhatsApp task

---

## 🧪 Testing MCP Servers

### Test Filesystem MCP (Working)
```bash
cat > vault/Needs_Action/TEST_FILESYSTEM.md << 'EOF'
---
id: test_fs_001
type: simple
---
## Test Task
List files in vault/Done/ folder.
EOF

bash scripts/process-tasks-cron.sh
tail -20 vault/Logs/claude-cron.log
```

### Test Gmail MCP (After OAuth)
```bash
cat > vault/Needs_Action/TEST_GMAIL.md << 'EOF'
---
id: test_gmail_001
type: simple
---
## Test Gmail
List my 3 most recent emails.
EOF

bash scripts/process-tasks-cron.sh
```

### Test Browser MCP (Interactive Only)
```bash
# Start interactive session
ccr code

# Then ask:
> "Use Browser MCP to open google.com and tell me the page title"
```

### Test WhatsApp MCP (After Twilio Setup)
```bash
cat > vault/Needs_Action/TEST_WHATSAPP.md << 'EOF'
---
id: test_wa_001
type: whatsapp_send
---
## Test WhatsApp
Send "Hello from AI!" to my number.
EOF

bash scripts/process-tasks-cron.sh
```

---

## 🚨 Important Notes

### Security
- ✅ `.credentials/` folder is in `.gitignore`
- ✅ `.env` file is in `.gitignore`
- ✅ All secrets use environment variables
- ✅ `.env.example` template provided (safe to commit)

### Limitations
- **Browser MCP:** Only works in interactive mode, not in cron
- **Gmail MCP:** Requires OAuth setup (one-time)
- **WhatsApp MCP:** Requires Twilio account (optional)

### Cron Automation
- ✅ Filesystem MCP works in cron (file operations)
- ❌ Browser MCP doesn't work in cron (interactive only)
- ⚠️ Gmail MCP will work in cron (after OAuth setup)
- ⚠️ WhatsApp MCP will work in cron (after Twilio setup)

---

## 📚 Documentation Files

1. **`docs/MCP_SETUP_GUIDE.md`** - Overview of all MCP servers
2. **`docs/GMAIL_MCP_SETUP.md`** - Step-by-step Gmail OAuth setup
3. **`docs/WHATSAPP_MCP_SETUP.md`** - WhatsApp options and Twilio setup
4. **`.env.example`** - Environment variables template
5. **`.claude/mcp.json`** - MCP server configuration

---

## 🎯 Recommended Next Steps

### For Basic Functionality (File operations only)
✅ **Already working!** No additional setup needed.

### For Email Automation (Recommended)
1. Follow `docs/GMAIL_MCP_SETUP.md`
2. Complete OAuth setup (30 minutes)
3. Test with sample email task

### For WhatsApp Automation (Optional)
1. Follow `docs/WHATSAPP_MCP_SETUP.md`
2. Create Twilio account (free trial)
3. Complete setup (30 minutes)
4. Test with sample WhatsApp task

### For LinkedIn Posting (Manual only)
- Use interactive `ccr code` sessions
- Browser MCP already configured
- Not available in cron automation

---

## 📞 Support & Troubleshooting

**Gmail Issues:** See `docs/GMAIL_MCP_SETUP.md` → Troubleshooting section
**WhatsApp Issues:** See `docs/WHATSAPP_MCP_SETUP.md` → Troubleshooting section
**General MCP Issues:** See `docs/MCP_SETUP_GUIDE.md`

**Common Issues:**
- "Credentials not found" → Check `.env` file paths
- "Permission denied" → Check file permissions (chmod 600)
- "Token expired" → Delete token and re-authenticate
- "MCP server not responding" → Check if npx can access the package

---

## ✨ Summary

**What's Working Now:**
- ✅ Filesystem MCP (file operations in vault)
- ✅ Cron automation with file-based tasks
- ✅ Environment variables properly configured
- ✅ Secrets excluded from git

**What Needs Setup:**
- ⚠️ Gmail MCP (30 min setup for email automation)
- ⚠️ WhatsApp MCP (30 min setup for WhatsApp automation)

**What's Limited:**
- ⚠️ Browser MCP (interactive mode only, not in cron)

**Atlas is production-ready for file-based task automation. Email and WhatsApp require one-time setup.**

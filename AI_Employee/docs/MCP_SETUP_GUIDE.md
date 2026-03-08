# MCP Servers Setup Guide - Atlas

## Overview

MCP (Model Context Protocol) servers enable Claude Code to interact with external services like Gmail, LinkedIn, and WhatsApp.

## Current Configuration

Location: `.claude/mcp.json`

### 1. Filesystem MCP ✅
**Status:** Already configured
**Purpose:** File operations in vault folder
**No setup needed** - Works automatically

### 2. Browser MCP (Puppeteer) ✅
**Status:** Already configured
**Purpose:** LinkedIn posting via browser automation
**No setup needed** - Works automatically

### 3. Gmail MCP ⚠️
**Status:** Configured but needs credentials
**Purpose:** Send and read emails

---

## Gmail MCP Setup

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (e.g., "Atlas-AI-Employee")
3. Enable Gmail API:
   - Go to "APIs & Services" → "Library"
   - Search for "Gmail API"
   - Click "Enable"

### Step 2: Create OAuth Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. Configure consent screen (if prompted):
   - User Type: External
   - App name: "Atlas AI Employee"
   - Add your email as test user
4. Application type: "Desktop app"
5. Download credentials JSON file

### Step 3: Save Credentials

1. Rename downloaded file to `gmail-credentials.json`
2. Move to: `/mnt/d/Hackathons/hackathon-0/silver/.credentials/gmail-credentials.json`

### Step 4: Authenticate

Run this command to authenticate (first time only):

```bash
cd /mnt/d/Hackathons/hackathon-0/silver
ccr code "Test Gmail MCP by listing my recent emails"
```

This will:
- Open browser for OAuth consent
- Save token to `.credentials/gmail-token.json`
- Future runs will use saved token

---

## Testing MCP Servers

### Test Filesystem MCP
```bash
ccr code --print "List all files in vault/Done/" --permission-mode bypassPermissions
```

### Test Browser MCP
```bash
ccr code --print "Open google.com and tell me the page title" --permission-mode bypassPermissions
```

### Test Gmail MCP (after setup)
```bash
ccr code --print "List my 5 most recent emails" --permission-mode bypassPermissions
```

---

## How Tasks Use MCP Servers

### Email Tasks
When a task file contains email instructions:
```yaml
type: email_reply
email_to: someone@example.com
```

Claude Code will:
1. Read task from vault/Needs_Action/
2. Use Gmail MCP to send email
3. Log action in vault/Logs/
4. Move task to vault/Done/

### LinkedIn Tasks
When a task file contains LinkedIn posting:
```yaml
type: linkedin_post
content: "Post content here"
```

Claude Code will:
1. Check if task needs approval (LinkedIn always requires approval)
2. Move to vault/Pending_Approval/
3. After human approval (move to vault/Approved/):
   - Use Browser MCP to open LinkedIn
   - Post content
   - Log action
   - Move to vault/Done/

---

## Security Notes

1. **Credentials Storage:**
   - `.credentials/` folder contains sensitive OAuth tokens
   - Add to `.gitignore` (already done)
   - Never commit credentials to git

2. **Permission Mode:**
   - Cron script uses `--permission-mode bypassPermissions`
   - This allows autonomous operation
   - Sensitive tasks still require HITL approval (vault/Pending_Approval/)

3. **MCP Server Isolation:**
   - Each MCP server runs in isolated process
   - Filesystem MCP only has access to vault/ folder
   - Browser MCP runs in headless mode

---

## Troubleshooting

### Gmail MCP Not Working
```bash
# Check if credentials file exists
ls -la .credentials/gmail-credentials.json

# Test authentication manually
npx -y @modelcontextprotocol/server-gmail
```

### Browser MCP Not Working
```bash
# Install Puppeteer dependencies (if needed)
sudo apt-get install -y chromium-browser

# Test browser MCP
npx -y @modelcontextprotocol/server-puppeteer
```

### MCP Server Logs
Check Claude Code logs for MCP errors:
```bash
tail -f vault/Logs/claude-cron.log
```

---

## WhatsApp Integration (Future)

WhatsApp doesn't have an official MCP server. Options:

1. **WhatsApp Web Automation** (via Browser MCP)
   - Use Puppeteer to automate WhatsApp Web
   - Requires phone to stay connected
   - Not recommended for production

2. **WhatsApp Business API** (Paid)
   - Official API for business accounts
   - Requires custom MCP server implementation
   - More reliable but costs money

3. **Third-party Services** (e.g., Twilio)
   - Use Twilio WhatsApp API
   - Create custom MCP server wrapper
   - Recommended for production use

---

## Next Steps

1. ✅ Filesystem MCP - Already working
2. ✅ Browser MCP - Already working
3. ⚠️ Gmail MCP - Follow setup steps above
4. ❌ WhatsApp MCP - Decide on approach (Web automation vs API)

Once Gmail MCP is set up, Atlas AI Employee will be fully functional for email and LinkedIn tasks!

# Gmail MCP Setup - Step by Step Guide

## Overview
Gmail MCP allows Claude Code to send and read emails on your behalf using Gmail API.

---

## Part 1: Google Cloud Console Setup

### Step 1: Create Google Cloud Project

1. **Open Browser** and go to: https://console.cloud.google.com/
2. **Sign in** with your Google account
3. **Click** "Select a project" dropdown (top left)
4. **Click** "New Project"
5. **Enter** project name: `Atlas-AI-Employee`
6. **Click** "Create"
7. **Wait** for project creation (takes ~30 seconds)
8. **Select** the new project from dropdown

### Step 2: Enable Gmail API

1. **Go to** "APIs & Services" → "Library" (left sidebar)
2. **Search** for "Gmail API"
3. **Click** on "Gmail API" in results
4. **Click** "Enable" button
5. **Wait** for API to be enabled (~10 seconds)

### Step 3: Configure OAuth Consent Screen

1. **Go to** "APIs & Services" → "OAuth consent screen" (left sidebar)
2. **Select** "External" user type
3. **Click** "Create"

**Fill in the form:**
- **App name:** `Atlas AI Employee`
- **User support email:** Your email address
- **Developer contact email:** Your email address
- **Leave** other fields empty
4. **Click** "Save and Continue"

**Scopes page:**
5. **Click** "Add or Remove Scopes"
6. **Search** for "Gmail API"
7. **Select** these scopes:
   - `https://www.googleapis.com/auth/gmail.readonly` (Read emails)
   - `https://www.googleapis.com/auth/gmail.send` (Send emails)
   - `https://www.googleapis.com/auth/gmail.compose` (Compose emails)
8. **Click** "Update"
9. **Click** "Save and Continue"

**Test users page:**
10. **Click** "Add Users"
11. **Enter** your Gmail address
12. **Click** "Add"
13. **Click** "Save and Continue"

**Summary page:**
14. **Review** and click "Back to Dashboard"

### Step 4: Create OAuth Credentials

1. **Go to** "APIs & Services" → "Credentials" (left sidebar)
2. **Click** "Create Credentials" → "OAuth client ID"
3. **Application type:** Select "Desktop app"
4. **Name:** `Atlas AI Employee Desktop`
5. **Click** "Create"

**Download Credentials:**
6. **Click** "Download JSON" button (download icon)
7. **Save** the file (it will be named like `client_secret_xxxxx.json`)

---

## Part 2: Save Credentials to Project

### Step 5: Move Credentials File

**In your terminal, run these commands:**

```bash
# Navigate to silver directory
cd /mnt/d/Hackathons/hackathon-0/silver

# Create credentials directory (if not exists)
mkdir -p .credentials

# Move downloaded file to .credentials folder
# Replace 'Downloads/client_secret_xxxxx.json' with your actual file path
mv ~/Downloads/client_secret_*.json .credentials/gmail-credentials.json

# Verify file exists
ls -la .credentials/gmail-credentials.json
```

**Expected output:**
```
-rw-r--r-- 1 user user 1234 Jan 23 16:00 .credentials/gmail-credentials.json
```

---

## Part 3: Authenticate Gmail MCP

### Step 6: First-Time Authentication

**Run this command in your terminal:**

```bash
cd /mnt/d/Hackathons/hackathon-0/silver
source .env
ccr code "Use Gmail MCP to list my 5 most recent emails"
```

**What will happen:**
1. Claude Code will start
2. Browser will open automatically
3. Google OAuth consent screen will appear
4. **Select** your Google account
5. **Click** "Continue" (you'll see a warning that app isn't verified - this is normal)
6. **Click** "Continue" again
7. **Review** permissions and click "Allow"
8. Browser will show "Authentication successful"
9. Token will be saved to `.credentials/gmail-token.json`

**After authentication:**
- Claude Code will list your recent emails
- Future runs won't need browser authentication
- Token is valid until you revoke it

---

## Part 4: Verify Setup

### Step 7: Test Gmail MCP

**Create a test task:**

```bash
cat > vault/Needs_Action/TEST_GMAIL_MCP.md << 'EOF'
---
id: test_gmail_mcp_001
source: manual
type: simple
status: pending
priority: low
created: 2026-01-23T17:00:00
---

## Test Gmail MCP

Test to verify Gmail MCP is working.

**Task:** List my 3 most recent emails and show their subjects.
EOF
```

**Run cron script:**

```bash
bash scripts/process-tasks-cron.sh
```

**Check results:**

```bash
# Check log
tail -20 vault/Logs/claude-cron.log

# Check if task moved to Done
ls -la vault/Done/TEST_GMAIL_MCP.md
```

---

## Part 5: Troubleshooting

### Issue: "Credentials file not found"

**Solution:**
```bash
# Check if file exists
ls -la .credentials/gmail-credentials.json

# Check .env file has correct path
cat .env | grep GMAIL_CREDENTIALS_PATH
```

### Issue: "Token expired or invalid"

**Solution:**
```bash
# Delete old token
rm .credentials/gmail-token.json

# Re-authenticate
ccr code "List my recent emails"
```

### Issue: "Browser doesn't open for OAuth"

**Solution:**
```bash
# Check if you're in WSL - OAuth might not open browser
# Copy the URL from terminal and paste in browser manually
```

### Issue: "Permission denied" errors

**Solution:**
```bash
# Fix file permissions
chmod 600 .credentials/gmail-credentials.json
chmod 600 .credentials/gmail-token.json
```

---

## Part 6: Security Best Practices

### ✅ DO:
- Keep `.credentials/` folder in `.gitignore`
- Use environment variables for paths
- Regularly review OAuth permissions in Google Account settings
- Revoke access if you stop using the app

### ❌ DON'T:
- Never commit credentials to git
- Don't share credentials files
- Don't use production Gmail account for testing
- Don't grant more permissions than needed

---

## Part 7: Using Gmail MCP in Tasks

### Example: Send Email Task

```yaml
---
id: email_task_001
source: manual
type: email_send
status: pending
priority: medium
created: 2026-01-23T17:00:00
---

## Send Email to Client

**To:** client@example.com
**Subject:** Project Update
**Body:**
Hi [Client Name],

Just wanted to update you on the project progress...

Best regards,
[Your Name]
```

### Example: Read Emails Task

```yaml
---
id: email_read_001
source: manual
type: email_read
status: pending
priority: low
created: 2026-01-23T17:00:00
---

## Check for Important Emails

**Task:** Check my inbox for emails from boss@company.com in the last 24 hours and summarize them.
```

---

## Summary Checklist

- [ ] Created Google Cloud Project
- [ ] Enabled Gmail API
- [ ] Configured OAuth consent screen
- [ ] Added test user (your email)
- [ ] Created OAuth credentials (Desktop app)
- [ ] Downloaded credentials JSON
- [ ] Moved to `.credentials/gmail-credentials.json`
- [ ] Updated `.env` file with correct paths
- [ ] Ran first-time authentication
- [ ] Token saved to `.credentials/gmail-token.json`
- [ ] Tested Gmail MCP with sample task
- [ ] Verified `.gitignore` excludes credentials

---

## Next Steps

Once Gmail MCP is working:
1. Test email sending functionality
2. Test email reading functionality
3. Create email reply tasks
4. Set up email filters in Company_Handbook.md
5. Configure auto-reply rules

**Gmail MCP is the most powerful integration - it enables full email automation!**

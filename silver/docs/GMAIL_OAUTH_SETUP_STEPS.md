# Gmail MCP Setup - Step by Step Guide

## Current Status
✅ **Browser MCP** - Connected
✅ **Filesystem MCP** - Connected
✅ **GitHub MCP** - Connected
❌ **Gmail MCP** - Failed (needs OAuth credentials)

---

## Gmail MCP Setup Process

### Overview
Gmail MCP needs OAuth credentials from Google Cloud Console. This is a one-time setup that takes about 30 minutes.

---

## Part 1: Google Cloud Console Setup (15 minutes)

### Step 1: Create Google Cloud Project

1. **Open browser** and go to: https://console.cloud.google.com/
2. **Sign in** with your Google account
3. **Click** "Select a project" dropdown (top left, next to "Google Cloud")
4. **Click** "NEW PROJECT" button
5. **Enter details:**
   - Project name: `Silver-AI-Employee`
   - Location: Leave as default (No organization)
6. **Click** "CREATE"
7. **Wait** ~30 seconds for project creation
8. **Select** the new project from dropdown

**Checkpoint:** You should see "Silver-AI-Employee" in the top bar.

---

### Step 2: Enable Gmail API

1. **Click** hamburger menu (☰) → "APIs & Services" → "Library"
2. **Search** for "Gmail API" in the search box
3. **Click** on "Gmail API" in results
4. **Click** "ENABLE" button
5. **Wait** ~10 seconds for API to be enabled

**Checkpoint:** You should see "API enabled" with a green checkmark.

---

### Step 3: Configure OAuth Consent Screen

1. **Click** hamburger menu (☰) → "APIs & Services" → "OAuth consent screen"
2. **Select** "External" user type
3. **Click** "CREATE"

**Fill in App Information:**
- **App name:** `Silver AI Employee`
- **User support email:** Your Gmail address (select from dropdown)
- **Developer contact email:** Your Gmail address

**Leave these blank:**
- App logo
- App domain
- Authorized domains

4. **Click** "SAVE AND CONTINUE"

**Scopes Page:**
5. **Click** "ADD OR REMOVE SCOPES"
6. **Filter** by typing "gmail" in the search box
7. **Select these 3 scopes:**
   - ✅ `https://www.googleapis.com/auth/gmail.readonly` (View your email messages and settings)
   - ✅ `https://www.googleapis.com/auth/gmail.send` (Send email on your behalf)
   - ✅ `https://www.googleapis.com/auth/gmail.compose` (Manage drafts and send emails)
8. **Click** "UPDATE"
9. **Click** "SAVE AND CONTINUE"

**Test Users Page:**
10. **Click** "ADD USERS"
11. **Enter** your Gmail address
12. **Click** "ADD"
13. **Click** "SAVE AND CONTINUE"

**Summary Page:**
14. **Review** and click "BACK TO DASHBOARD"

**Checkpoint:** OAuth consent screen should show "External" with "Testing" status.

---

### Step 4: Create OAuth Credentials

1. **Click** hamburger menu (☰) → "APIs & Services" → "Credentials"
2. **Click** "CREATE CREDENTIALS" → "OAuth client ID"
3. **Application type:** Select "Desktop app"
4. **Name:** `Silver AI Employee Desktop`
5. **Click** "CREATE"

**Download Credentials:**
6. A popup will appear with "OAuth client created"
7. **Click** "DOWNLOAD JSON" button (download icon)
8. The file will download as `client_secret_XXXXX.json`

**Checkpoint:** You should have a JSON file downloaded to your Downloads folder.

---

## Part 2: Save Credentials to Project (5 minutes)

### Step 5: Move Credentials File

**Open a NEW terminal window** (keep Claude Code running in the other one) and run:

```bash
# Navigate to silver directory
cd /mnt/d/Hackathons/hackathon-0/silver

# Create credentials directory
mkdir -p .credentials

# Move downloaded file (replace XXXXX with your actual filename)
# Check your Downloads folder for the exact filename
mv ~/Downloads/client_secret_*.json .credentials/gmail-credentials.json

# Verify file exists
ls -la .credentials/gmail-credentials.json
```

**Expected output:**
```
-rw-r--r-- 1 user user 1234 Jan 23 17:00 .credentials/gmail-credentials.json
```

**If you get "No such file":**
- Check your Downloads folder: `ls ~/Downloads/client_secret_*.json`
- Or manually copy the file to `.credentials/gmail-credentials.json`

---

## Part 3: Authenticate Gmail MCP (10 minutes)

### Step 6: First-Time OAuth Authentication

**In your Claude Code session** (the one that's already running), type this prompt:

```
Use Gmail MCP to list my 5 most recent emails
```

**What will happen:**

1. **Browser will open automatically** with Google OAuth consent screen
2. **Select your Google account**
3. **You'll see a warning:** "Google hasn't verified this app"
   - **Click** "Continue" (this is normal for testing apps)
4. **Review permissions:**
   - View your email messages and settings
   - Send email on your behalf
   - Manage drafts and send emails
5. **Click** "Allow"
6. **Browser will show:** "Authentication successful! You can close this window."
7. **Return to Claude Code** - it will now list your recent emails

**Token saved:** After successful authentication, a token file will be created at:
```
.credentials/gmail-token.json
```

**Future runs:** You won't need to authenticate again - the token will be reused automatically.

---

## Part 4: Verify Gmail MCP Working

### Step 7: Test Gmail MCP

**In Claude Code, try these commands:**

**Test 1: List emails**
```
List my 3 most recent emails with subjects
```

**Test 2: Check MCP status**
```
/mcp
```

**Expected result:**
```
4. gmail  ✔ connected · Enter to view details
```

**If it works:** Gmail MCP is fully operational! ✅

---

## Troubleshooting

### Issue: "Credentials file not found"

**Check file exists:**
```bash
ls -la /mnt/d/Hackathons/hackathon-0/silver/.credentials/gmail-credentials.json
```

**If missing:** Re-download from Google Cloud Console and move to correct location.

---

### Issue: "Browser doesn't open for OAuth"

**Manual authentication:**
1. Claude Code will show a URL in the terminal
2. Copy the URL
3. Paste in browser manually
4. Complete OAuth flow
5. Return to Claude Code

---

### Issue: "Token expired or invalid"

**Delete old token and re-authenticate:**
```bash
rm /mnt/d/Hackathons/hackathon-0/silver/.credentials/gmail-token.json
```

Then try listing emails again - it will trigger new OAuth flow.

---

### Issue: "Permission denied" errors

**Fix file permissions:**
```bash
chmod 600 /mnt/d/Hackathons/hackathon-0/silver/.credentials/gmail-credentials.json
chmod 600 /mnt/d/Hackathons/hackathon-0/silver/.credentials/gmail-token.json
```

---

## Security Notes

✅ **DO:**
- Keep `.credentials/` folder in `.gitignore` (already done)
- Use environment variables for paths (already configured)
- Regularly review OAuth permissions in Google Account settings
- Revoke access if you stop using the app

❌ **DON'T:**
- Never commit credentials to git
- Don't share credentials files
- Don't use production Gmail account for testing
- Don't grant more permissions than needed

---

## Next Steps

After Gmail MCP is working:

1. ✅ **Gmail MCP** - Complete OAuth setup
2. ⏭️ **WhatsApp MCP** - Set up Twilio (next task)
3. ⏭️ **LinkedIn** - Test Browser MCP for posting
4. ⏭️ **End-to-end testing** - Create tasks and verify automation

---

## Summary Checklist

**Google Cloud Console:**
- [ ] Created project "Silver-AI-Employee"
- [ ] Enabled Gmail API
- [ ] Configured OAuth consent screen (External, Testing)
- [ ] Added your email as test user
- [ ] Created OAuth credentials (Desktop app)
- [ ] Downloaded credentials JSON

**Local Setup:**
- [ ] Moved credentials to `.credentials/gmail-credentials.json`
- [ ] Verified file exists with correct path
- [ ] File permissions set (600)

**Authentication:**
- [ ] Ran Gmail MCP command in Claude Code
- [ ] Browser opened with OAuth consent
- [ ] Clicked "Continue" on unverified app warning
- [ ] Granted all 3 Gmail permissions
- [ ] Token saved to `.credentials/gmail-token.json`
- [ ] Gmail MCP shows "✔ connected" in `/mcp`

**Testing:**
- [ ] Successfully listed recent emails
- [ ] Gmail MCP working in Claude Code session

---

**Once Gmail MCP is working, we'll move to WhatsApp (Twilio) setup!**

# Daily Operations Guide - Silver Tier AI Employee

Complete guide for daily operations, commands, and troubleshooting.

---

## 📅 Daily Routine

### 🌅 Morning Routine (5 minutes)

#### 1. Check System Status
```bash
pm2 status
```
**What it does**: Shows all running services (orchestrator, watchers)
**Expected**: All services should show "online" status
**If not online**: Run `pm2 restart all`

#### 2. Check Pending Tasks
```bash
ls -la vault/Needs_Action/
ls -la vault/Pending_Approval/
```
**What it does**: Lists tasks waiting for processing/approval
**Action needed**: Review and approve tasks in Pending_Approval folder

#### 3. Check Dashboard
```bash
cat vault/Dashboard.md
```
**What it does**: Shows system overview and statistics
**Check**: Last Updated timestamp should be recent (within 5 minutes)

#### 4. Quick Health Check
```bash
pm2 logs --lines 20
```
**What it does**: Shows recent logs from all services
**Look for**: Any ERROR messages or warnings

---

### 🏃 Throughout the Day

#### Check for New Approvals (Every 2-3 hours)
```bash
ls -la vault/Pending_Approval/
```
**What it does**: Shows tasks waiting for your approval
**Action**: Move approved tasks to `vault/Approved/` folder

#### Monitor System (If needed)
```bash
pm2 monit
```
**What it does**: Real-time monitoring of CPU/Memory usage
**Exit**: Press `Ctrl+C`

---

### 🌙 Evening Routine (5 minutes)

#### 1. Review Completed Tasks
```bash
ls -lt vault/Done/ | head -20
```
**What it does**: Shows 20 most recent completed tasks
**Check**: Verify important tasks were completed

#### 2. Check for Errors
```bash
tail -n 50 logs/orchestrator-error.log
tail -n 50 logs/gmail-watcher-error.log
tail -n 50 logs/whatsapp-watcher-error.log
```
**What it does**: Shows recent errors from each service
**Action**: If errors found, check troubleshooting section

#### 3. Save PM2 Configuration
```bash
pm2 save
```
**What it does**: Saves current PM2 setup (runs automatically on reboot)
**When**: Run this after making any PM2 changes

---

## 🎮 PM2 Commands Reference

### Basic Commands

#### Start All Services
```bash
pm2 start ecosystem.config.js
```
**What it does**: Starts orchestrator and all watchers
**When to use**: First time setup or after stopping all services

#### Stop All Services
```bash
pm2 stop all
```
**What it does**: Stops all running services
**When to use**: When you need to stop the system temporarily

#### Restart All Services
```bash
pm2 restart all
```
**What it does**: Restarts all services (picks up code changes)
**When to use**: After updating code or fixing bugs

#### Check Status
```bash
pm2 status
```
**What it does**: Shows status of all services
**Output**: Shows online/stopped, uptime, memory usage

---

### Individual Service Commands

#### Restart Specific Service
```bash
pm2 restart silver-orchestrator
pm2 restart silver-gmail-watcher
pm2 restart silver-whatsapp-watcher
```
**What it does**: Restarts only one service
**When to use**: When only one service has issues

#### Stop Specific Service
```bash
pm2 stop silver-orchestrator
pm2 stop silver-gmail-watcher
pm2 stop silver-whatsapp-watcher
```
**What it does**: Stops only one service
**When to use**: When you need to disable one watcher temporarily

#### Start Specific Service
```bash
pm2 start silver-orchestrator
pm2 start silver-gmail-watcher
pm2 start silver-whatsapp-watcher
```
**What it does**: Starts only one service
**When to use**: After stopping a specific service

---

### Log Commands

#### View All Logs (Real-time)
```bash
pm2 logs
```
**What it does**: Shows live logs from all services
**Exit**: Press `Ctrl+C`

#### View Specific Service Logs
```bash
pm2 logs silver-orchestrator
pm2 logs silver-gmail-watcher
pm2 logs silver-whatsapp-watcher
```
**What it does**: Shows logs from one service only
**Exit**: Press `Ctrl+C`

#### View Last N Lines
```bash
pm2 logs silver-orchestrator --lines 50
```
**What it does**: Shows last 50 log lines
**When to use**: Quick check without real-time streaming

#### Clear All Logs
```bash
pm2 flush
```
**What it does**: Deletes all PM2 logs
**When to use**: When logs get too large (use carefully!)

---

### Advanced Commands

#### Monitor Resources
```bash
pm2 monit
```
**What it does**: Real-time CPU/Memory monitoring
**Exit**: Press `Ctrl+C`

#### Show Process Details
```bash
pm2 show silver-orchestrator
```
**What it does**: Detailed info about one service
**Shows**: Uptime, restarts, memory, CPU, logs path

#### Delete Service
```bash
pm2 delete silver-orchestrator
```
**What it does**: Removes service from PM2
**Warning**: Use only if you want to completely remove a service

#### Save Configuration
```bash
pm2 save
```
**What it does**: Saves current PM2 setup
**When to use**: After adding/removing services

#### Startup on Boot
```bash
pm2 startup
```
**What it does**: Configures PM2 to start on system reboot
**When to use**: One-time setup (already done)

---

## 📋 Common Operations

### Operation 1: Approve a Task

**Scenario**: You received an email, AI drafted a reply, now you need to approve it.

**Steps**:
1. Check pending tasks:
   ```bash
   ls -la vault/Pending_Approval/
   ```

2. Open task file in editor (or Obsidian):
   ```bash
   cat vault/Pending_Approval/EMAIL_xyz.md
   ```

3. Review the draft reply

4. If approved, move to Approved folder:
   ```bash
   mv vault/Pending_Approval/EMAIL_xyz.md vault/Approved/
   ```

5. Wait 5 minutes - orchestrator will send it automatically

6. Verify in Done folder:
   ```bash
   ls -la vault/Done/ | grep EMAIL_xyz
   ```

---

### Operation 2: Reject a Task

**Scenario**: AI drafted a reply but you don't want to send it.

**Steps**:
1. Move to Rejected folder:
   ```bash
   mv vault/Pending_Approval/EMAIL_xyz.md vault/Rejected/
   ```

2. Task will not be sent

---

### Operation 3: Manually Send WhatsApp Message

**Scenario**: You want to send a WhatsApp message manually.

**Steps**:
1. Create task file:
   ```bash
   nano vault/Needs_Action/MANUAL_WHATSAPP_001.md
   ```

2. Add content:
   ```markdown
   ---
   id: manual_whatsapp_001
   source: manual
   type: whatsapp
   status: pending
   priority: high
   whatsapp_sender: Contact Name
   ---

   ## Manual WhatsApp Task

   Send this message to Contact Name:

   Your message here...
   ```

3. Save and exit (Ctrl+X, Y, Enter)

4. Wait 5 minutes - orchestrator will process it

5. Check Pending_Approval folder and approve

---

### Operation 4: Check Why Task is Stuck

**Scenario**: Task is not moving from Needs_Action or Approved folder.

**Steps**:
1. Check orchestrator status:
   ```bash
   pm2 status
   ```
   - If stopped: `pm2 restart silver-orchestrator`

2. Check orchestrator logs:
   ```bash
   pm2 logs silver-orchestrator --lines 50
   ```
   - Look for ERROR messages

3. Check lock status:
   ```bash
   cat vault/Logs/orchestrator_state.json
   ```
   - If locked: Edit file and set `"locked": false`

4. Restart orchestrator:
   ```bash
   pm2 restart silver-orchestrator
   ```

---

### Operation 5: WhatsApp Not Sending

**Scenario**: WhatsApp messages are stuck in Approved folder.

**Steps**:
1. Check WhatsApp watcher status:
   ```bash
   pm2 status | grep whatsapp
   ```
   - If stopped: `pm2 restart silver-whatsapp-watcher`

2. Check WhatsApp session:
   ```bash
   ls -la sessions/wa_autonomous_v4/
   ```
   - Should have browser session files

3. Check logs:
   ```bash
   tail -n 100 logs/whatsapp-watcher-error.log
   ```

4. If session expired, restart watcher:
   ```bash
   pm2 restart silver-whatsapp-watcher
   ```

---

### Operation 6: Gmail Not Receiving

**Scenario**: New emails are not creating tasks.

**Steps**:
1. Check Gmail watcher status:
   ```bash
   pm2 status | grep gmail
   ```
   - If stopped: `pm2 restart silver-gmail-watcher`

2. Check credentials:
   ```bash
   ls -la .credentials/
   ```
   - Should have `gmail-credentials.json` and `gmail-token.pickle`

3. Check logs:
   ```bash
   tail -n 100 logs/gmail-watcher-error.log
   ```

4. If token expired, restart watcher:
   ```bash
   pm2 restart silver-gmail-watcher
   ```

---

## 🔧 Troubleshooting Guide

### Problem: All Services Stopped

**Solution**:
```bash
pm2 restart all
pm2 status
```

---

### Problem: Orchestrator Keeps Restarting

**Check logs**:
```bash
pm2 logs silver-orchestrator --err --lines 50
```

**Common causes**:
- Python error in code
- Missing dependencies
- Lock file stuck

**Fix**:
1. Check error message in logs
2. If lock stuck: Edit `vault/Logs/orchestrator_state.json`, set `"locked": false`
3. Restart: `pm2 restart silver-orchestrator`

---

### Problem: High Memory Usage

**Check usage**:
```bash
pm2 monit
```

**Solution**:
```bash
pm2 restart all
```

---

### Problem: Logs Too Large

**Check log size**:
```bash
du -sh logs/
```

**Clear logs**:
```bash
pm2 flush
```

**Or manually**:
```bash
rm logs/*.log
pm2 restart all
```

---

### Problem: Dashboard Not Updating

**Check**:
```bash
cat vault/Dashboard.md | grep "Last Updated"
```

**If old (>10 minutes)**:
1. Check orchestrator is running: `pm2 status`
2. Check orchestrator logs: `pm2 logs silver-orchestrator --lines 30`
3. Restart orchestrator: `pm2 restart silver-orchestrator`
4. Wait 5 minutes and check again

---

## 📊 Understanding PM2 Status Output

```bash
pm2 status
```

**Output columns**:
- **id**: Process ID in PM2
- **name**: Service name (silver-orchestrator, silver-gmail-watcher, etc.)
- **status**:
  - `online` = Running normally ✅
  - `stopped` = Not running ❌
  - `errored` = Crashed ⚠️
- **uptime**: How long service has been running
- **↺**: Number of restarts (high number = problem)
- **cpu**: CPU usage percentage
- **mem**: Memory usage

**Healthy system**:
- All services: `online`
- Uptime: >1 hour
- Restarts: <5
- CPU: <10%
- Memory: <100MB per service

---

## 🎯 Quick Reference

### Daily Must-Do Commands
```bash
# Morning check
pm2 status
ls -la vault/Pending_Approval/

# Throughout day
ls -la vault/Pending_Approval/

# Evening check
ls -lt vault/Done/ | head -20
```

### Emergency Commands
```bash
# Everything stopped
pm2 restart all

# One service crashed
pm2 restart silver-orchestrator

# Check what's wrong
pm2 logs --err --lines 50

# Clear stuck lock
# Edit vault/Logs/orchestrator_state.json
# Set "locked": false
```

### Useful Shortcuts
```bash
# Quick status
pm2 ls

# Quick logs
pm2 logs --lines 20

# Quick restart
pm2 restart all

# Quick health check
pm2 status && ls -la vault/Pending_Approval/
```

---

## 📞 Support Checklist

When something goes wrong, check in this order:

1. ✅ **PM2 Status**: `pm2 status` - All online?
2. ✅ **Logs**: `pm2 logs --err --lines 50` - Any errors?
3. ✅ **Lock**: `cat vault/Logs/orchestrator_state.json` - Locked?
4. ✅ **Dashboard**: `cat vault/Dashboard.md` - Updating?
5. ✅ **Folders**: `ls vault/Pending_Approval/` - Tasks stuck?

If all checks pass but still issues:
```bash
pm2 restart all
pm2 save
```

---

**System Status**: Production Ready ✅
**Last Updated**: 2026-02-24

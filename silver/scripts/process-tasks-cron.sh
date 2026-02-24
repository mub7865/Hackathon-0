#!/bin/bash
# Silver Tier - Claude Code Task Processing
# Runs every 10 minutes via cron

# Change to silver directory
cd /mnt/d/Hackathons/hackathon-0/silver

# Load environment variables from .env file
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "ERROR: .env file not found!" >> vault/Logs/claude-cron.log
    exit 1
fi

# Log file
LOG_FILE="vault/Logs/claude-cron.log"

# Timestamp
echo "==================================" >> "$LOG_FILE"
echo "$(date '+%Y-%m-%d %H:%M:%S') - Starting Claude Code processing" >> "$LOG_FILE"

# Check if there are tasks to process
TASK_COUNT=$(find vault/Needs_Action -name "*.md" -type f 2>/dev/null | wc -l)

if [ "$TASK_COUNT" -eq 0 ]; then
    echo "No tasks in Needs_Action folder" >> "$LOG_FILE"
    exit 0
fi

echo "Found $TASK_COUNT task(s) to process" >> "$LOG_FILE"

# Run Claude Code with --print flag (non-interactive mode)
# Enable tools needed for task processing: Read, Write, Edit, Bash, Glob, Grep
# Use --permission-mode bypassPermissions for autonomous operation (no prompts)
timeout 5m ccr code --print "You are processing tasks from the vault/Needs_Action/ folder. For each task file: 1) Read the task file, 2) Analyze if it's simple, complex, or sensitive, 3) For simple tasks: Move to vault/Done/, 4) For complex tasks: Create Plan.md in vault/Plans/ then move to vault/Done/, 5) For sensitive tasks: Move to vault/Pending_Approval/ with reasons. Process all tasks now and then exit." --tools "Read,Write,Edit,Bash,Glob,Grep" --permission-mode bypassPermissions >> "$LOG_FILE" 2>&1

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "Claude Code completed successfully" >> "$LOG_FILE"
elif [ $EXIT_CODE -eq 124 ]; then
    echo "Claude Code timeout after 5 minutes" >> "$LOG_FILE"
else
    echo "Claude Code exited with code $EXIT_CODE" >> "$LOG_FILE"
fi

echo "==================================" >> "$LOG_FILE"

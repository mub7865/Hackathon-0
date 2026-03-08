#!/bin/bash
# Ralph Wiggum Stop Hook
# Keeps Claude Code running until tasks are complete

# This hook is triggered when Claude tries to exit
# It checks if tasks are complete, and if not, re-injects the prompt

# Configuration
MAX_ITERATIONS=10
VAULT_PATH="D:/Hackathons/hackathon-0/silver/vault"
STATE_FILE="$VAULT_PATH/.ralph-state.json"

# Get current iteration count
if [ -f "$STATE_FILE" ]; then
    ITERATION=$(jq -r '.iteration // 0' "$STATE_FILE" 2>/dev/null || echo "0")
else
    ITERATION=0
fi

# Increment iteration
ITERATION=$((ITERATION + 1))

# Check if max iterations reached
if [ $ITERATION -ge $MAX_ITERATIONS ]; then
    echo "Max iterations ($MAX_ITERATIONS) reached. Allowing exit."
    rm -f "$STATE_FILE"
    exit 0
fi

# Check completion strategies

# Strategy 1: Promise-based (check Claude's output for completion promise)
if echo "$CLAUDE_OUTPUT" | grep -q "<promise>TASK_COMPLETE</promise>"; then
    echo "Task complete promise found. Allowing exit."
    rm -f "$STATE_FILE"
    exit 0
fi

# Strategy 2: File-based (check if Needs_Action folder is empty)
NEEDS_ACTION_COUNT=$(find "$VAULT_PATH/Needs_Action" -name "*.md" -type f 2>/dev/null | wc -l)
if [ "$NEEDS_ACTION_COUNT" -eq 0 ]; then
    echo "All tasks processed (Needs_Action is empty). Allowing exit."
    rm -f "$STATE_FILE"
    exit 0
fi

# Tasks not complete - block exit and re-inject prompt
echo "Tasks not complete (iteration $ITERATION/$MAX_ITERATIONS). Continuing..."

# Save state
echo "{\"iteration\": $ITERATION, \"timestamp\": \"$(date -Iseconds)\"}" > "$STATE_FILE"

# Re-inject the original prompt
if [ -f "$STATE_FILE.prompt" ]; then
    cat "$STATE_FILE.prompt"
else
    echo "Continue processing tasks in $VAULT_PATH/Needs_Action/. When done, output: <promise>TASK_COMPLETE</promise>"
fi

# Exit with code 1 to block Claude's exit
exit 1

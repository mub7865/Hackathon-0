"""
Orchestrator - Automated Task Processing Engine
Runs every 5-10 minutes, processes tasks, and manages approval workflow
"""

from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import time
import logging
import yaml
import shutil
import subprocess
import json
import sys

from .state_manager import StateManager, OrchestratorState
from .task_processor import TaskProcessor, Classification
from .approval_handler import ApprovalHandler, ApprovalResult
from ..utils.task_file import TaskFile
from ..utils.logger import setup_logger


class OrchestratorError(Exception):
    """Base exception for orchestrator errors"""
    pass


class Orchestrator:
    """
    Automated task processing engine.
    Runs on a schedule, processes tasks, and manages approval workflow.
    """

    def __init__(self, vault_path: str, cycle_interval: int = 300):
        """
        Initialize orchestrator.

        Args:
            vault_path: Path to Obsidian vault
            cycle_interval: Seconds between cycles (default: 300 = 5 minutes)
        """
        self.vault_path = Path(vault_path)
        self.cycle_interval = cycle_interval

        # Folder paths
        self.needs_action = self.vault_path / 'Needs_Action'
        self.pending_approval = self.vault_path / 'Pending_Approval'
        self.approved = self.vault_path / 'Approved'
        self.rejected = self.vault_path / 'Rejected'
        self.done = self.vault_path / 'Done'
        self.logs = self.vault_path / 'Logs'

        # Logger (setup first, before other components)
        self.logger = setup_logger('orchestrator', str(self.logs))

        # State management
        self.state_file = self.logs / 'orchestrator_state.json'
        self.state_manager = StateManager(self.state_file)

        # Task processor
        self.handbook_rules = self._load_handbook_rules()
        self.task_processor = TaskProcessor(self.handbook_rules)

        # Approval handler
        self.approval_handler = ApprovalHandler(self.logger)

        # Running flag
        self.running = False

    def _load_handbook_rules(self) -> Dict[str, Any]:
        """
        Load Company Handbook rules.

        Returns:
            Dictionary of handbook rules
        """
        handbook_path = self.vault_path / 'Company_Handbook.md'

        if not handbook_path.exists():
            self.logger.warning("Company Handbook not found, using default rules")
            return {}

        # For now, return empty dict - rules are hardcoded in TaskProcessor
        # In production, you'd parse the handbook markdown
        return {}

    def start(self) -> None:
        """
        Start orchestrator loop.
        Runs continuously until stopped.
        """
        self.running = True
        self.logger.info(f"Starting orchestrator (cycle interval: {self.cycle_interval}s)")

        while self.running:
            try:
                self.run_cycle()
                time.sleep(self.cycle_interval)
            except KeyboardInterrupt:
                self.logger.info("Received stop signal")
                self.stop()
                break
            except Exception as e:
                self.logger.error(f"Cycle error: {e}")
                time.sleep(60)  # Wait 1 minute on error

    def stop(self) -> None:
        """
        Stop orchestrator gracefully.
        Completes current cycle before stopping.
        """
        self.logger.info("Stopping orchestrator")
        self.running = False

    def run_cycle(self) -> Dict[str, Any]:
        """
        Execute one processing cycle.

        Returns:
            Cycle result with statistics

        Raises:
            OrchestratorError: If cycle fails critically
        """
        cycle_start = datetime.now()
        self.logger.info("Starting orchestrator cycle")

        # Load state
        state = self.state_manager.load_state()

        # Try to acquire lock
        if not self.state_manager.acquire_lock(state):
            self.logger.warning("Could not acquire lock, skipping cycle")
            return {'status': 'skipped', 'reason': 'locked'}

        try:
            # Process Needs_Action folder
            tasks_processed = self._process_needs_action()

            # Process Approved folder (execute actions)
            actions_executed = self._process_approved()

            # Process Pending_Approval folder (for future MCP integration)
            approvals_processed = self._process_pending_approval()

            # Update Dashboard
            self._update_dashboard()

            # Update state
            state.current_cycle += 1
            state.last_run = datetime.now().isoformat()
            state.status = "running"
            state.statistics.tasks_processed_today += tasks_processed
            state.statistics.tasks_approved_today += approvals_processed

            self.state_manager.save_state(state)

            cycle_duration = (datetime.now() - cycle_start).total_seconds()
            self.logger.info(f"Cycle complete: {tasks_processed} tasks processed in {cycle_duration:.1f}s")

            return {
                'status': 'success',
                'tasks_processed': tasks_processed,
                'approvals_processed': approvals_processed,
                'duration': cycle_duration
            }

        finally:
            # Always release lock
            self.state_manager.release_lock(state)

    def _process_needs_action(self) -> int:
        """
        Process tasks in Needs_Action folder using AI processor.

        Uses ai_processor module with Claude/Gemini API to:
        - Classify tasks (SIMPLE, COMPLEX, SENSITIVE)
        - Create Plan.md for complex tasks
        - Generate contextual drafts using Agent Skills
        - Move to Pending_Approval for human review

        Returns:
            Number of tasks processed
        """
        if not self.needs_action.exists():
            return 0

        task_files = list(self.needs_action.glob('*.md'))

        if len(task_files) == 0:
            return 0

        self.logger.info(f"Found {len(task_files)} task(s) in Needs_Action folder")

        processed_count = 0

        # Import AI processor
        try:
            from .ai_processor import process_task
        except ImportError as e:
            self.logger.error(f"Could not import ai_processor: {e}")
            self.logger.error("Make sure Anthropic or Gemini API is configured")
            return 0

        for task_file in task_files:
            try:
                self.logger.info(f"Processing task: {task_file.name}")

                # Use AI processor with Claude/Gemini API
                success = process_task(task_file, self.vault_path)

                if success:
                    processed_count += 1
                    self.logger.info(f"Successfully processed {task_file.name}")
                else:
                    self.logger.error(f"Failed to process {task_file.name}")

            except Exception as e:
                self.logger.error(f"Error processing {task_file.name}: {e}")
                continue

        return processed_count

    def _process_approved(self) -> int:
        """
        Process approved tasks and execute actions directly via action scripts.

        Directly calls action scripts (bypassing MCP for reliability):
        - gmail_action.py for email tasks
        - whatsapp_action.py for WhatsApp tasks
        - linkedin_action.py for LinkedIn tasks

        Returns:
            Number of actions executed
        """
        if not self.approved.exists():
            return 0

        task_files = list(self.approved.glob('*.md'))

        if len(task_files) == 0:
            return 0

        self.logger.info(f"Found {len(task_files)} approved task(s) to execute")

        executed_count = 0

        for task_file in task_files:
            try:
                self.logger.info(f"Executing approved task: {task_file.name}")

                # Execute task directly via action scripts
                success = self._execute_approved_task_direct(task_file)

                if success:
                    executed_count += 1
                    self.logger.info(f"Successfully executed {task_file.name}")
                else:
                    self.logger.error(f"Failed to execute {task_file.name}, keeping in Approved")

            except Exception as e:
                self.logger.error(f"Error executing {task_file.name}: {e}")
                import traceback
                traceback.print_exc()
                continue

        return executed_count

    def _execute_approved_task_direct(self, task_file: Path) -> bool:
        """
        Execute approved task by directly calling action scripts.

        Args:
            task_file: Path to approved task file

        Returns:
            True if successful, False otherwise
        """
        try:
            # Read task file
            content = task_file.read_text(encoding='utf-8')

            # Parse frontmatter and content
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter = yaml.safe_load(parts[1])
                    body = parts[2].strip()
                else:
                    self.logger.error(f"Invalid frontmatter in {task_file.name}")
                    return False
            else:
                self.logger.error(f"No frontmatter in {task_file.name}")
                return False

            # Extract task type and draft content
            task_type = frontmatter.get('type', 'unknown')
            draft_content = ""

            # Extract draft based on task type
            if task_type == 'email':
                # Extract from "## Draft Response" section
                if "## Draft Response" in body:
                    draft_section = body.split("## Draft Response")[1]
                    if "## Classification" in draft_section:
                        draft_content = draft_section.split("## Classification")[0].strip()
                    else:
                        draft_content = draft_section.strip()

                    # Clean the draft content - remove metadata headers and footers
                    draft_content = self._extract_message_body(draft_content)

            elif task_type == 'whatsapp':
                # Extract from "## Draft Response" section
                if "## Draft Response" in body:
                    draft_section = body.split("## Draft Response")[1]
                    if "## Classification" in draft_section:
                        draft_content = draft_section.split("## Classification")[0].strip()
                    else:
                        draft_content = draft_section.strip()

                    # Clean the draft content - remove metadata headers and footers
                    draft_content = self._extract_message_body(draft_content)

            elif task_type == 'linkedin':
                # Extract from "### Post Content:" section
                if "### Post Content:" in body:
                    content_section = body.split("### Post Content:")[1]
                    if "### Expected Outcome:" in content_section:
                        draft_content = content_section.split("### Expected Outcome:")[0].strip()
                    elif "---" in content_section:
                        draft_content = content_section.split("---")[0].strip()
                    else:
                        draft_content = content_section.strip()

            if not draft_content:
                self.logger.error(f"No draft content found in {task_file.name}")
                return False

            # Import action scripts
            sys.path.insert(0, str(Path(__file__).parent.parent))

            # Execute based on task type
            success = False

            if task_type == 'email':
                from actions.gmail_action import send_email

                to = frontmatter.get('email_from')
                subject = frontmatter.get('email_subject', 'Re: Your message')

                if not subject.startswith('Re:'):
                    subject = f"Re: {subject}"

                self.logger.info(f"Sending email to {to}")
                result = send_email(to=to, subject=subject, body=draft_content)
                success = result.get('status') == 'success'

            elif task_type == 'whatsapp':
                from actions.whatsapp_action import send_whatsapp

                to = frontmatter.get('whatsapp_sender') or frontmatter.get('whatsapp_from')

                # Stop WhatsApp watcher BEFORE sending (to release browser session)
                self.logger.info("Stopping WhatsApp watcher to release browser session...")
                try:
                    subprocess.run("pm2 stop silver-whatsapp-watcher", shell=True, check=False, capture_output=True, text=True, timeout=10)
                    time.sleep(5)  # Wait for watcher to fully stop
                except Exception as e:
                    self.logger.warning(f"Could not stop watcher: {e}")

                self.logger.info(f"Sending WhatsApp to {to}")
                result = send_whatsapp(to=to, message=draft_content)
                success = result.get('status') == 'success'

                # Restart WhatsApp watcher AFTER sending
                self.logger.info("Restarting WhatsApp watcher...")
                try:
                    subprocess.run("pm2 start silver-whatsapp-watcher", shell=True, check=False, capture_output=True, text=True, timeout=10)
                except Exception as e:
                    self.logger.warning(f"Could not restart watcher: {e}")

            elif task_type == 'linkedin':
                from actions.linkedin_action import post_to_linkedin

                self.logger.info("Posting to LinkedIn")
                result = post_to_linkedin(content=draft_content)
                success = result.get('status') == 'success'

            # If successful, move to Done
            if success:
                done_dir = self.vault_path / "Done"
                done_dir.mkdir(exist_ok=True)

                # Update frontmatter
                frontmatter['status'] = 'completed'
                frontmatter['completed_at'] = datetime.now().isoformat()

                # Write to Done
                done_file = done_dir / task_file.name
                output_parts = ["---"]
                output_parts.append(yaml.dump(frontmatter, default_flow_style=False))
                output_parts.append("---")
                output_parts.append("")
                output_parts.append(body)

                done_file.write_text("\n".join(output_parts), encoding='utf-8')

                # Remove from Approved
                task_file.unlink()

                self.logger.info(f"Task completed and moved to Done: {task_file.name}")
                return True
            else:
                self.logger.error(f"Action execution failed for {task_file.name}")
                return False

        except Exception as e:
            self.logger.error(f"Error executing task {task_file.name}: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _execute_email_action(self, task: TaskFile, task_file: Path) -> bool:
        """Execute email sending action."""
        try:
            import re

            # Parse email details from task content
            content = task.content

            # Extract recipient
            to_email = None
            if hasattr(task, 'email_from'):
                to_email = task.email_from
            else:
                # Try to extract from content
                to_match = re.search(r'\*\*To\*\*:\s*([^\n]+)', content)
                if to_match:
                    to_email = to_match.group(1).strip()

            # Extract subject
            subject = None
            if hasattr(task, 'email_subject'):
                subject = f"Re: {task.email_subject}"
            else:
                subject_match = re.search(r'\*\*Subject\*\*:\s*([^\n]+)', content)
                if subject_match:
                    subject = subject_match.group(1).strip()

            # Extract email body from Draft Reply section
            body_match = re.search(r'## Draft Reply.*?\n\n(.*?)(?:\n---|\Z)', content, re.DOTALL)
            if body_match:
                body = body_match.group(1).strip()
                # Remove metadata lines
                body_lines = [line for line in body.split('\n') if not line.startswith('**')]
                body = '\n'.join(body_lines).strip()
            else:
                self.logger.error("Could not extract email body from task")
                return False

            if not to_email or not subject or not body:
                self.logger.error(f"Missing email details: to={to_email}, subject={subject}, body={'present' if body else 'missing'}")
                return False

            # Import and call gmail action
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from actions.gmail_action import send_email

            self.logger.info(f"Sending email to {to_email}")
            result = send_email(to=to_email, subject=subject, body=body)

            if result['status'] == 'success':
                self.logger.info(f"Email sent successfully: {result.get('message_id')}")
                return True
            else:
                self.logger.error(f"Email sending failed: {result.get('error')}")
                return False

        except Exception as e:
            self.logger.error(f"Error executing email action: {e}")
            return False

    def _execute_whatsapp_action(self, task: TaskFile, task_file: Path) -> bool:
        """Execute WhatsApp sending action."""
        try:
            # Parse WhatsApp details from task content
            content = task.content

            # Extract recipient
            to_number = None
            if hasattr(task, 'sender_number'):
                to_number = task.sender_number
            else:
                import re
                to_match = re.search(r'\*\*To\*\*:\s*([^\n]+)', content)
                if to_match:
                    to_number = to_match.group(1).strip()
                    # Extract just the phone number
                    number_match = re.search(r'\+\d+', to_number)
                    if number_match:
                        to_number = number_match.group(0)

            # Extract message from Draft Reply section
            message_match = re.search(r'## Draft Reply.*?\n\n(.*?)(?:\n---|\Z)', content, re.DOTALL)
            if message_match:
                message = message_match.group(1).strip()
                # Remove metadata lines
                message_lines = [line for line in message.split('\n') if not line.startswith('**')]
                message = '\n'.join(message_lines).strip()
            else:
                self.logger.error("Could not extract WhatsApp message from task")
                return False

            if not to_number or not message:
                self.logger.error(f"Missing WhatsApp details: to={to_number}, message={'present' if message else 'missing'}")
                return False

            # Import and call whatsapp action
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from actions.whatsapp_action import send_whatsapp

            self.logger.info(f"Sending WhatsApp to {to_number}")
            result = send_whatsapp(to=to_number, message=message)

            if result['status'] == 'success':
                self.logger.info(f"WhatsApp sent successfully (placeholder mode): {result.get('message_sid')}")
                return True
            else:
                self.logger.error(f"WhatsApp sending failed: {result.get('error')}")
                return False

        except Exception as e:
            self.logger.error(f"Error executing WhatsApp action: {e}")
            return False

    def _execute_linkedin_action(self, task: TaskFile, task_file: Path) -> bool:
        """Execute LinkedIn posting action."""
        try:
            # Parse LinkedIn post content from task
            content = task.content

            # Extract post content from Draft LinkedIn Post section
            import re
            post_match = re.search(r'### Post Content:\s*\n\n(.*?)(?:\n###|\n---|\Z)', content, re.DOTALL)
            if post_match:
                post_content = post_match.group(1).strip()
            else:
                self.logger.error("Could not extract LinkedIn post content from task")
                return False

            if not post_content:
                self.logger.error("LinkedIn post content is empty")
                return False

            # Import and call linkedin action
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from actions.linkedin_action import post_to_linkedin

            self.logger.info("Posting to LinkedIn")
            result = post_to_linkedin(content=post_content)

            if result['status'] == 'success':
                self.logger.info(f"LinkedIn post created successfully: {result.get('post_id')}")
                return True
            else:
                self.logger.error(f"LinkedIn posting failed: {result.get('error')}")
                return False

        except Exception as e:
            self.logger.error(f"Error executing LinkedIn action: {e}")
            return False

    def _move_approved_to_done(self, task_file: Path) -> None:
        """Move approved task to Done folder after execution."""
        # Ensure Done folder exists
        self.done.mkdir(parents=True, exist_ok=True)

        # Read task and update metadata
        task = self._read_task_file(task_file)
        task.status = 'done'
        task.processed = datetime.now().isoformat()
        task.executed = datetime.now().isoformat()

        # Write updated task to Done
        dest_path = self.done / task_file.name
        self._write_task_file(dest_path, task)

        # Remove from Approved
        task_file.unlink()

        self.logger.info(f"Moved executed task {task_file.name} to Done")

    def _task_requires_approval(self, task: TaskFile, task_file: Path) -> bool:
        """
        Check if task requires approval based on content markers.

        Args:
            task: TaskFile object
            task_file: Path to task file

        Returns:
            True if task requires approval
        """
        # Check frontmatter
        if hasattr(task, 'requires_approval') and task.requires_approval:
            return True

        # Check content for approval markers
        content = task.content.lower()
        approval_markers = [
            'awaiting approval',
            'pending approval',
            'requires approval',
            'draft reply',
            'draft post',
            'approval required'
        ]

        return any(marker in content for marker in approval_markers)

    def _task_is_completed(self, task: TaskFile, task_file: Path) -> bool:
        """
        Check if task is completed based on status and content.

        Args:
            task: TaskFile object
            task_file: Path to task file

        Returns:
            True if task is completed
        """
        # Check status in frontmatter
        if hasattr(task, 'status') and task.status in ['done', 'completed']:
            return True

        # Check content for completion markers
        content = task.content.lower()
        completion_markers = [
            'status: sent',
            'reply sent',
            'task completed',
            'action completed'
        ]

        return any(marker in content for marker in completion_markers)

    def _extract_message_body(self, draft_content: str) -> str:
        """
        Extract clean message body from draft content.
        Removes metadata headers, footers, and formatting.

        Args:
            draft_content: Raw draft content with metadata

        Returns:
            Clean message body text
        """
        import re

        # Remove "## Draft Reply" header variations
        draft_content = re.sub(r'^##\s*Draft\s*(Reply|Response).*?\n', '', draft_content, flags=re.MULTILINE | re.IGNORECASE)

        # Split by "---" separator to remove footer
        if '\n---' in draft_content:
            draft_content = draft_content.split('\n---')[0]

        # Remove metadata lines (lines starting with **Key**: value)
        lines = draft_content.split('\n')
        clean_lines = []

        for line in lines:
            # Skip metadata lines like "**To**: ...", "**Draft Created**: ...", etc.
            if re.match(r'^\*\*[^*]+\*\*:\s*.+', line.strip()):
                continue
            # Skip empty lines at the start
            if not clean_lines and not line.strip():
                continue
            clean_lines.append(line)

        # Join and clean up
        message_body = '\n'.join(clean_lines).strip()

        # Remove any leading/trailing whitespace and extra newlines
        message_body = re.sub(r'\n{3,}', '\n\n', message_body)

        return message_body

    def _move_to_pending_approval_simple(self, task_file: Path) -> None:
        """
        Move task to Pending_Approval folder (simple version without classification).

        Args:
            task_file: Path to task file in Needs_Action
        """
        # Ensure Pending_Approval folder exists
        self.pending_approval.mkdir(parents=True, exist_ok=True)

        # Move file
        dest_path = self.pending_approval / task_file.name
        shutil.move(str(task_file), str(dest_path))

        self.logger.info(f"Moved {task_file.name} to Pending_Approval")

    def _build_task_prompt(self, task: TaskFile, task_file: Path) -> str:
        """
        Build prompt for Claude Code to process a task.

        Args:
            task: TaskFile object
            task_file: Path to task file

        Returns:
            Prompt string for Claude Code
        """
        # Build a concise prompt that references the skills
        prompt = f"""Process task: {task_file.name}

Type: {task.type} | Source: {task.source} | Priority: {task.priority}

Use Agent Skills from .claude/skills/:
- whatsapp-reply (for WhatsApp tasks)
- email-reply (for email tasks)
- linkedin-post (for LinkedIn tasks)
- create-plan (for complex tasks)
- request-approval (for sensitive actions)

Read {task_file.absolute()}, process it with the appropriate skill, update the file with results. Add "Draft Reply (Awaiting Approval)" if needs approval, or "Status: Sent" if completed."""
        return prompt

    def _call_claude_code(self, prompt: str) -> Dict[str, Any]:
        """
        Call Claude Code CLI to process a task.

        Args:
            prompt: Prompt for Claude Code

        Returns:
            Result dictionary with success status and any error messages
        """
        try:
            # Build command - use --print for non-interactive mode
            # and --dangerously-skip-permissions for autonomous execution
            # On Windows, use shell=True to execute .cmd files
            cmd = [
                'ccr',
                'code',
                '--print',
                '--dangerously-skip-permissions',
                '--output-format', 'text',
                prompt
            ]

            self.logger.debug(f"Calling Claude Code with prompt length: {len(prompt)} chars")

            # Execute command with vault as working directory
            # Use shell=True on Windows to find ccr in PATH
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                cwd=str(self.vault_path.absolute()),
                shell=True  # Required for Windows .cmd files
            )

            if result.returncode == 0:
                self.logger.debug("Claude Code execution successful")
                return {
                    'success': True,
                    'output': result.stdout,
                    'error': None
                }
            else:
                self.logger.error(f"Claude Code failed with return code {result.returncode}")
                self.logger.error(f"STDERR: {result.stderr}")
                return {
                    'success': False,
                    'output': result.stdout,
                    'error': result.stderr
                }

        except subprocess.TimeoutExpired:
            self.logger.error("Claude Code execution timed out after 5 minutes")
            return {
                'success': False,
                'output': None,
                'error': 'Timeout after 5 minutes'
            }
        except FileNotFoundError:
            self.logger.error("ccr command not found - is Claude Code Router installed?")
            return {
                'success': False,
                'output': None,
                'error': 'ccr command not found'
            }
        except Exception as e:
            self.logger.error(f"Unexpected error calling Claude Code: {e}")
            return {
                'success': False,
                'output': None,
                'error': str(e)
            }

    def _process_pending_approval(self) -> int:
        """
        Process approved tasks in Pending_Approval folder.

        Returns:
            Number of approvals processed
        """
        if not self.pending_approval.exists():
            return 0

        task_files = list(self.pending_approval.glob('*.md'))
        processed_count = 0

        for task_file in task_files:
            try:
                # Read task file
                task = self._read_task_file(task_file)

                # Process approval
                result = self.approval_handler.process_approval(task)

                if result.status == "approved":
                    # Move to Done (MCP action execution will be added in Phase 6 & 7)
                    self._move_to_done_from_approval(task_file)
                    processed_count += 1
                    self.logger.info(f"Approved task {task_file.name} moved to Done")

                elif result.status == "rejected":
                    # Keep in Pending_Approval with rejection note
                    self.logger.info(f"Task {task_file.name} rejected, keeping in Pending_Approval")
                    # Update task file with rejection status
                    task.status = "rejected"
                    self._write_task_file(task_file, task)

                # If pending, do nothing (leave in Pending_Approval)

            except Exception as e:
                self.logger.error(f"Error processing approval for {task_file.name}: {e}")

        return processed_count

    def _move_to_done_from_approval(self, task_file: Path) -> None:
        """
        Move approved task to Done folder.

        Args:
            task_file: Path to task file in Pending_Approval
        """
        # Ensure Done folder exists
        self.done.mkdir(parents=True, exist_ok=True)

        # Read task and update metadata
        task = self._read_task_file(task_file)
        task.status = 'done'
        task.processed = datetime.now().isoformat()

        # Write updated task to Done
        dest_path = self.done / task_file.name
        self._write_task_file(dest_path, task)

        # Remove from Pending_Approval
        task_file.unlink()

        self.logger.info(f"Moved approved task {task_file.name} to Done")

    def _read_task_file(self, file_path: Path) -> TaskFile:
        """
        Read task file with YAML frontmatter.

        Args:
            file_path: Path to task file

        Returns:
            TaskFile object
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Split frontmatter and content
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                frontmatter = yaml.safe_load(parts[1])
                body = parts[2].strip()
                return TaskFile.from_yaml_dict(frontmatter, body)

        # No frontmatter, create minimal task
        return TaskFile(
            id=file_path.stem,
            source='file',
            type='file_drop',
            status='pending',
            priority='medium',
            created=datetime.now().isoformat(),
            content=content
        )

    def _move_to_pending_approval(self, task_file: Path, classification: Classification) -> None:
        """
        Move task to Pending_Approval folder.

        Args:
            task_file: Path to task file
            classification: Classification result
        """
        # Ensure Pending_Approval folder exists
        self.pending_approval.mkdir(parents=True, exist_ok=True)

        # Read task and update metadata
        task = self._read_task_file(task_file)
        task.requires_approval = True
        task.status = 'pending'

        # Add classification reasons to content
        reasons_text = "\n\n## Approval Required\n\n"
        reasons_text += "This task requires approval for the following reasons:\n\n"
        for reason in classification.reasons:
            reasons_text += f"- {reason}\n"

        task.content += reasons_text

        # Write updated task to Pending_Approval
        dest_path = self.pending_approval / task_file.name
        self._write_task_file(dest_path, task)

        # Remove from Needs_Action
        task_file.unlink()

        self.logger.info(f"Moved {task_file.name} to Pending_Approval: {', '.join(classification.reasons)}")

    def _move_to_done(self, task_file: Path) -> None:
        """
        Move task to Done folder.

        Args:
            task_file: Path to task file
        """
        # Ensure Done folder exists
        self.done.mkdir(parents=True, exist_ok=True)

        # Read task and update metadata
        task = self._read_task_file(task_file)
        task.status = 'done'
        task.processed = datetime.now().isoformat()

        # Write updated task to Done
        dest_path = self.done / task_file.name
        self._write_task_file(dest_path, task)

        # Remove from Needs_Action
        task_file.unlink()

        self.logger.info(f"Moved {task_file.name} to Done")

    def _write_task_file(self, file_path: Path, task: TaskFile) -> None:
        """
        Write task file with YAML frontmatter.

        Args:
            file_path: Path to write to
            task: TaskFile object
        """
        # Convert to YAML frontmatter
        frontmatter = yaml.dump(task.to_yaml_dict(), default_flow_style=False)

        # Write file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('---\n')
            f.write(frontmatter)
            f.write('---\n\n')
            f.write(task.content)

    def _update_dashboard(self) -> None:
        """Update Dashboard.md with current statistics and status."""
        dashboard_path = self.vault_path / 'Dashboard.md'

        if not dashboard_path.exists():
            self.logger.warning("Dashboard.md not found, skipping update")
            return

        try:
            # Count files in each folder
            needs_action_count = len(list(self.needs_action.glob('*.md'))) if self.needs_action.exists() else 0
            pending_approval_count = len(list(self.pending_approval.glob('*.md'))) if self.pending_approval.exists() else 0
            approved_count = len(list(self.approved.glob('*.md'))) if self.approved.exists() else 0
            done_count = len(list(self.done.glob('*.md'))) if self.done.exists() else 0

            # Load state for orchestrator info
            state = self.state_manager.load_state()

            # Get PM2 status for watchers
            try:
                import subprocess
                pm2_result = subprocess.run(['pm2', 'jlist'], capture_output=True, text=True, timeout=5)
                pm2_data = json.loads(pm2_result.stdout) if pm2_result.returncode == 0 else []

                # Find watcher statuses
                gmail_status = "offline"
                whatsapp_status = "offline"
                linkedin_status = "offline"

                for process in pm2_data:
                    if process.get('name') == 'silver-gmail-watcher' and process.get('pm2_env', {}).get('status') == 'online':
                        gmail_status = "online"
                    elif process.get('name') == 'silver-whatsapp-watcher' and process.get('pm2_env', {}).get('status') == 'online':
                        whatsapp_status = "online"
                    elif process.get('name') == 'silver-linkedin-watcher' and process.get('pm2_env', {}).get('status') == 'online':
                        linkedin_status = "online"
            except Exception as e:
                self.logger.warning(f"Could not get PM2 status: {e}")
                gmail_status = "unknown"
                whatsapp_status = "unknown"
                linkedin_status = "unknown"

            # Read current dashboard
            with open(dashboard_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Update Last Updated timestamp at the top
            now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            content = self._replace_section(content, '**Last Updated**:', f'**Last Updated**: {now_str}')

            # Update Task Statistics section
            stats_section = f"""## Task Statistics

- **Needs Action**: {needs_action_count} tasks
- **Pending Approval**: {pending_approval_count} tasks
- **Approved**: {approved_count} tasks
- **Done**: {done_count} tasks
- **Last Updated**: {now_str}"""

            content = self._replace_section_block(content, '## Task Statistics', stats_section)

            # Update Orchestrator Status section
            orchestrator_status = "running" if state.status == "running" else "stopped"
            last_run = state.last_run if state.last_run else "Never"

            orchestrator_section = f"""## Orchestrator Status

- **Current Cycle**: {state.current_cycle}
- **Last Run**: {last_run}
- **Status**: {orchestrator_status.title()}
- **Cycle Interval**: 5 minutes

### Today's Processing

- **Tasks Processed**: {state.statistics.tasks_processed_today}
- **Tasks Approved**: {state.statistics.tasks_approved_today}
- **Tasks Rejected**: {state.statistics.tasks_rejected_today}
- **Errors**: {state.statistics.errors_today}"""

            content = self._replace_section_block(content, '## Orchestrator Status', orchestrator_section)

            # Update Watcher Status sections
            gmail_emoji = "🟢" if gmail_status == "online" else "🔴"
            whatsapp_emoji = "🟢" if whatsapp_status == "online" else "🔴"
            linkedin_emoji = "🟢" if linkedin_status == "online" else "🔴"

            # Update Gmail Watcher status
            content = self._replace_section(content, '### 📧 Gmail Watcher', f'### 📧 Gmail Watcher\n- **Status**: {gmail_emoji} {gmail_status.title()}')

            # Update WhatsApp Watcher status
            content = self._replace_section(content, '### 💬 WhatsApp Watcher', f'### 💬 WhatsApp Watcher\n- **Status**: {whatsapp_emoji} {whatsapp_status.title()}')

            # Update System Health - Lock Status
            lock_emoji = "🔓" if not state.lock.locked else "🔒"
            lock_status = "Unlocked" if not state.lock.locked else f"Locked by {state.lock.locked_by}"
            content = self._replace_section(content, '- **Orchestrator Lock**:', f'- **Orchestrator Lock**: {lock_emoji} {lock_status}')

            # Write updated dashboard
            with open(dashboard_path, 'w', encoding='utf-8') as f:
                f.write(content)

            self.logger.info(f"Dashboard updated: {needs_action_count} needs action, {pending_approval_count} pending, {done_count} done")

        except Exception as e:
            self.logger.error(f"Error updating dashboard: {e}")

    def _replace_section(self, content: str, marker: str, replacement: str) -> str:
        """Replace a single line section in the dashboard."""
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if marker in line:
                lines[i] = replacement
                break
        return '\n'.join(lines)

    def _replace_section_block(self, content: str, section_header: str, new_section: str) -> str:
        """Replace a multi-line section block in the dashboard."""
        if section_header in content:
            parts = content.split(section_header)
            if len(parts) > 1:
                # Find next section (starts with ##) or end
                after_section = parts[1].split('\n## ', 1)
                if len(after_section) > 1:
                    content = parts[0] + new_section + '\n\n## ' + after_section[1]
                else:
                    content = parts[0] + new_section
        return content

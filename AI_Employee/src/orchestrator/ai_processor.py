"""
AI-powered task processor for Silver Tier AI Employee
Uses Claude API (Anthropic or local CCR) or Gemini API for intelligent task processing
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

# Load environment variables from .env file
from dotenv import load_dotenv
_env_file = Path(__file__).parent.parent.parent / ".env"
if _env_file.exists():
    load_dotenv(_env_file)

# Try importing both SDKs
try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


class AIProcessor:
    """AI-powered task processor using Claude or Gemini"""

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.skills_path = Path(__file__).parent.parent.parent / ".claude" / "skills"

        # Initialize AI client
        self.ai_client = None
        self.ai_type = None
        self._initialize_ai_client()

        # Load Agent Skills as prompts
        self.skills = self._load_skills()

    def _initialize_ai_client(self):
        """Initialize AI client (Anthropic or Gemini)"""

        # Try Anthropic first (including local CCR)
        if ANTHROPIC_AVAILABLE:
            api_key = os.getenv("ANTHROPIC_API_KEY", "test")
            base_url = os.getenv("ANTHROPIC_BASE_URL")

            try:
                if base_url:
                    # Local CCR setup
                    self.ai_client = Anthropic(
                        api_key=api_key,
                        base_url=base_url
                    )
                    self.ai_type = "anthropic_local"
                    print(f"[OK] AI Client initialized: Anthropic (Local CCR at {base_url})")
                elif api_key and api_key != "test":
                    # Real Anthropic API
                    self.ai_client = Anthropic(api_key=api_key)
                    self.ai_type = "anthropic"
                    print("[OK] AI Client initialized: Anthropic API")
            except Exception as e:
                print(f"[WARN] Anthropic initialization failed: {e}")

        # Try Gemini if Anthropic not available
        if not self.ai_client and GEMINI_AVAILABLE:
            api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
            if api_key:
                try:
                    genai.configure(api_key=api_key)
                    self.ai_client = genai.GenerativeModel('gemini-pro')
                    self.ai_type = "gemini"
                    print("[OK] AI Client initialized: Gemini API")
                except Exception as e:
                    print(f"[WARN] Gemini initialization failed: {e}")

        if not self.ai_client:
            raise RuntimeError(
                "No AI client available. Please configure:\n"
                "  - ANTHROPIC_API_KEY for Claude API, OR\n"
                "  - GEMINI_API_KEY for Gemini API, OR\n"
                "  - ANTHROPIC_BASE_URL for local CCR"
            )

    def _load_skills(self) -> Dict[str, str]:
        """Load Agent Skills from .claude/skills/ directory"""
        skills = {}

        if not self.skills_path.exists():
            print(f"[WARN] Skills directory not found: {self.skills_path}")
            return skills

        # Load process-task skill
        process_task_skill = self.skills_path / "process-task" / "SKILL.md"
        if process_task_skill.exists():
            skills["process-task"] = process_task_skill.read_text(encoding="utf-8")
            print(f"[OK] Loaded skill: process-task")

        # Load other skills
        for skill_dir in self.skills_path.iterdir():
            if skill_dir.is_dir() and skill_dir.name != "process-task":
                skill_file = skill_dir / "SKILL.md"
                if skill_file.exists():
                    skills[skill_dir.name] = skill_file.read_text(encoding="utf-8")
                    print(f"[OK] Loaded skill: {skill_dir.name}")

        return skills

    def _call_ai(self, prompt: str, max_tokens: int = 4000) -> str:
        """Call AI API (Anthropic or Gemini)"""

        if self.ai_type in ["anthropic", "anthropic_local"]:
            response = self.ai_client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text

        elif self.ai_type == "gemini":
            response = self.ai_client.generate_content(prompt)
            return response.text

        else:
            raise RuntimeError("No AI client available")

    def classify_task(self, task_data: Dict[str, Any]) -> Tuple[str, str]:
        """
        Classify task as SIMPLE, COMPLEX, or SENSITIVE
        Returns: (classification, reasoning)
        """

        # Build classification prompt using process-task skill
        skill_prompt = self.skills.get("process-task", "")

        prompt = f"""You are an AI assistant helping classify tasks for an AI employee system.

{skill_prompt}

Task to classify:
---
Source: {task_data.get('source', 'unknown')}
Type: {task_data.get('type', 'unknown')}
From: {task_data.get('email_from') or task_data.get('whatsapp_from') or task_data.get('linkedin_from', 'unknown')}
Subject: {task_data.get('email_subject') or task_data.get('whatsapp_message', '')[:100]}

Content:
{task_data.get('content', '')}
---

Classify this task as SIMPLE, COMPLEX, or SENSITIVE based on the criteria in the skill.

Respond in JSON format:
{{
  "classification": "SIMPLE|COMPLEX|SENSITIVE",
  "reasoning": "Brief explanation of why this classification was chosen"
}}
"""

        try:
            response = self._call_ai(prompt, max_tokens=500)

            # Parse JSON response
            # Handle markdown code blocks if present
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]

            result = json.loads(response.strip())
            return result["classification"], result["reasoning"]

        except Exception as e:
            print(f"[WARN] Classification failed: {e}")
            # Default to SIMPLE if classification fails
            return "SIMPLE", f"Classification failed: {e}"

    def create_plan(self, task_data: Dict[str, Any]) -> str:
        """
        Create Plan.md for COMPLEX tasks
        Returns: Plan content as markdown
        """

        # Build planning prompt using create-plan skill
        skill_prompt = self.skills.get("create-plan", "")

        prompt = f"""You are an AI assistant helping create execution plans for complex tasks.

{skill_prompt}

Task to plan:
---
Source: {task_data.get('source', 'unknown')}
Type: {task_data.get('type', 'unknown')}
From: {task_data.get('email_from') or task_data.get('whatsapp_from') or task_data.get('linkedin_from', 'unknown')}
Subject: {task_data.get('email_subject') or task_data.get('whatsapp_message', '')[:100]}

Content:
{task_data.get('content', '')}
---

Create a detailed execution plan for this task. Break it down into clear, actionable steps.

Format as markdown with:
# Execution Plan

## Objective
[What needs to be accomplished]

## Steps
1. [Step 1]
2. [Step 2]
...

## Success Criteria
- [Criterion 1]
- [Criterion 2]
"""

        try:
            plan = self._call_ai(prompt, max_tokens=2000)
            return plan

        except Exception as e:
            print(f"[WARN] Plan creation failed: {e}")
            return f"# Execution Plan\n\nError creating plan: {e}"

    def generate_draft(self, task_data: Dict[str, Any], classification: str) -> str:
        """
        Generate draft response based on task type and classification
        Returns: Draft content
        """

        task_type = task_data.get('type', 'unknown')

        # Select appropriate skill
        if task_type == 'email':
            skill_name = 'email-reply'
        elif task_type == 'whatsapp':
            skill_name = 'whatsapp-reply'
        elif task_type == 'linkedin':
            skill_name = 'linkedin-post'
        else:
            skill_name = 'process-task'

        skill_prompt = self.skills.get(skill_name, "")

        # Build draft generation prompt
        prompt = f"""You are an AI assistant helping draft responses for an AI employee system.

{skill_prompt}

Task details:
---
Source: {task_data.get('source', 'unknown')}
Type: {task_type}
Classification: {classification}
From: {task_data.get('email_from') or task_data.get('whatsapp_from') or task_data.get('linkedin_from', 'unknown')}
Subject: {task_data.get('email_subject') or task_data.get('whatsapp_message', '')[:100]}

Content:
{task_data.get('content', '')}
---

Generate an appropriate draft response following the guidelines in the skill.

For emails: Professional, contextual reply
For WhatsApp: Brief, professional message
For LinkedIn: Engaging post for business promotion

Return ONLY the draft content, no explanations.
"""

        try:
            draft = self._call_ai(prompt, max_tokens=1000)
            return draft.strip()

        except Exception as e:
            print(f"[WARN] Draft generation failed: {e}")
            return f"Error generating draft: {e}"

    def process_task(self, task_file: Path) -> bool:
        """
        Process a single task file with AI reasoning
        Returns: True if successful, False otherwise
        """

        try:
            # Read task file
            content = task_file.read_text(encoding='utf-8')

            # Parse frontmatter and content
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    import yaml
                    frontmatter = yaml.safe_load(parts[1])
                    body = parts[2].strip()
                else:
                    print(f"[WARN] Invalid frontmatter in {task_file.name}")
                    return False
            else:
                print(f"[WARN] No frontmatter in {task_file.name}")
                return False

            task_data = {**frontmatter, 'content': body}

            print(f"\n{'='*60}")
            print(f"Processing: {task_file.name}")
            print(f"Source: {task_data.get('source')}, Type: {task_data.get('type')}")

            # Step 1: Classify task
            classification, reasoning = self.classify_task(task_data)
            print(f"Classification: {classification}")
            print(f"Reasoning: {reasoning}")

            # Step 2: Create plan if COMPLEX
            plan_content = None
            if classification == "COMPLEX":
                print("Creating execution plan...")
                plan_content = self.create_plan(task_data)

            # Step 3: Generate draft
            print("Generating draft...")
            draft = self.generate_draft(task_data, classification)

            # Step 4: Create pending approval file
            pending_file = self.vault_path / "Pending_Approval" / task_file.name

            # Build output content
            output_parts = [
                "---",
                f"id: {task_data.get('id')}",
                f"source: {task_data.get('source')}",
                f"type: {task_data.get('type')}",
                f"status: pending_approval",
                f"classification: {classification}",
                f"processed_at: {datetime.now().isoformat()}",
            ]

            # Add source-specific fields
            if task_data.get('email_from'):
                output_parts.append(f"email_from: {task_data['email_from']}")
                output_parts.append(f"email_subject: {task_data.get('email_subject', '')}")
            elif task_data.get('whatsapp_sender') or task_data.get('whatsapp_from'):
                # Support both field names for compatibility
                sender = task_data.get('whatsapp_sender') or task_data.get('whatsapp_from')
                output_parts.append(f"whatsapp_sender: {sender}")
            elif task_data.get('linkedin_from'):
                output_parts.append(f"linkedin_from: {task_data['linkedin_from']}")

            output_parts.append("---")
            output_parts.append("")
            output_parts.append("## Original Message")
            output_parts.append(body)
            output_parts.append("")

            if plan_content:
                output_parts.append("## Execution Plan")
                output_parts.append(plan_content)
                output_parts.append("")

            output_parts.append("## Draft Response")
            output_parts.append(draft)
            output_parts.append("")
            output_parts.append("## Classification")
            output_parts.append(f"**{classification}**: {reasoning}")

            # Write pending approval file
            pending_file.write_text("\n".join(output_parts), encoding='utf-8')

            # Move original to processing
            processing_dir = self.vault_path / "Processing"
            processing_dir.mkdir(exist_ok=True)
            task_file.rename(processing_dir / task_file.name)

            print(f"[OK] Task processed successfully")
            print(f"  -> Pending approval: {pending_file.name}")
            print(f"{'='*60}\n")

            return True

        except Exception as e:
            print(f"[ERROR] Error processing {task_file.name}: {e}")
            import traceback
            traceback.print_exc()
            return False


def process_task(task_file: Path, vault_path: str) -> bool:
    """
    Process a single task file (compatible with simple_processor interface)
    """
    processor = AIProcessor(vault_path)
    return processor.process_task(task_file)

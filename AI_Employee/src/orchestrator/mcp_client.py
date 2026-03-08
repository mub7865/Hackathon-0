"""
MCP Client for Silver Tier AI Employee
Calls MCP servers to execute actions (send email, WhatsApp, LinkedIn)
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
import time


class MCPClient:
    """Client for calling MCP servers"""

    def __init__(self):
        self.mcp_config_path = Path(__file__).parent.parent.parent / ".claude" / "mcp.json"
        self.mcp_config = self._load_mcp_config()

    def _load_mcp_config(self) -> Dict[str, Any]:
        """Load MCP configuration from .claude/mcp.json"""
        if not self.mcp_config_path.exists():
            raise FileNotFoundError(f"MCP config not found: {self.mcp_config_path}")

        with open(self.mcp_config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        print(f"[OK] Loaded MCP config: {len(config.get('mcpServers', {}))} servers")
        return config

    def _call_mcp_server(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call an MCP server tool with proper initialization handshake

        Args:
            server_name: Name of MCP server (e.g., 'email', 'whatsapp', 'linkedin')
            tool_name: Name of tool to call (e.g., 'send_email', 'send_message')
            arguments: Tool arguments

        Returns:
            Tool response as dict
        """

        # Get server config
        servers = self.mcp_config.get('mcpServers', {})
        if server_name not in servers:
            raise ValueError(f"MCP server not found: {server_name}")

        server_config = servers[server_name]
        command = server_config.get('command')
        args = server_config.get('args', [])

        if not command:
            raise ValueError(f"No command specified for server: {server_name}")

        print(f"Calling MCP server: {server_name}.{tool_name}")

        try:
            # Start MCP server process
            process = subprocess.Popen(
                [command] + args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                bufsize=1
            )

            # Step 1: Send initialize request
            init_request = {
                "jsonrpc": "2.0",
                "id": 0,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "silver-tier-employee",
                        "version": "1.0.0"
                    }
                }
            }
            process.stdin.write(json.dumps(init_request) + "\n")
            process.stdin.flush()

            # Step 2: Wait for initialize response
            init_response = process.stdout.readline()
            if init_response:
                try:
                    init_result = json.loads(init_response)
                    if 'error' in init_result:
                        raise RuntimeError(f"MCP initialization error: {init_result['error']}")
                except json.JSONDecodeError:
                    pass  # Continue anyway

            # Step 3: Send initialized notification
            initialized_notif = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized"
            }
            process.stdin.write(json.dumps(initialized_notif) + "\n")
            process.stdin.flush()

            # Step 4: Send tools/call request
            tool_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            process.stdin.write(json.dumps(tool_request) + "\n")
            process.stdin.flush()

            # Step 5: Read response
            response_line = process.stdout.readline()
            if response_line:
                try:
                    response = json.loads(response_line)
                    if response.get('id') == 1:
                        if 'result' in response:
                            process.stdin.close()
                            process.terminate()
                            return response['result']
                        elif 'error' in response:
                            process.stdin.close()
                            process.terminate()
                            raise RuntimeError(f"MCP error: {response['error']}")
                except json.JSONDecodeError as e:
                    raise RuntimeError(f"Invalid JSON response: {e}")

            # Clean up
            process.stdin.close()
            process.terminate()
            process.wait(timeout=5)

            raise RuntimeError(f"No valid response from MCP server: {server_name}")

        except subprocess.TimeoutExpired:
            process.kill()
            raise RuntimeError(f"MCP server timeout: {server_name}")
        except Exception as e:
            if process.poll() is None:
                process.kill()
            raise RuntimeError(f"MCP call failed: {e}")

    def send_email(self, to: str, subject: str, body: str, cc: Optional[List[str]] = None) -> bool:
        """
        Send email via email MCP server

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body
            cc: Optional CC recipients

        Returns:
            True if successful, False otherwise
        """

        try:
            arguments = {
                "to": to,
                "subject": subject,
                "body": body
            }

            if cc:
                arguments["cc"] = cc

            result = self._call_mcp_server("email", "send_email", arguments)

            # Parse the result - MCP returns TextContent with JSON string
            if result and 'content' in result:
                import json
                result_text = result['content'][0]['text']
                result_data = json.loads(result_text)

                if result_data.get('status') == 'success':
                    print(f"[OK] Email sent to {to}")
                    return True
                else:
                    error_msg = result_data.get('error', 'Unknown error')
                    print(f"[ERROR] Email send failed: {error_msg}")
                    return False
            else:
                print(f"[ERROR] Invalid MCP response for email")
                return False

        except Exception as e:
            print(f"[ERROR] Email send failed: {e}")
            return False

    def send_whatsapp(self, to: str, message: str) -> bool:
        """
        Send WhatsApp message via whatsapp MCP server

        Args:
            to: Recipient phone number or name
            message: Message content

        Returns:
            True if successful, False otherwise
        """

        try:
            arguments = {
                "to": to,
                "message": message
            }

            result = self._call_mcp_server("whatsapp", "send_whatsapp", arguments)

            # Parse the result - MCP returns TextContent with JSON string
            if result and 'content' in result:
                import json
                result_text = result['content'][0]['text']
                result_data = json.loads(result_text)

                if result_data.get('status') == 'success':
                    print(f"[OK] WhatsApp sent to {to}")
                    return True
                else:
                    error_msg = result_data.get('error', 'Unknown error')
                    print(f"[ERROR] WhatsApp send failed: {error_msg}")
                    return False
            else:
                print(f"[ERROR] Invalid MCP response for WhatsApp")
                return False

        except Exception as e:
            print(f"[ERROR] WhatsApp send failed: {e}")
            return False

    def post_linkedin(self, content: str, visibility: str = "PUBLIC") -> bool:
        """
        Post to LinkedIn via linkedin MCP server

        Args:
            content: Post content
            visibility: Post visibility (PUBLIC, CONNECTIONS, etc.)

        Returns:
            True if successful, False otherwise
        """

        try:
            arguments = {
                "content": content,
                "visibility": visibility
            }

            result = self._call_mcp_server("linkedin", "create_post", arguments)

            print(f"[OK] LinkedIn post created")
            return True

        except Exception as e:
            print(f"[ERROR] LinkedIn post failed: {e}")
            return False

    def execute_task(self, task_data: Dict[str, Any], draft_content: str) -> bool:
        """
        Execute approved task by calling appropriate MCP server

        Args:
            task_data: Task metadata from frontmatter
            draft_content: Approved draft content

        Returns:
            True if successful, False otherwise
        """

        task_type = task_data.get('type', 'unknown')

        try:
            if task_type == 'email':
                # Send email
                to = task_data.get('email_from')
                if not to:
                    print(f"[ERROR] No recipient found in task data (email_from)")
                    return False

                subject = task_data.get('email_subject', 'Re: Your message')

                # Add "Re: " prefix if not already present
                if not subject.startswith('Re:'):
                    subject = f"Re: {subject}"

                print(f"[DEBUG] Sending email to: {to}, subject: {subject}")
                return self.send_email(to, subject, draft_content)

            elif task_type == 'whatsapp':
                # Send WhatsApp message
                # Try both field names for compatibility
                to = task_data.get('whatsapp_sender') or task_data.get('whatsapp_from')
                if not to:
                    print(f"[ERROR] No recipient found in task data (whatsapp_sender or whatsapp_from)")
                    return False
                return self.send_whatsapp(to, draft_content)

            elif task_type == 'linkedin':
                # Post to LinkedIn
                return self.post_linkedin(draft_content)

            else:
                print(f"[WARN] Unknown task type: {task_type}")
                return False

        except Exception as e:
            print(f"[ERROR] Task execution failed: {e}")
            import traceback
            traceback.print_exc()
            return False


# Convenience function for backward compatibility
def execute_approved_task(task_file: Path, vault_path: str) -> bool:
    """
    Execute an approved task using MCP servers

    Args:
        task_file: Path to approved task file
        vault_path: Path to vault directory

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
                import yaml
                frontmatter = yaml.safe_load(parts[1])
                body = parts[2].strip()
            else:
                print(f"[WARN] Invalid frontmatter in {task_file.name}")
                return False
        else:
            print(f"[WARN] No frontmatter in {task_file.name}")
            return False

        # Extract draft content based on task type
        task_type = frontmatter.get('type', 'unknown')
        draft_content = ""

        if task_type == 'linkedin':
            # For LinkedIn, extract from "### Post Content:" section
            if "### Post Content:" in body:
                content_section = body.split("### Post Content:")[1]
                # Get content until "### Expected Outcome:" or next major section
                if "### Expected Outcome:" in content_section:
                    draft_content = content_section.split("### Expected Outcome:")[0].strip()
                elif "---" in content_section:
                    draft_content = content_section.split("---")[0].strip()
                else:
                    draft_content = content_section.strip()

        elif task_type == 'whatsapp':
            # For WhatsApp, extract from "## Draft Response" section
            if "## Draft Response" in body:
                draft_section = body.split("## Draft Response")[1]
                # Get content until "## Classification" or next section
                if "## Classification" in draft_section:
                    draft_content = draft_section.split("## Classification")[0].strip()
                elif "---" in draft_section:
                    draft_content = draft_section.split("---")[0].strip()
                else:
                    draft_content = draft_section.strip()

        elif task_type == 'email':
            # For Email, extract from "## Draft Response" section
            if "## Draft Response" in body:
                draft_section = body.split("## Draft Response")[1]
                # Get content until "## Classification" or next section
                if "## Classification" in draft_section:
                    draft_content = draft_section.split("## Classification")[0].strip()
                else:
                    draft_content = draft_section.strip()

        else:
            # Generic extraction for unknown types
            if "## Draft Response" in body:
                draft_section = body.split("## Draft Response")[1]
                if "##" in draft_section:
                    draft_content = draft_section.split("##")[0].strip()
                else:
                    draft_content = draft_section.strip()

        if not draft_content:
            print(f"[WARN] No draft content found in {task_file.name}")
            return False

        # Execute via MCP
        client = MCPClient()
        success = client.execute_task(frontmatter, draft_content)

        if success:
            # Move to Done
            done_dir = Path(vault_path) / "Done"
            done_dir.mkdir(exist_ok=True)

            # Update status in frontmatter
            frontmatter['status'] = 'completed'
            frontmatter['completed_at'] = time.strftime('%Y-%m-%dT%H:%M:%S')

            # Write updated file to Done
            done_file = done_dir / task_file.name
            output_parts = ["---"]
            for key, value in frontmatter.items():
                output_parts.append(f"{key}: {value}")
            output_parts.append("---")
            output_parts.append("")
            output_parts.append(body)

            done_file.write_text("\n".join(output_parts), encoding='utf-8')

            # Remove from Approved
            task_file.unlink()

            print(f"[OK] Task completed: {task_file.name}")
            return True
        else:
            print(f"[ERROR] Task execution failed: {task_file.name}")
            return False

    except Exception as e:
        print(f"[ERROR] Error executing task {task_file.name}: {e}")
        import traceback
        traceback.print_exc()
        return False

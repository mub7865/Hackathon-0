"""
Social Media MCP Server
Exposes social media operations (posting, engagement monitoring) as MCP tools
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.actions.social_media_actions import (
    process_post_request,
    process_approved_post,
    get_pending_posts
)
from src.models.social_post import PostPlatform
from src.utils.security_utils import (
    validate_description,
    sanitize_file_path,
    check_rate_limit,
    sanitize_text
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SocialMediaMCPServer:
    """
    MCP Server for social media operations

    Provides tools for:
    - Creating Facebook posts
    - Creating Instagram posts
    - Getting pending approvals
    - Approving posts
    - Getting engagement summary
    """

    def __init__(self, vault_path: Optional[str] = None):
        """
        Initialize Social Media MCP Server

        Args:
            vault_path: Path to vault directory (optional)
        """
        self.vault_path = vault_path or os.getenv('VAULT_PATH', str(Path(__file__).parent.parent.parent / 'vault'))
        self.vault_path = Path(self.vault_path)

        logger.info(f"Initialized Social Media MCP Server with vault: {self.vault_path}")

    def get_tools(self) -> List[Dict[str, Any]]:
        """
        Get list of available MCP tools

        Returns:
            List of tool definitions
        """
        return [
            {
                "name": "create_facebook_post",
                "description": "Create a Facebook post. Requires approval before publishing.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "Post content/text (max 63,206 characters)"
                        },
                        "image_path": {
                            "type": "string",
                            "description": "Path to image file (optional)"
                        },
                        "scheduled_time": {
                            "type": "string",
                            "description": "Schedule post for later (ISO format, optional)"
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Hashtags (optional)"
                        }
                    },
                    "required": ["content"]
                }
            },
            {
                "name": "create_instagram_post",
                "description": "Create an Instagram post. Requires image and approval before publishing.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "Post caption (max 2,200 characters)"
                        },
                        "image_path": {
                            "type": "string",
                            "description": "Path to image file (required for Instagram)"
                        },
                        "scheduled_time": {
                            "type": "string",
                            "description": "Schedule post for later (ISO format, optional)"
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Hashtags (optional)"
                        }
                    },
                    "required": ["content", "image_path"]
                }
            },
            {
                "name": "get_pending_posts",
                "description": "Get list of social media posts pending approval.",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "approve_post",
                "description": "Approve a pending social media post and publish it.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "task_file": {
                            "type": "string",
                            "description": "Path to task file in Pending_Approval folder"
                        },
                        "approved_by": {
                            "type": "string",
                            "description": "Name of approver"
                        }
                    },
                    "required": ["task_file", "approved_by"]
                }
            },
            {
                "name": "get_engagement_summary",
                "description": "Get summary of recent social media engagement (comments, messages, reactions).",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "platform": {
                            "type": "string",
                            "enum": ["facebook", "instagram", "all"],
                            "description": "Filter by platform (optional, defaults to 'all')"
                        },
                        "days": {
                            "type": "integer",
                            "description": "Number of days to look back (default: 7)"
                        }
                    },
                    "required": []
                }
            }
        ]

    def handle_create_facebook_post(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle create_facebook_post tool call

        Args:
            arguments: Tool arguments

        Returns:
            Result dictionary
        """
        try:
            # Rate limiting
            is_allowed, error_msg = check_rate_limit('mcp_create_facebook_post', max_requests=10, window=86400)  # 10 posts per day
            if not is_allowed:
                return {
                    "success": False,
                    "error": error_msg
                }

            # Validate and sanitize content
            is_valid, error_msg, sanitized_content = validate_description(arguments['content'], 'content')
            if not is_valid:
                return {
                    "success": False,
                    "error": f"Validation failed: {error_msg}"
                }

            # Check content length
            if len(sanitized_content) > 63206:
                return {
                    "success": False,
                    "error": "Facebook post content exceeds maximum length (63,206 characters)"
                }

            # Validate image path if provided
            if 'image_path' in arguments and arguments['image_path']:
                is_valid, error_msg, sanitized_path = sanitize_file_path(arguments['image_path'])
                if not is_valid:
                    return {
                        "success": False,
                        "error": f"Invalid image path: {error_msg}"
                    }
                arguments['image_path'] = sanitized_path

            # Create task file
            task_file = self._create_post_task_file(
                platform='facebook',
                content=sanitized_content,
                image_path=arguments.get('image_path'),
                scheduled_time=arguments.get('scheduled_time'),
                tags=arguments.get('tags', [])
            )

            # Process post request (moves to Pending_Approval)
            status = process_post_request(task_file)

            return {
                "success": True,
                "status": status,
                "message": "Facebook post created and pending approval",
                "task_file": task_file
            }

        except Exception as e:
            logger.error(f"Error handling create_facebook_post: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def handle_create_instagram_post(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle create_instagram_post tool call

        Args:
            arguments: Tool arguments

        Returns:
            Result dictionary
        """
        try:
            # Rate limiting (Instagram has stricter limits)
            is_allowed, error_msg = check_rate_limit('mcp_create_instagram_post', max_requests=5, window=86400)  # 5 posts per day
            if not is_allowed:
                return {
                    "success": False,
                    "error": error_msg
                }

            # Validate and sanitize content
            is_valid, error_msg, sanitized_content = validate_description(arguments['content'], 'content')
            if not is_valid:
                return {
                    "success": False,
                    "error": f"Validation failed: {error_msg}"
                }

            # Check content length
            if len(sanitized_content) > 2200:
                return {
                    "success": False,
                    "error": "Instagram post content exceeds maximum length (2,200 characters)"
                }

            # Validate image path (required for Instagram)
            if not arguments.get('image_path'):
                return {
                    "success": False,
                    "error": "Instagram posts require an image"
                }

            is_valid, error_msg, sanitized_path = sanitize_file_path(arguments['image_path'])
            if not is_valid:
                return {
                    "success": False,
                    "error": f"Invalid image path: {error_msg}"
                }

            # Check if image file exists
            if not Path(sanitized_path).exists():
                return {
                    "success": False,
                    "error": f"Image file not found: {sanitized_path}"
                }

            # Create task file
            task_file = self._create_post_task_file(
                platform='instagram',
                content=sanitized_content,
                image_path=sanitized_path,
                scheduled_time=arguments.get('scheduled_time'),
                tags=arguments.get('tags', [])
            )

            # Process post request (moves to Pending_Approval)
            status = process_post_request(task_file)

            return {
                "success": True,
                "status": status,
                "message": "Instagram post created and pending approval",
                "task_file": task_file
            }

        except Exception as e:
            logger.error(f"Error handling create_instagram_post: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def handle_get_pending_posts(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle get_pending_posts tool call

        Args:
            arguments: Tool arguments (empty)

        Returns:
            Result dictionary
        """
        try:
            pending = get_pending_posts(str(self.vault_path))

            # Parse each pending file to get details
            pending_details = []
            for task_file in pending:
                from src.utils.file_utils import parse_task_file
                frontmatter, body = parse_task_file(task_file)

                # Extract content preview
                content_preview = frontmatter.get('content', '')[:100]
                if not content_preview:
                    # Try to extract from body
                    lines = body.split('\n')
                    for line in lines:
                        if line.strip() and not line.startswith('#'):
                            content_preview = line.strip()[:100]
                            break

                pending_details.append({
                    'task_file': task_file,
                    'platform': frontmatter.get('platform', 'unknown'),
                    'post_id': frontmatter.get('post_id', ''),
                    'content_preview': content_preview,
                    'has_image': bool(frontmatter.get('image_path')),
                    'created': frontmatter.get('created', ''),
                    'approval_reason': frontmatter.get('approval_reason', 'All social media posts require approval')
                })

            return {
                "success": True,
                "count": len(pending_details),
                "pending_posts": pending_details
            }

        except Exception as e:
            logger.error(f"Error handling get_pending_posts: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def handle_approve_post(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle approve_post tool call

        Args:
            arguments: Tool arguments

        Returns:
            Result dictionary
        """
        try:
            # Rate limiting
            is_allowed, error_msg = check_rate_limit('mcp_approve_post')
            if not is_allowed:
                return {
                    "success": False,
                    "error": error_msg
                }

            # Sanitize file path
            task_file = arguments['task_file']
            is_valid, error_msg, sanitized_path = sanitize_file_path(task_file, str(self.vault_path))
            if not is_valid:
                return {
                    "success": False,
                    "error": f"Invalid file path: {error_msg}"
                }
            task_file = sanitized_path

            # Validate approved_by
            is_valid, error_msg, approved_by = sanitize_text(arguments['approved_by'], 'approved_by', 100)
            if not is_valid:
                return {
                    "success": False,
                    "error": error_msg
                }

            # Update task with approval
            from src.utils.file_utils import update_task_frontmatter, move_task_file
            update_task_frontmatter(
                task_file,
                {
                    'status': 'approved',
                    'approved_by': approved_by,
                    'approved_at': datetime.now().isoformat()
                }
            )

            # Move to Approved folder
            approved_path = move_task_file(task_file, 'Approved')

            # Process approved post (publishes to platform)
            status = process_approved_post(approved_path)

            if status == 'done':
                return {
                    "success": True,
                    "status": "published",
                    "message": "Post approved and published successfully",
                    "task_file": approved_path
                }
            else:
                return {
                    "success": False,
                    "status": "error",
                    "message": "Failed to publish approved post",
                    "task_file": approved_path
                }

        except Exception as e:
            logger.error(f"Error handling approve_post: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def handle_get_engagement_summary(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle get_engagement_summary tool call

        Args:
            arguments: Tool arguments

        Returns:
            Result dictionary
        """
        try:
            platform = arguments.get('platform', 'all')
            days = arguments.get('days', 7)

            # Get engagement task files from Done folder
            done_folder = self.vault_path / 'Done'
            if not done_folder.exists():
                return {
                    "success": True,
                    "summary": {
                        "total_engagements": 0,
                        "by_platform": {},
                        "by_type": {},
                        "urgent_count": 0,
                        "responded_count": 0
                    }
                }

            # Scan engagement files
            from src.utils.file_utils import parse_task_file
            from datetime import timedelta

            cutoff_date = datetime.now() - timedelta(days=days)
            engagements = []

            for file in done_folder.glob('*.md'):
                try:
                    frontmatter, _ = parse_task_file(str(file))

                    # Check if it's an engagement file
                    if frontmatter.get('type') != 'social_media_engagement':
                        continue

                    # Check platform filter
                    file_platform = frontmatter.get('platform', '')
                    if platform != 'all' and file_platform != platform:
                        continue

                    # Check date
                    created = frontmatter.get('created', '')
                    if created:
                        created_date = datetime.fromisoformat(created)
                        if created_date < cutoff_date:
                            continue

                    engagements.append(frontmatter)

                except:
                    continue

            # Summarize engagements
            summary = {
                "total_engagements": len(engagements),
                "by_platform": {},
                "by_type": {},
                "urgent_count": 0,
                "responded_count": 0,
                "sentiment_breakdown": {
                    "positive": 0,
                    "negative": 0,
                    "neutral": 0
                }
            }

            for eng in engagements:
                # Count by platform
                plat = eng.get('platform', 'unknown')
                summary['by_platform'][plat] = summary['by_platform'].get(plat, 0) + 1

                # Count by type
                eng_type = eng.get('engagement_type', 'unknown')
                summary['by_type'][eng_type] = summary['by_type'].get(eng_type, 0) + 1

                # Count urgent
                if eng.get('is_urgent'):
                    summary['urgent_count'] += 1

                # Count responded
                if eng.get('status') == 'responded':
                    summary['responded_count'] += 1

                # Count sentiment
                sentiment = eng.get('sentiment', 'neutral')
                if sentiment in summary['sentiment_breakdown']:
                    summary['sentiment_breakdown'][sentiment] += 1

            return {
                "success": True,
                "summary": summary,
                "period_days": days
            }

        except Exception as e:
            logger.error(f"Error handling get_engagement_summary: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _create_post_task_file(
        self,
        platform: str,
        content: str,
        image_path: Optional[str] = None,
        scheduled_time: Optional[str] = None,
        tags: List[str] = None
    ) -> str:
        """
        Create task file for social media post

        Args:
            platform: Platform (facebook or instagram)
            content: Post content
            image_path: Path to image (optional)
            scheduled_time: Scheduled time (optional)
            tags: Hashtags (optional)

        Returns:
            Path to created task file
        """
        import yaml

        # Create Needs_Action folder if not exists
        needs_action = self.vault_path / 'Needs_Action'
        needs_action.mkdir(parents=True, exist_ok=True)

        # Generate task filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"post_{platform}_{timestamp}.md"
        task_file = needs_action / filename

        # Create frontmatter
        frontmatter = {
            'title': f"{platform.title()} Post",
            'type': 'social_media',
            'platform': platform,
            'content': content,
            'status': 'needs_action',
            'created': datetime.now().isoformat(),
            'priority': 'medium',
            'post_id': f"{platform}_{timestamp}"
        }

        if image_path:
            frontmatter['image_path'] = image_path
        if scheduled_time:
            frontmatter['scheduled_time'] = scheduled_time
        if tags:
            frontmatter['tags'] = tags

        # Create task file content
        file_content = "---\n"
        file_content += yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)
        file_content += "---\n\n"
        file_content += f"# {platform.title()} Post\n\n"
        file_content += f"**Platform**: {platform.title()}\n"
        file_content += f"**Status**: Pending Approval\n\n"
        file_content += "## Content\n\n"
        file_content += f"{content}\n\n"
        if image_path:
            file_content += f"**Image**: {image_path}\n\n"
        if tags:
            file_content += f"**Tags**: {', '.join(tags)}\n\n"

        # Write task file
        with open(task_file, 'w', encoding='utf-8') as f:
            f.write(file_content)

        logger.info(f"Created post task file: {task_file}")
        return str(task_file)

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a tool by name

        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments

        Returns:
            Tool result
        """
        handlers = {
            'create_facebook_post': self.handle_create_facebook_post,
            'create_instagram_post': self.handle_create_instagram_post,
            'get_pending_posts': self.handle_get_pending_posts,
            'approve_post': self.handle_approve_post,
            'get_engagement_summary': self.handle_get_engagement_summary
        }

        handler = handlers.get(tool_name)
        if not handler:
            return {
                "success": False,
                "error": f"Unknown tool: {tool_name}"
            }

        return handler(arguments)


def main():
    """Main entry point for MCP server"""
    server = SocialMediaMCPServer()

    # Print available tools
    print("Social Media MCP Server")
    print("=" * 50)
    print(f"Vault Path: {server.vault_path}")
    print(f"\nAvailable Tools ({len(server.get_tools())}):")
    for tool in server.get_tools():
        print(f"  - {tool['name']}: {tool['description']}")
    print("\nServer ready.")


if __name__ == '__main__':
    main()

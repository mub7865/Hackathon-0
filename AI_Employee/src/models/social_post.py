"""
Social Media Post Entity
Represents a social media post (Facebook/Instagram) with approval workflow
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class PostPlatform(Enum):
    """Social media platform enumeration"""
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"


class PostStatus(Enum):
    """Post status enumeration"""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    PUBLISHED = "published"
    FAILED = "failed"
    REJECTED = "rejected"


@dataclass
class SocialMediaPost:
    """
    Represents a social media post for Facebook or Instagram

    All posts require human approval before publishing
    """
    post_id: str
    platform: PostPlatform
    content: str
    image_path: Optional[str] = None
    status: PostStatus = PostStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.now)
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    published_url: Optional[str] = None
    error_message: Optional[str] = None
    audit_trail: List[Dict[str, Any]] = field(default_factory=list)

    # Metadata
    scheduled_time: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    mentions: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Add initial audit entry and convert string status to enum if needed"""
        # Convert string status to enum if needed
        if isinstance(self.status, str):
            self.status = PostStatus(self.status)

        # Convert string platform to enum if needed
        if isinstance(self.platform, str):
            self.platform = PostPlatform(self.platform)

        self.add_audit_entry('created', 'system', 'Post draft created')

    def add_audit_entry(self, action: str, user: str, details: str = "") -> None:
        """Add entry to audit trail"""
        self.audit_trail.append({
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'user': user,
            'details': details,
            'status': self.status.value
        })

    def request_approval(self) -> None:
        """Move post to pending approval"""
        self.status = PostStatus.PENDING_APPROVAL
        self.add_audit_entry('approval_requested', 'system', 'Post submitted for approval')

    def approve(self, approved_by: str) -> None:
        """Approve post for publishing"""
        self.status = PostStatus.APPROVED
        self.approved_by = approved_by
        self.approved_at = datetime.now()
        self.add_audit_entry('approved', approved_by, 'Post approved for publishing')

    def reject(self, rejected_by: str, reason: str) -> None:
        """Reject post"""
        self.status = PostStatus.REJECTED
        self.error_message = reason
        self.add_audit_entry('rejected', rejected_by, f'Post rejected: {reason}')

    def mark_published(self, published_url: str) -> None:
        """Mark post as published"""
        self.status = PostStatus.PUBLISHED
        self.published_at = datetime.now()
        self.published_url = published_url
        self.add_audit_entry('published', 'system', f'Post published: {published_url}')

    def mark_failed(self, error_message: str) -> None:
        """Mark post as failed"""
        self.status = PostStatus.FAILED
        self.error_message = error_message
        self.add_audit_entry('failed', 'system', f'Publishing failed: {error_message}')

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'post_id': self.post_id,
            'platform': self.platform.value,
            'content': self.content,
            'image_path': self.image_path,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'approved_by': self.approved_by,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'published_url': self.published_url,
            'error_message': self.error_message,
            'scheduled_time': self.scheduled_time.isoformat() if self.scheduled_time else None,
            'tags': self.tags,
            'mentions': self.mentions,
            'audit_trail': self.audit_trail
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SocialMediaPost':
        """Create from dictionary"""
        return cls(
            post_id=data['post_id'],
            platform=PostPlatform(data['platform']),
            content=data['content'],
            image_path=data.get('image_path'),
            status=PostStatus(data.get('status', 'draft')),
            created_at=datetime.fromisoformat(data['created_at']),
            approved_by=data.get('approved_by'),
            approved_at=datetime.fromisoformat(data['approved_at']) if data.get('approved_at') else None,
            published_at=datetime.fromisoformat(data['published_at']) if data.get('published_at') else None,
            published_url=data.get('published_url'),
            error_message=data.get('error_message'),
            scheduled_time=datetime.fromisoformat(data['scheduled_time']) if data.get('scheduled_time') else None,
            tags=data.get('tags', []),
            mentions=data.get('mentions', []),
            audit_trail=data.get('audit_trail', [])
        )

    @classmethod
    def from_task_file(cls, frontmatter: Dict[str, Any], body: str) -> 'SocialMediaPost':
        """
        Create SocialMediaPost from task file

        Args:
            frontmatter: YAML frontmatter from task file
            body: Task file body content

        Returns:
            SocialMediaPost instance
        """
        post_id = frontmatter.get('post_id', f"post_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        platform = PostPlatform(frontmatter.get('platform', 'facebook'))
        content = frontmatter.get('content', '')

        # If content not in frontmatter, extract from body
        if not content:
            # Look for content in body (after frontmatter)
            lines = body.strip().split('\n')
            content_lines = []
            in_content = False

            for line in lines:
                if (line.strip().startswith('## Content') or
                    line.strip().startswith('## Post Content') or
                    line.strip().startswith('**Content:**')):
                    in_content = True
                    continue
                if in_content and line.strip() and not line.startswith('#'):
                    content_lines.append(line.strip())
                elif in_content and line.startswith('#'):
                    break

            content = '\n'.join(content_lines)

        return cls(
            post_id=post_id,
            platform=platform,
            content=content,
            image_path=frontmatter.get('image_path'),
            scheduled_time=datetime.fromisoformat(frontmatter['scheduled_time']) if frontmatter.get('scheduled_time') else None,
            tags=frontmatter.get('tags', []),
            mentions=frontmatter.get('mentions', [])
        )


def validate_post(post: SocialMediaPost) -> tuple[bool, Optional[str]]:
    """
    Validate social media post data

    Args:
        post: SocialMediaPost to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    from src.utils.security_utils import validate_description

    # Validate content
    if not post.content or not post.content.strip():
        return False, "Post content is required"

    is_valid, error_msg, _ = validate_description(post.content, 'content')
    if not is_valid:
        return False, error_msg

    # Instagram requires image
    if post.platform == PostPlatform.INSTAGRAM and not post.image_path:
        return False, "Instagram posts require an image"

    # Check content length limits
    if post.platform == PostPlatform.FACEBOOK and len(post.content) > 63206:
        return False, "Facebook post content exceeds maximum length (63,206 characters)"

    if post.platform == PostPlatform.INSTAGRAM and len(post.content) > 2200:
        return False, "Instagram post content exceeds maximum length (2,200 characters)"

    return True, None

"""
Social Media Engagement Entity
Represents engagement activity (comments, reactions, messages) on social media
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class EngagementPlatform(Enum):
    """Social media platform enumeration"""
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"


class EngagementType(Enum):
    """Type of engagement"""
    COMMENT = "comment"
    REACTION = "reaction"
    MESSAGE = "message"
    SHARE = "share"
    MENTION = "mention"
    REPLY = "reply"


class EngagementStatus(Enum):
    """Engagement processing status"""
    NEW = "new"
    REVIEWED = "reviewed"
    RESPONDED = "responded"
    IGNORED = "ignored"


@dataclass
class SocialMediaEngagement:
    """
    Represents engagement activity on social media posts

    Used to track comments, reactions, messages, and other interactions
    that may require response or monitoring
    """
    engagement_id: str
    platform: EngagementPlatform
    engagement_type: EngagementType
    status: EngagementStatus = EngagementStatus.NEW

    # Engagement details
    from_user: str = ""  # Username/name of person who engaged
    from_user_id: Optional[str] = None  # Platform user ID
    content: str = ""  # Comment text, message content, etc.
    post_id: Optional[str] = None  # Related post ID (if applicable)
    post_url: Optional[str] = None  # URL to the post

    # Timestamps
    engagement_time: datetime = field(default_factory=datetime.now)
    detected_at: datetime = field(default_factory=datetime.now)
    responded_at: Optional[datetime] = None

    # Response tracking
    response_content: Optional[str] = None
    response_by: Optional[str] = None

    # Metadata
    is_urgent: bool = False  # Flagged for urgent response
    sentiment: Optional[str] = None  # positive, negative, neutral
    requires_action: bool = False  # Needs human review/response

    # Context
    context: Dict[str, Any] = field(default_factory=dict)

    def mark_reviewed(self) -> None:
        """Mark engagement as reviewed"""
        self.status = EngagementStatus.REVIEWED

    def mark_responded(self, response_content: str, response_by: str) -> None:
        """Mark engagement as responded to"""
        self.status = EngagementStatus.RESPONDED
        self.response_content = response_content
        self.response_by = response_by
        self.responded_at = datetime.now()

    def mark_ignored(self) -> None:
        """Mark engagement as ignored (no response needed)"""
        self.status = EngagementStatus.IGNORED

    def flag_urgent(self, reason: str = "") -> None:
        """Flag engagement as urgent"""
        self.is_urgent = True
        if reason:
            self.context['urgent_reason'] = reason

    def set_sentiment(self, sentiment: str) -> None:
        """Set sentiment analysis result"""
        if sentiment.lower() in ['positive', 'negative', 'neutral']:
            self.sentiment = sentiment.lower()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'engagement_id': self.engagement_id,
            'platform': self.platform.value,
            'engagement_type': self.engagement_type.value,
            'status': self.status.value,
            'from_user': self.from_user,
            'from_user_id': self.from_user_id,
            'content': self.content,
            'post_id': self.post_id,
            'post_url': self.post_url,
            'engagement_time': self.engagement_time.isoformat(),
            'detected_at': self.detected_at.isoformat(),
            'responded_at': self.responded_at.isoformat() if self.responded_at else None,
            'response_content': self.response_content,
            'response_by': self.response_by,
            'is_urgent': self.is_urgent,
            'sentiment': self.sentiment,
            'requires_action': self.requires_action,
            'context': self.context
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SocialMediaEngagement':
        """Create from dictionary"""
        return cls(
            engagement_id=data['engagement_id'],
            platform=EngagementPlatform(data['platform']),
            engagement_type=EngagementType(data['engagement_type']),
            status=EngagementStatus(data.get('status', 'new')),
            from_user=data.get('from_user', ''),
            from_user_id=data.get('from_user_id'),
            content=data.get('content', ''),
            post_id=data.get('post_id'),
            post_url=data.get('post_url'),
            engagement_time=datetime.fromisoformat(data['engagement_time']),
            detected_at=datetime.fromisoformat(data['detected_at']),
            responded_at=datetime.fromisoformat(data['responded_at']) if data.get('responded_at') else None,
            response_content=data.get('response_content'),
            response_by=data.get('response_by'),
            is_urgent=data.get('is_urgent', False),
            sentiment=data.get('sentiment'),
            requires_action=data.get('requires_action', False),
            context=data.get('context', {})
        )

    @classmethod
    def from_facebook_comment(
        cls,
        comment_id: str,
        from_user: str,
        content: str,
        post_id: Optional[str] = None,
        post_url: Optional[str] = None
    ) -> 'SocialMediaEngagement':
        """
        Create engagement from Facebook comment

        Args:
            comment_id: Facebook comment ID
            from_user: Username of commenter
            content: Comment text
            post_id: Related post ID
            post_url: URL to the post

        Returns:
            SocialMediaEngagement instance
        """
        return cls(
            engagement_id=f"fb_comment_{comment_id}",
            platform=EngagementPlatform.FACEBOOK,
            engagement_type=EngagementType.COMMENT,
            from_user=from_user,
            content=content,
            post_id=post_id,
            post_url=post_url
        )

    @classmethod
    def from_instagram_comment(
        cls,
        comment_id: str,
        from_user: str,
        content: str,
        post_id: Optional[str] = None,
        post_url: Optional[str] = None
    ) -> 'SocialMediaEngagement':
        """
        Create engagement from Instagram comment

        Args:
            comment_id: Instagram comment ID
            from_user: Username of commenter
            content: Comment text
            post_id: Related post ID
            post_url: URL to the post

        Returns:
            SocialMediaEngagement instance
        """
        return cls(
            engagement_id=f"ig_comment_{comment_id}",
            platform=EngagementPlatform.INSTAGRAM,
            engagement_type=EngagementType.COMMENT,
            from_user=from_user,
            content=content,
            post_id=post_id,
            post_url=post_url
        )

    @classmethod
    def from_facebook_message(
        cls,
        message_id: str,
        from_user: str,
        content: str
    ) -> 'SocialMediaEngagement':
        """
        Create engagement from Facebook message

        Args:
            message_id: Facebook message ID
            from_user: Username of sender
            content: Message text

        Returns:
            SocialMediaEngagement instance
        """
        return cls(
            engagement_id=f"fb_message_{message_id}",
            platform=EngagementPlatform.FACEBOOK,
            engagement_type=EngagementType.MESSAGE,
            from_user=from_user,
            content=content
        )

    @classmethod
    def from_instagram_dm(
        cls,
        message_id: str,
        from_user: str,
        content: str
    ) -> 'SocialMediaEngagement':
        """
        Create engagement from Instagram DM

        Args:
            message_id: Instagram message ID
            from_user: Username of sender
            content: Message text

        Returns:
            SocialMediaEngagement instance
        """
        return cls(
            engagement_id=f"ig_dm_{message_id}",
            platform=EngagementPlatform.INSTAGRAM,
            engagement_type=EngagementType.MESSAGE,
            from_user=from_user,
            content=content
        )


def analyze_engagement_urgency(engagement: SocialMediaEngagement) -> bool:
    """
    Analyze if engagement requires urgent attention

    Args:
        engagement: SocialMediaEngagement to analyze

    Returns:
        True if urgent, False otherwise
    """
    # Keywords that indicate urgency
    urgent_keywords = [
        'urgent', 'asap', 'immediately', 'emergency', 'help',
        'problem', 'issue', 'broken', 'not working', 'error',
        'complaint', 'refund', 'cancel', 'angry', 'disappointed'
    ]

    content_lower = engagement.content.lower()

    # Check for urgent keywords
    for keyword in urgent_keywords:
        if keyword in content_lower:
            engagement.flag_urgent(f"Contains urgent keyword: {keyword}")
            return True

    # Messages are generally more urgent than comments
    if engagement.engagement_type == EngagementType.MESSAGE:
        engagement.requires_action = True

    return False


def detect_sentiment(engagement: SocialMediaEngagement) -> str:
    """
    Simple sentiment detection for engagement

    Args:
        engagement: SocialMediaEngagement to analyze

    Returns:
        Sentiment: 'positive', 'negative', or 'neutral'
    """
    content_lower = engagement.content.lower()

    # Positive indicators
    positive_words = [
        'great', 'awesome', 'excellent', 'love', 'amazing',
        'wonderful', 'fantastic', 'perfect', 'thank', 'thanks'
    ]

    # Negative indicators
    negative_words = [
        'bad', 'terrible', 'awful', 'hate', 'worst',
        'disappointed', 'angry', 'frustrated', 'problem', 'issue'
    ]

    positive_count = sum(1 for word in positive_words if word in content_lower)
    negative_count = sum(1 for word in negative_words if word in content_lower)

    if positive_count > negative_count:
        sentiment = 'positive'
    elif negative_count > positive_count:
        sentiment = 'negative'
    else:
        sentiment = 'neutral'

    engagement.set_sentiment(sentiment)
    return sentiment

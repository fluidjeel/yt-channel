"""Data models for comment intelligence analysis."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


EMOTIONAL_STATES = [
    "hope",
    "loneliness",
    "heartbreak",
    "healing",
    "validation",
    "motivation",
    "acceptance",
    "gratitude",
    "anger",
    "nostalgia",
    "self-worth",
    "longing",
]

LIFE_SITUATIONS = [
    "breakup",
    "toxic_relationship",
    "unrequited_love",
    "self_esteem",
    "family_conflict",
    "loneliness",
    "healing_journey",
    "career_stress",
    "friendship",
    "personal_growth",
    "spiritual_search",
    "identity",
]

COMMENT_THEMES = [
    "relatability",
    "self_love",
    "letting_go",
    "moving_on",
    "validation",
    "motivation",
    "heartbreak",
    "wisdom",
    "gratitude",
    "sharing_with_others",
    "saving_for_later",
    "creator_praise",
]


@dataclass
class RawComment:
    comment_id: str
    video_id: str
    text: str
    like_count: int
    author: str
    parent_id: str = ""
    channel: str = ""

    def to_row(self) -> dict[str, Any]:
        return {
            "comment_id": self.comment_id,
            "video_id": self.video_id,
            "channel": self.channel,
            "text": self.text,
            "like_count": self.like_count,
            "author": self.author,
            "parent_id": self.parent_id,
        }


@dataclass
class AnalyzedComment:
    comment_id: str
    video_id: str
    channel: str
    video_title: str
    video_rank: int
    video_views_per_day: float
    text: str
    like_count: int
    author: str
    is_spam: bool
    cluster_id: int
    theme: str
    emotional_state: str
    life_situation: str
    save_signal: bool
    share_signal: bool
    pain_point_score: float
    confidence: float

    def to_row(self) -> dict[str, Any]:
        return {
            "comment_id": self.comment_id,
            "video_id": self.video_id,
            "channel": self.channel,
            "video_title": self.video_title,
            "video_rank": self.video_rank,
            "video_views_per_day": round(self.video_views_per_day, 2),
            "text": self.text,
            "like_count": self.like_count,
            "author": self.author,
            "is_spam": self.is_spam,
            "cluster_id": self.cluster_id,
            "theme": self.theme,
            "emotional_state": self.emotional_state,
            "life_situation": self.life_situation,
            "save_signal": self.save_signal,
            "share_signal": self.share_signal,
            "pain_point_score": round(self.pain_point_score, 4),
            "confidence": round(self.confidence, 4),
        }


@dataclass
class CommentCluster:
    cluster_id: int
    channel: str
    theme: str
    emotional_state: str
    life_situation: str
    comment_count: int
    video_count: int
    avg_likes: float
    save_signal_pct: float
    share_signal_pct: float
    confidence: float
    example_comments: list[str] = field(default_factory=list)
    evidence_comment_ids: list[str] = field(default_factory=list)
    avg_video_views_per_day: float = 0.0
    top_phrases: list[str] = field(default_factory=list)

    def to_row(self) -> dict[str, Any]:
        return {
            "cluster_id": self.cluster_id,
            "channel": self.channel,
            "theme": self.theme,
            "emotional_state": self.emotional_state,
            "life_situation": self.life_situation,
            "comment_count": self.comment_count,
            "video_count": self.video_count,
            "avg_likes": round(self.avg_likes, 2),
            "save_signal_pct": round(self.save_signal_pct, 2),
            "share_signal_pct": round(self.share_signal_pct, 2),
            "confidence": round(self.confidence, 4),
            "avg_video_views_per_day": round(self.avg_video_views_per_day, 2),
            "example_comments": " || ".join(self.example_comments[:3]),
            "evidence_comment_ids": "|".join(self.evidence_comment_ids[:10]),
            "top_phrases": "|".join(self.top_phrases[:5]),
        }

"""Data models for Market Intelligence."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ChannelCategory(str, Enum):
    DIRECT_COMPETITOR = "DIRECT_COMPETITOR"
    ADJACENT_COMPETITOR = "ADJACENT_COMPETITOR"
    EMERGING_CHANNEL = "EMERGING_CHANNEL"
    OUTLIER_WINNER = "OUTLIER_WINNER"


@dataclass
class ChannelMetadata:
    channel_id: str
    channel_name: str
    channel_url: str
    subscriber_count: int = 0
    video_count: int = 0
    total_views: int = 0
    description: str = ""
    niche_category: str = ""
    discovery_source: str = ""
    top_titles: list[str] = field(default_factory=list)
    themes: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    def to_row(self) -> dict[str, Any]:
        return {
            "channel_name": self.channel_name,
            "channel_url": self.channel_url,
            "subscriber_count": self.subscriber_count,
            "video_count": self.video_count,
            "total_views": self.total_views,
            "niche_category": self.niche_category,
            "discovery_source": self.discovery_source,
        }


@dataclass
class ChannelProfile:
    """Textual profile used for similarity scoring."""

    channel_url: str
    channel_name: str
    titles_text: str = ""
    descriptions_text: str = ""
    transcript_text: str = ""
    emotional_vector: list[float] = field(default_factory=list)
    visual_themes: list[str] = field(default_factory=list)
    narrative_style: str = ""
    subscriber_count: int = 0
    video_count: int = 0
    total_views: int = 0
    avg_views_per_video: float = 0.0


@dataclass
class SimilarityResult:
    seed_channel: str
    candidate_channel: str
    similarity_score: float
    emotional_similarity: float
    visual_similarity: float
    narrative_similarity: float

    def to_row(self) -> dict[str, Any]:
        return {
            "seed_channel": self.seed_channel,
            "candidate_channel": self.candidate_channel,
            "similarity_score": round(self.similarity_score, 4),
            "emotional_similarity": round(self.emotional_similarity, 4),
            "visual_similarity": round(self.visual_similarity, 4),
            "narrative_similarity": round(self.narrative_similarity, 4),
        }


@dataclass
class OpportunityScore:
    theme: str
    competition_score: float
    demand_score: float
    growth_score: float
    composite_score: float

    def to_row(self) -> dict[str, Any]:
        return {
            "theme": self.theme,
            "competition_score": round(self.competition_score, 4),
            "demand_score": round(self.demand_score, 4),
            "growth_score": round(self.growth_score, 4),
            "composite_score": round(self.composite_score, 4),
        }

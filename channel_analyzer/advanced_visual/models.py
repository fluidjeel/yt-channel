"""Data models for advanced visual analysis."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


CHARACTER_ARCHETYPES = [
    "solitary_male",
    "solitary_female",
    "couple",
    "traveler",
    "dreamer",
    "observer",
    "no_character",
]

GAZE_TYPES = [
    "looking_away",
    "looking_down",
    "looking_up",
    "side_profile",
    "back_profile",
    "direct_gaze",
    "no_face",
]

EMOTIONAL_EXPRESSIONS = [
    "hopeful",
    "reflective",
    "longing",
    "peaceful_sadness",
    "resilience",
    "acceptance",
    "wonder",
]

COMPOSITION_TYPES = [
    "tiny_human_large_world",
    "centered_subject",
    "edge_subject",
    "full_frame_subject",
]

SYMBOLISM_TAGS = [
    "moon",
    "rain",
    "ocean",
    "clouds",
    "sunset",
    "stars",
    "road",
    "window",
    "birds",
]

RELATIONSHIP_TYPES = [
    "alone",
    "couple",
    "separated_couple",
    "walking_together",
    "looking_at_each_other",
    "ambiguous",
]


@dataclass
class FrameAnalysis:
    video_id: str
    frame_path: str
    timestamp_sec: float
    character_archetype: str
    character_confidence: float
    gaze: str
    gaze_confidence: float
    expression: str
    expression_confidence: float
    composition: str
    composition_confidence: float
    negative_space_pct: float
    subject_scale_pct: float
    symbolism: list[str]
    relationship: str
    relationship_confidence: float
    anime_style_score: float
    face_count: int
    method: str = "clip+heuristic"

    def to_row(self) -> dict[str, Any]:
        return {
            "video_id": self.video_id,
            "frame_path": self.frame_path,
            "timestamp_sec": round(self.timestamp_sec, 2),
            "character_archetype": self.character_archetype,
            "character_confidence": round(self.character_confidence, 4),
            "gaze": self.gaze,
            "gaze_confidence": round(self.gaze_confidence, 4),
            "expression": self.expression,
            "expression_confidence": round(self.expression_confidence, 4),
            "composition": self.composition,
            "composition_confidence": round(self.composition_confidence, 4),
            "negative_space_pct": round(self.negative_space_pct, 2),
            "subject_scale_pct": round(self.subject_scale_pct, 2),
            "symbolism": "|".join(self.symbolism),
            "relationship": self.relationship,
            "relationship_confidence": round(self.relationship_confidence, 4),
            "anime_style_score": round(self.anime_style_score, 4),
            "face_count": self.face_count,
            "method": self.method,
        }


@dataclass
class VideoVisualProfile:
    video_id: str
    title: str = ""
    views: int = 0
    views_per_day: float = 0.0
    rank: int = 0
    frames_analyzed: int = 0
    dominant_archetype: str = ""
    dominant_gaze: str = ""
    dominant_expression: str = ""
    dominant_composition: str = ""
    dominant_relationship: str = ""
    avg_negative_space_pct: float = 0.0
    avg_subject_scale_pct: float = 0.0
    avg_anime_style_score: float = 0.0
    symbolism_frequency: dict[str, int] = field(default_factory=dict)
    archetype_scores: dict[str, float] = field(default_factory=dict)
    expression_scores: dict[str, float] = field(default_factory=dict)

    def to_row(self) -> dict[str, Any]:
        return {
            "video_id": self.video_id,
            "title": self.title,
            "views": self.views,
            "views_per_day": round(self.views_per_day, 2),
            "rank": self.rank,
            "frames_analyzed": self.frames_analyzed,
            "dominant_archetype": self.dominant_archetype,
            "dominant_gaze": self.dominant_gaze,
            "dominant_expression": self.dominant_expression,
            "dominant_composition": self.dominant_composition,
            "dominant_relationship": self.dominant_relationship,
            "avg_negative_space_pct": round(self.avg_negative_space_pct, 2),
            "avg_subject_scale_pct": round(self.avg_subject_scale_pct, 2),
            "avg_anime_style_score": round(self.avg_anime_style_score, 4),
            "top_symbolism": "|".join(
                k for k, _ in sorted(
                    self.symbolism_frequency.items(), key=lambda x: -x[1]
                )[:5]
            ),
        }

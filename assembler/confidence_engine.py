"""Confidence scoring for MVP assembler — rules from docs/MVP_SCORING.md."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

Confidence = Literal["HIGH", "MEDIUM", "LOW", "N/A"]

VALIDATED_COMMENT_CHANNELS = frozenset({"whisprs_yt", "soulxsigh"})
COMMENT_HIGH_THRESHOLD = 300

EvidenceType = Literal[
    "comment",
    "visual",
    "narrative",
    "performance",
    "bible",
    "cross_channel",
]


@dataclass
class EvidenceField:
    """Every emitted field wraps value + confidence + source."""

    value: Any
    confidence: Confidence
    source: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "value": self.value,
            "confidence": self.confidence,
            "source": self.source,
        }
        return out


def empty_field(confidence: Confidence = "N/A") -> EvidenceField:
    return EvidenceField(value=None, confidence=confidence, source=[])


def field(
    value: Any,
    *,
    confidence: Confidence,
    source: list[str],
) -> EvidenceField:
    return EvidenceField(value=value, confidence=confidence, source=source)


def combine_confidence(*levels: Confidence) -> Confidence:
    order = {"N/A": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3}
    if not levels:
        return "LOW"
    return min(levels, key=lambda c: order.get(c, 0))


def comment_confidence(cleaned_count: int, slug: str) -> Confidence:
    if cleaned_count >= COMMENT_HIGH_THRESHOLD and slug in VALIDATED_COMMENT_CHANNELS:
        return "HIGH"
    if cleaned_count >= COMMENT_HIGH_THRESHOLD:
        return "MEDIUM"
    if cleaned_count > 0:
        return "LOW"
    return "N/A"


def score_from_evidence_types(
    types: set[EvidenceType],
    *,
    cleaned_comment_count: int = 0,
    slug: str = "",
) -> Confidence:
    has_comments = "comment" in types and cleaned_comment_count > 0
    cc = comment_confidence(cleaned_comment_count, slug) if has_comments else "N/A"

    if has_comments and cc in ("HIGH", "MEDIUM") and len(types) >= 3:
        return "HIGH" if cc == "HIGH" else "MEDIUM"
    if has_comments and len(types) >= 2:
        return combine_confidence(cc, "MEDIUM")
    if len(types) >= 2:
        return "MEDIUM"
    if len(types) == 1:
        return "LOW"
    return "N/A"

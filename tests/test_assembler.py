"""Tests for MVP assembler (evidence wrapper + smoke assembly)."""

from __future__ import annotations

from pathlib import Path

import pytest

from assembler.confidence_engine import (
    EvidenceField,
    combine_confidence,
    comment_confidence,
    field,
)
from assembler.assemble import assemble_mvp_profile

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_evidence_field_shape() -> None:
    ef = field("heartbreak", confidence="HIGH", source=["audience_psychology"])
    d = ef.to_dict()
    assert set(d) == {"value", "confidence", "source"}
    assert d["value"] == "heartbreak"
    assert d["confidence"] == "HIGH"
    assert d["source"] == ["audience_psychology"]


def test_combine_confidence_takes_minimum() -> None:
    assert combine_confidence("HIGH", "LOW", "MEDIUM") == "LOW"


def test_comment_confidence_tiers() -> None:
    assert comment_confidence(500, "whisprs_yt") == "HIGH"
    assert comment_confidence(500, "unknown_channel") == "MEDIUM"
    assert comment_confidence(10, "whisprs_yt") == "LOW"
    assert comment_confidence(0, "whisprs_yt") == "N/A"


@pytest.mark.skipif(
    not (PROJECT_ROOT / "reports" / "whisprs_yt" / "audience_psychology.md").exists(),
    reason="benchmark reports not present",
)
def test_assemble_whisprs_smoke() -> None:
    profile = assemble_mvp_profile("whisprs_yt")
    assert profile["channel_slug"] == "whisprs_yt"
    dom = profile["outcome_profile"]["dominant_emotional_outcome"]
    assert "value" in dom and "confidence" in dom and "source" in dom
    recs = profile["content_recommendations"]["items"]
    for item in recs:
        assert item["category"] in ("content_gaps", "viral_patterns", "performance_correlations")
        assert "recommendation" in item
        assert set(item["recommendation"]) == {"value", "confidence", "source"}

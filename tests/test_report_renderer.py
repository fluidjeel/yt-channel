"""Tests for MVP report renderer (markdown from JSON, no LLM)."""

from __future__ import annotations

from pathlib import Path

import pytest

from assembler.report_renderer import render_channel_report, write_channel_report
from assembler.slug import resolve_channel_slug

PROJECT_ROOT = Path(__file__).resolve().parent.parent

MINIMAL_PROFILE = {
    "channel_slug": "test_channel",
    "channel_name": "Test Channel",
    "channel_url": "https://www.youtube.com/@TestChannel",
    "analyzed_at": "2026-06-27T00:00:00+00:00",
    "pipeline_status": "full",
    "outcome_profile": {
        "dominant_emotional_outcome": {
            "value": "acceptance",
            "confidence": "HIGH",
            "source": ["reports/test_channel/content_dna.md"],
        },
        "secondary_outcomes": {
            "value": ["hope", "self-worth"],
            "confidence": "MEDIUM",
            "source": [],
        },
        "emotional_journey": {
            "arrival_state": {"value": "heartbreak", "confidence": "HIGH", "source": []},
            "transformation_stages": {
                "value": ["Hook", "Resolution"],
                "confidence": "MEDIUM",
                "source": [],
            },
            "desired_state": {"value": "acceptance", "confidence": "LOW", "source": []},
        },
        "audience_emotional_need": {
            "primary_need": {"value": "validation", "confidence": "HIGH", "source": []},
            "save_signals": {"value": ["needed this"], "confidence": "HIGH", "source": []},
            "share_signals": {"value": [], "confidence": "N/A", "source": []},
        },
    },
    "brand_profile": {
        "visual_identity": {
            "style_summary": {"value": ["minimal palette"], "confidence": "MEDIUM", "source": []},
            "dominant_motifs": {"value": [], "confidence": "N/A", "source": []},
        },
        "narrative_identity": {
            "structure_template": {
                "value": ["Hook", "Reflection"],
                "confidence": "MEDIUM",
                "source": [],
            },
            "voice_tone": {"value": ["gentle"], "confidence": "LOW", "source": []},
        },
        "production_signature": {
            "pacing_cadence": {"value": None, "confidence": "N/A", "source": []},
            "music_mood": {"value": None, "confidence": "N/A", "source": []},
        },
        "profile_confidence": {"value": "MEDIUM", "confidence": "MEDIUM", "source": ["assembler"]},
    },
    "content_recommendations": {
        "items": [
            {
                "category": "content_gaps",
                "recommendation": {
                    "value": "Try more gratitude themes",
                    "confidence": "LOW",
                    "source": [],
                },
            },
            {
                "category": "performance_correlations",
                "recommendation": {
                    "value": "High negative space correlates with top videos",
                    "confidence": "MEDIUM",
                    "source": [],
                },
            },
            {
                "category": "viral_patterns",
                "recommendation": {
                    "value": "Self-love quotes outperform revenge framing",
                    "confidence": "LOW",
                    "source": [],
                },
            },
        ],
        "evidence_tier": {"value": "MEDIUM", "confidence": "MEDIUM", "source": ["assembler"]},
    },
}


def test_render_includes_all_sections() -> None:
    md = render_channel_report("test_channel", profile=MINIMAL_PROFILE)
    for heading in (
        "## 1. Audience Outcome Profile",
        "## 2. Brand Identity Profile",
        "## 3. Content Opportunities",
        "## 4. Evidence Confidence",
        "## 5. Top Performing Patterns",
        "## 6. Recommended Experiments",
    ):
        assert heading in md


def test_render_shows_confidence_badges() -> None:
    md = render_channel_report("test_channel", profile=MINIMAL_PROFILE)
    assert "**Confidence:** `HIGH`" in md
    assert "**Confidence:** `MEDIUM`" in md
    assert "acceptance" in md
    assert "Try more gratitude themes" in md
    assert "High negative space" in md
    assert "Self-love quotes" in md


def test_render_no_inference_footer() -> None:
    md = render_channel_report("test_channel", profile=MINIMAL_PROFILE)
    assert "no inference or LLM" in md


def test_resolve_slug_from_benchmark_url() -> None:
    slug = resolve_channel_slug("https://www.youtube.com/@WhisprsYT/shorts")
    assert slug == "whisprs_yt"


def test_resolve_slug_from_handle() -> None:
    slug = resolve_channel_slug("https://www.youtube.com/@SomeNewCreator")
    assert slug == "some_new_creator"


@pytest.mark.skipif(
    not (PROJECT_ROOT / "reports" / "whisprs_yt" / "mvp_profile.json").exists(),
    reason="whisprs_yt MVP profile not present",
)
def test_write_whisprs_report_smoke(tmp_path: Path) -> None:
    out = write_channel_report("whisprs_yt", output_path=tmp_path / "report.md")
    text = out.read_text(encoding="utf-8")
    assert out.exists()
    assert "Channel Intelligence Report" in text
    assert "## 1. Audience Outcome Profile" in text

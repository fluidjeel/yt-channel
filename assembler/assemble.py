"""Orchestrate MVP profile assembly from existing pipeline artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from channel_analyzer.utils import save_json

from assembler.brand_profile_assembler import assemble_brand_profile
from assembler.helpers import (
    analyzed_at,
    channel_name,
    list_source_reports,
    pipeline_status,
    reports_dir,
)
from assembler.outcome_profile_assembler import assemble_outcome_profile
from assembler.recommendations_assembler import assemble_recommendations


def assemble_mvp_profile(
    slug: str,
    *,
    channel_url: str | None = None,
) -> dict[str, Any]:
    """Build full MVP JSON from reports/{slug}/ and data/channels/{slug}/."""
    if not reports_dir(slug).exists():
        raise FileNotFoundError(f"No reports directory for slug: {slug}")

    profile: dict[str, Any] = {
        "channel_url": channel_url,
        "channel_slug": slug,
        "channel_name": channel_name(slug),
        "analyzed_at": analyzed_at(slug),
        "pipeline_status": pipeline_status(slug),
        "metadata": {
            "source_reports": list_source_reports(slug),
            "benchmark_cohort": [
                "whisprs_yt",
                "soulful_lines",
                "soulxsigh",
                "dark_poetry_hub",
                "the_faceless_storyteller",
            ],
            "assembler_version": "1.0.0",
            "field_schema": "value + confidence + source",
        },
        "outcome_profile": assemble_outcome_profile(slug),
        "brand_profile": assemble_brand_profile(slug),
        "content_recommendations": assemble_recommendations(slug),
    }
    return profile


def write_mvp_profile(
    slug: str,
    *,
    channel_url: str | None = None,
    output_path: Path | None = None,
) -> Path:
    profile = assemble_mvp_profile(slug, channel_url=channel_url)
    out = output_path or (reports_dir(slug) / "mvp_profile.json")
    save_json(out, profile)
    return out

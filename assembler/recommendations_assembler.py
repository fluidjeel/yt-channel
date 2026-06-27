"""Recommendations assembler — allowlisted sections only (observed evidence)."""

from __future__ import annotations

from typing import Any

from assembler.confidence_engine import EvidenceField, comment_confidence, field
from assembler.helpers import (
    cleaned_comment_count,
    parse_bible_gaps,
    parse_channel_unique_signals,
    parse_cohort_niche_patterns,
    parse_performance_correlations,
    parse_playbook_gaps,
    parse_playbook_viral_patterns,
    report_path,
)

ALLOWLISTED_CATEGORIES = frozenset({
    "content_gaps",
    "viral_patterns",
    "performance_correlations",
})


def _rec_item(
    category: str,
    text: str,
    *,
    confidence: str,
    source: list[str],
) -> dict[str, Any]:
    return {
        "category": category,
        "recommendation": field(text, confidence=confidence, source=source).to_dict(),
    }


def assemble_recommendations(slug: str) -> dict[str, Any]:
    cc = cleaned_comment_count(slug)
    items: list[dict[str, Any]] = []

    gaps = parse_playbook_gaps(slug)
    gap_src = [report_path(slug, "channel_playbook.md")]
    gap_conf = "MEDIUM" if gaps else "N/A"
    for g in gaps:
        items.append(_rec_item("content_gaps", g, confidence=gap_conf, source=gap_src))

    viral = parse_playbook_viral_patterns(slug)
    viral_src = [report_path(slug, "channel_playbook.md")]
    viral_conf = "MEDIUM" if viral else "N/A"
    for v in viral:
        items.append(_rec_item("viral_patterns", v, confidence=viral_conf, source=viral_src))

    perf = parse_performance_correlations(slug)
    perf_src = [report_path(slug, "advanced_visual_analysis.md")]
    perf_conf = "MEDIUM" if perf else "LOW"
    for p in perf:
        items.append(_rec_item("performance_correlations", p, confidence=perf_conf, source=perf_src))

    # Cohort context — cross-channel, not channel-specific playbook
    cohort = parse_cohort_niche_patterns()
    if cohort:
        items.append(
            _rec_item(
                "content_gaps",
                f"Cohort pattern (shared): {cohort[0]}",
                confidence="MEDIUM",
                source=["reports/cross_channel_synthesis_v2.md"],
            )
        )

    unique = parse_channel_unique_signals(slug)
    for u in unique[:3]:
        items.append(
            _rec_item(
                "viral_patterns",
                u,
                confidence="LOW",
                source=["reports/validation_phase2.md"],
            )
        )

    bible_gaps = parse_bible_gaps(slug)
    for bg in bible_gaps[:5]:
        items.append(
            _rec_item(
                "content_gaps",
                bg,
                confidence="LOW",
                source=[
                    report_path(slug, "content_dna.md"),
                    report_path(slug, "audience_persona.md"),
                ],
            )
        )

    return {
        "items": items,
        "allowlisted_categories": sorted(ALLOWLISTED_CATEGORIES),
        "evidence_tier": field(
            "HIGH" if cc >= 300 and slug in ("whisprs_yt", "soulxsigh") else (
                "MEDIUM" if cc > 0 or gaps or viral else "LOW"
            ),
            confidence=comment_confidence(cc, slug) if cc else ("MEDIUM" if items else "LOW"),
            source=["assembler/evidence_tier"],
        ).to_dict(),
    }

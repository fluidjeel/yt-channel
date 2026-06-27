"""Outcome Profile assembler — audience emotional outcome from existing artifacts."""

from __future__ import annotations

from typing import Any

from assembler.confidence_engine import (
    EvidenceField,
    combine_confidence,
    comment_confidence,
    empty_field,
    field,
)
from assembler.helpers import (
    cleaned_comment_count,
    comment_theme_counts,
    data_path,
    dominant_from_csv,
    parse_emotional_arc_from_bible,
    parse_emotional_triggers,
    parse_key_insight_first,
    parse_narrative_template,
    parse_save_signals,
    parse_share_signals,
    quote_theme_counts,
    read_report,
    report_path,
)


def _dominant_emotional_outcome(slug: str, cc: int) -> EvidenceField:
    expr = dominant_from_csv(slug, "advanced_visual_videos.csv", "dominant_expression")
    if expr:
        conf = combine_confidence(
            comment_confidence(cc, slug) if cc else "N/A",
            "MEDIUM",
        )
        if cc >= 300:
            conf = "HIGH" if slug in ("whisprs_yt", "soulxsigh") else "MEDIUM"
        return field(
            expr,
            confidence=conf,
            source=[data_path(slug, "advanced_visual_videos.csv")],
        )
    triggers = parse_emotional_triggers(slug, top_n=1)
    if triggers:
        return field(
            triggers[0],
            confidence=comment_confidence(cc, slug) if cc else "LOW",
            source=[report_path(slug, "audience_psychology.md")],
        )
    themes = quote_theme_counts(slug, top_n=1)
    if themes:
        return field(
            themes[0]["theme"],
            confidence="LOW",
            source=[data_path(slug, "quote_database.csv")],
        )
    return empty_field("N/A")


def _secondary_outcomes(slug: str, cc: int) -> EvidenceField:
    items: list[str] = []
    sources: list[str] = []
    for t in parse_emotional_triggers(slug, top_n=4)[1:4]:
        items.append(t)
        sources.append(report_path(slug, "audience_psychology.md"))
    if len(items) < 2:
        for row in quote_theme_counts(slug, top_n=4)[1:4]:
            if row["theme"] not in items:
                items.append(row["theme"])
                sources.append(data_path(slug, "quote_database.csv"))
    conf = comment_confidence(cc, slug) if cc and items else ("MEDIUM" if items else "N/A")
    return field(items[:3], confidence=conf, source=list(dict.fromkeys(sources)))


def _arrival_state(slug: str, cc: int) -> EvidenceField:
    if cc == 0:
        return empty_field("N/A")
    themes = comment_theme_counts(slug, top_n=2)
    if themes:
        label = ", ".join(t["theme"] for t in themes)
        return field(
            label,
            confidence=comment_confidence(cc, slug),
            source=[data_path(slug, "comments.csv")],
        )
    triggers = parse_emotional_triggers(slug, top_n=2)
    if triggers:
        return field(
            ", ".join(triggers),
            confidence="MEDIUM" if cc else "LOW",
            source=[report_path(slug, "audience_psychology.md")],
        )
    return empty_field("LOW")


def _transformation_stages(slug: str) -> EvidenceField:
    emotional = parse_emotional_arc_from_bible(slug)
    if emotional:
        return field(
            emotional,
            confidence="MEDIUM",
            source=[report_path(slug, "master_emotional_bible.md")],
        )
    structural = parse_narrative_template(slug)
    if structural:
        return field(
            structural,
            confidence="MEDIUM",
            source=[report_path(slug, "narrative_patterns.md")],
        )
    return empty_field("LOW")


def _desired_state(slug: str, cc: int) -> EvidenceField:
    triggers = parse_emotional_triggers(slug, top_n=2)
    positive = [t for t in triggers if any(k in t.lower() for k in ("accept", "hope", "gratitude", "self", "growth"))]
    if positive:
        return field(
            ", ".join(positive[:2]),
            confidence=comment_confidence(cc, slug) if cc else "MEDIUM",
            source=[report_path(slug, "audience_psychology.md")],
        )
    md = read_report(slug, "emotion_clusters.md")
    if "Hope" in md or "Acceptance" in md:
        return field(
            "hope / acceptance",
            confidence="LOW",
            source=[report_path(slug, "emotion_clusters.md")],
        )
    return empty_field("N/A")


def _primary_need(slug: str, cc: int) -> EvidenceField:
    insight = parse_key_insight_first(slug)
    if insight:
        return field(
            insight[:300],
            confidence=comment_confidence(cc, slug) if cc else "MEDIUM",
            source=[report_path(slug, "audience_psychology.md")],
        )
    themes = quote_theme_counts(slug, top_n=2)
    if themes:
        label = f"Primary themes: {', '.join(t['theme'] for t in themes)}"
        return field(
            label,
            confidence="LOW",
            source=[data_path(slug, "quote_database.csv")],
        )
    return empty_field("N/A")


def _save_share_signals(slug: str, cc: int) -> tuple[EvidenceField, EvidenceField]:
    saves = parse_save_signals(slug)
    shares = parse_share_signals(slug)
    conf = comment_confidence(cc, slug) if cc else "LOW"
    src = [report_path(slug, "audience_psychology.md")]
    return (
        field(saves, confidence=conf if saves else "N/A", source=src if saves else []),
        field(shares, confidence=conf if shares else "N/A", source=src if shares else []),
    )


def assemble_outcome_profile(slug: str) -> dict[str, Any]:
    cc = cleaned_comment_count(slug)
    save_f, share_f = _save_share_signals(slug, cc)
    return {
        "dominant_emotional_outcome": _dominant_emotional_outcome(slug, cc).to_dict(),
        "secondary_outcomes": _secondary_outcomes(slug, cc).to_dict(),
        "emotional_journey": {
            "arrival_state": _arrival_state(slug, cc).to_dict(),
            "transformation_stages": _transformation_stages(slug).to_dict(),
            "desired_state": _desired_state(slug, cc).to_dict(),
        },
        "audience_emotional_need": {
            "primary_need": _primary_need(slug, cc).to_dict(),
            "save_signals": save_f.to_dict(),
            "share_signals": share_f.to_dict(),
        },
    }

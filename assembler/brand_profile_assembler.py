"""Brand Profile assembler — visual, narrative, and voice from step reports."""

from __future__ import annotations

import re
from typing import Any

from assembler.confidence_engine import EvidenceField, combine_confidence, field
from assembler.helpers import (
    data_path,
    dominant_from_csv,
    mean_from_csv,
    parse_dna_facts,
    parse_narrative_template,
    read_report,
    report_path,
)


def _extract_visual_section(slug: str, heading: str) -> str:
    md = read_report(slug, "advanced_visual_analysis.md")
    return _section_body(md, heading)


def _section_body(md: str, heading: str) -> str:
    pattern = rf"^##\s+{re.escape(heading)}\s*$"
    match = re.search(pattern, md, re.MULTILINE | re.IGNORECASE)
    if not match:
        return ""
    start = match.end()
    nxt = re.search(r"^##\s+", md[start:], re.MULTILINE)
    return md[start : start + nxt.start()] if nxt else md[start:]


def _visual_style_summary(slug: str) -> EvidenceField:
    md = read_report(slug, "advanced_visual_analysis.md")
    if not md:
        return EvidenceField(value=None, confidence="N/A", source=[])
    bullets: list[str] = []
    for heading in ("Composition", "Color Palette", "Lighting", "Emotional Expression"):
        body = _section_body(md, heading)
        for line in body.splitlines():
            if line.strip().startswith("- "):
                bullets.append(line.strip()[2:][:180])
            if len(bullets) >= 5:
                break
        if len(bullets) >= 5:
            break
    if not bullets:
        insight = _section_body(md, "Key Insights")
        bullets = [line.strip()[2:] for line in insight.splitlines() if line.strip().startswith("- ")][:5]
    return field(
        bullets,
        confidence="MEDIUM" if bullets else "N/A",
        source=[report_path(slug, "advanced_visual_analysis.md")],
    )


def _dominant_visual_motifs(slug: str) -> EvidenceField:
    motifs: list[str] = []
    sources: list[str] = []
    for col, label in (
        ("composition_type", "composition_type"),
        ("lighting_type", "lighting_type"),
        ("color_palette", "color_palette"),
    ):
        val = dominant_from_csv(slug, "advanced_visual_videos.csv", col)
        if val:
            motifs.append(f"{label}: {val}")
            sources.append(data_path(slug, "advanced_visual_videos.csv"))
    return field(
        motifs,
        confidence="MEDIUM" if motifs else "N/A",
        source=list(dict.fromkeys(sources)),
    )


def _narrative_structure(slug: str) -> EvidenceField:
    stages = parse_narrative_template(slug)
    if stages:
        return field(
            stages,
            confidence="MEDIUM",
            source=[report_path(slug, "narrative_patterns.md")],
        )
    md = read_report(slug, "narrative_patterns.md")
    hook = re.search(r"Hook type[:\s]*\*\*([^*]+)\*\*", md, re.I)
    if hook:
        return field(
            [hook.group(1).strip()],
            confidence="LOW",
            source=[report_path(slug, "narrative_patterns.md")],
        )
    return EvidenceField(value=None, confidence="N/A", source=[])


def _voice_tone(slug: str) -> EvidenceField:
    facts = parse_dna_facts(slug)
    tone_facts = [f for f in facts if any(k in f.lower() for k in ("voice", "tone", "narration", "quote"))]
    if tone_facts:
        return field(
            tone_facts[:4],
            confidence="MEDIUM",
            source=[report_path(slug, "content_dna.md")],
        )
    md = read_report(slug, "quote_patterns.md")
    themes = re.findall(r"^##\s+(.+)$", md, re.MULTILINE)
    if themes:
        return field(
            themes[:5],
            confidence="LOW",
            source=[report_path(slug, "quote_patterns.md")],
        )
    return EvidenceField(value=None, confidence="N/A", source=[])


def _pacing_cadence(slug: str) -> EvidenceField:
    dur = mean_from_csv(slug, "videos.csv", "duration")
    if dur is not None:
        return field(
            {"mean_duration_seconds": round(dur, 1)},
            confidence="MEDIUM",
            source=[data_path(slug, "videos.csv")],
        )
    return EvidenceField(value=None, confidence="N/A", source=[])


def _music_mood(slug: str) -> EvidenceField:
    md = read_report(slug, "music_analysis.md")
    if not md:
        return EvidenceField(value=None, confidence="N/A", source=[])
    moods: list[str] = []
    for line in md.splitlines():
        if "mood" in line.lower() and line.strip().startswith("- "):
            moods.append(line.strip()[2:])
    conf = "MEDIUM" if moods else "LOW"
    return field(
        moods[:5] if moods else ["music analysis report present; see source report"],
        confidence=conf,
        source=[report_path(slug, "music_analysis.md")],
    )


def assemble_brand_profile(slug: str) -> dict[str, Any]:
    visual = _visual_style_summary(slug)
    motifs = _dominant_visual_motifs(slug)
    narrative = _narrative_structure(slug)
    overall = combine_confidence(
        visual.confidence,
        motifs.confidence,
        narrative.confidence,
    )
    return {
        "visual_identity": {
            "style_summary": visual.to_dict(),
            "dominant_motifs": motifs.to_dict(),
        },
        "narrative_identity": {
            "structure_template": narrative.to_dict(),
            "voice_tone": _voice_tone(slug).to_dict(),
        },
        "production_signature": {
            "pacing_cadence": _pacing_cadence(slug).to_dict(),
            "music_mood": _music_mood(slug).to_dict(),
        },
        "profile_confidence": field(overall, confidence=overall, source=["assembler"]).to_dict(),
    }

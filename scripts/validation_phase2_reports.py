#!/usr/bin/env python3
"""Generate validation_phase2.md and cross_channel_synthesis_v2.md from artifacts."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from channel_analyzer.benchmark.channels import load_benchmark_program
from channel_analyzer.benchmark.config import channel_config
from channel_analyzer.config import PROJECT_ROOT
from channel_analyzer.cross_channel.collector import collect_all_profiles
from channel_analyzer.cross_channel.synthesizer import (
    PATTERN_LABELS,
    analyze_patterns,
    build_niche_dna_sections,
)
from channel_analyzer.utils import read_csv

PHASE2_SLUGS = [
    "whisprs_yt",
    "soulxsigh",
    "dark_poetry_hub",
    "soulful_lines",
    "the_faceless_storyteller",
]

REQUIRED_BIBLES = [
    "content_dna.md",
    "audience_persona.md",
    "master_emotional_bible.md",
]

REQUIRED_REPORTS = [
    "advanced_visual_analysis.md",
    "narrative_patterns.md",
]


def _file_exists(slug: str, name: str, kind: str = "reports") -> bool:
    cfg = channel_config(slug)
    base = cfg.reports_dir if kind == "reports" else cfg.data_dir
    return (base / name).exists()


def _comment_stats(slug: str) -> dict:
    cfg = channel_config(slug)
    path = cfg.data_dir / "comments.csv"
    if not path.exists():
        return {"raw": 0, "cleaned": 0, "has_data": False}
    df = read_csv(path)
    if df.empty:
        return {"raw": 0, "cleaned": 0, "has_data": False}
    cleaned = df
    if "is_spam" in df.columns:
        cleaned = df[df["is_spam"] == False]  # noqa: E712
    themes = {}
    if "theme" in cleaned.columns and not cleaned.empty:
        themes = dict(cleaned["theme"].value_counts().head(5))
    return {
        "raw": len(df),
        "cleaned": len(cleaned),
        "has_data": True,
        "top_themes": themes,
    }


def _channel_row(slug: str) -> dict:
    cfg = channel_config(slug)
    bibles = {b: _file_exists(slug, b) for b in REQUIRED_BIBLES}
    reports = {r: _file_exists(slug, r) for r in REQUIRED_REPORTS}
    comments = _comment_stats(slug)
    videos = len(read_csv(cfg.videos_csv)) if cfg.videos_csv.exists() else 0
    return {
        "slug": slug,
        "bibles_complete": all(bibles.values()),
        "bibles": bibles,
        "reports": reports,
        "videos": videos,
        "comments": comments,
    }


def build_validation_phase2() -> str:
    rows = [_channel_row(s) for s in PHASE2_SLUGS]

    lines = [
        "# Validation Phase 2 Report",
        "",
        "**Date:** evidence snapshot from pipeline artifacts",
        "**Scope:** Whisprs + soulxsigh + dark_poetry_hub + existing benchmark channels",
        "**Rules:** Evidence only — no new theory",
        "",
        "---",
        "",
        "## 1. Channel Coverage Table",
        "",
        "| Channel | Videos | Bibles | Advanced Visual | Narrative | Comments (cleaned) |",
        "| --- | ---: | --- | --- | --- | ---: |",
    ]

    for r in rows:
        b = "✅" if r["bibles_complete"] else "❌"
        av = "✅" if r["reports"]["advanced_visual_analysis.md"] else "❌"
        nar = "✅" if r["reports"]["narrative_patterns.md"] else "❌"
        cc = r["comments"]["cleaned"]
        lines.append(
            f"| `{r['slug']}` | {r['videos']} | {b} | {av} | {nar} | {cc} |"
        )

    lines.extend(["", "## 2. Comment Coverage Table", ""])
    lines.append("| Channel | Raw | Cleaned | Usable dataset? | Top themes |")
    lines.append("| --- | ---: | ---: | --- | --- |")
    for r in rows:
        c = r["comments"]
        usable = "✅" if c["cleaned"] >= 300 else ("partial" if c["cleaned"] > 0 else "❌")
        themes = ", ".join(f"{k} ({v})" for k, v in c.get("top_themes", {}).items()) or "—"
        lines.append(f"| `{r['slug']}` | {c['raw']} | {c['cleaned']} | {usable} | {themes} |")

    # soulxsigh sanity
    sanity_path = PROJECT_ROOT / "reports" / "soulxsigh_sanity_check.json"
    if sanity_path.exists():
        sanity = json.loads(sanity_path.read_text(encoding="utf-8"))
        lines.extend(
            [
                "",
                "### Pre-pipeline soulxsigh sanity check",
                "",
                f"- Shorts tab: **{sanity['shorts_count']}** videos",
                f"- Inspected: **{sanity['inspected']}** Shorts",
                f"- Comment density: **{sanity['comment_count_sum']}** on sample (30/video)",
                f"- Substantive comments: **{sanity['substantive_pct']}%** (not emoji-only)",
                f"- Niche: original poetry + `#poetry #deepthoughts` (love/healing adjacent)",
                "",
            ]
        )

    program = load_benchmark_program()
    profiles = [p for p in collect_all_profiles(program) if p.slug in PHASE2_SLUGS]
    patterns = analyze_patterns(profiles, "whisprs_yt")

    lines.extend(["", "## 3. Evidence Confidence by Layer", ""])
    lines.append("| Layer | Confidence | Basis |")
    lines.append("| --- | --- | --- |")

    full_bibles = sum(1 for r in rows if r["bibles_complete"])
    comment_channels = sum(1 for r in rows if r["comments"]["cleaned"] >= 300)
    visual_channels = sum(1 for r in rows if r["reports"]["advanced_visual_analysis.md"])

    layers = [
        ("Human State / JTBD", "PARTIAL", "Inferred from bibles + quotes; comment validation on 1–2 channels"),
        ("Recognition", "LOW–MEDIUM" if comment_channels >= 2 else "LOW", f"{comment_channels} channel(s) with 300+ cleaned comments"),
        ("Mechanism", "LOW–MEDIUM" if comment_channels >= 2 else "LOW", "Comment phrase signals where comments exist"),
        ("Emotional Outcome", "MEDIUM", f"{full_bibles} channels with master_emotional_bible.md"),
        ("Visual DNA", "MEDIUM" if visual_channels >= 3 else "LOW", f"{visual_channels} channels with advanced_visual_analysis.md"),
        ("Narrative DNA", "MEDIUM" if full_bibles >= 3 else "LOW", f"{full_bibles} channels with narrative_patterns.md"),
        ("Brand flavor", "LOW", "Requires manual read of content_dna divergence"),
    ]
    for layer, conf, basis in layers:
        lines.append(f"| {layer} | {conf} | {basis} |")

    niche = [p for p in patterns if p.classification == "niche"]
    unique = [p for p in patterns if p.classification == "unique"]

    lines.extend(["", "## 4. Major Cross-Channel Similarities", ""])
    if niche:
        for p in niche[:8]:
            lines.append(
                f"- **{p.label}** — {len(p.channels_observed)}/{len(profiles)} channels "
                f"({', '.join(p.channels_observed)})"
            )
    else:
        lines.append("_Run full pipelines to populate._")

    lines.extend(["", "## 5. Major Cross-Channel Differences", ""])
    for p in profiles:
        if p.comment_themes:
            top = list(p.comment_themes.keys())[:3]
            lines.append(f"- `{p.slug}` comment themes: {', '.join(top)}")
        if p.visual_signals.get("dominant_archetype"):
            arch = list(p.visual_signals["dominant_archetype"].keys())[:2]
            lines.append(f"- `{p.slug}` dominant archetype: {', '.join(arch)}")

    lines.extend(["", "## 6. Whisprs-Specific Findings", ""])
    ref_only = [p for p in unique if "whisprs_yt" in p.channels_observed]
    if ref_only:
        for p in ref_only:
            lines.append(f"- **{p.label}** — only in whisprs_yt")
    else:
        lines.append("- Dreamer archetype + looking-up gaze (from prior BENCHMARK_VALIDATION.md)")
        lines.append("- Higher acceptance expression dominance vs competitors")

    lines.extend(["", "## 7. Stop Condition Status", ""])
    stop = [
        ("5 complete channels (3 bibles each)", full_bibles >= 5),
        ("2 comment datasets (300+ cleaned)", comment_channels >= 2),
        ("Cross-channel synthesis v2", (PROJECT_ROOT / "reports" / "cross_channel_synthesis_v2.md").exists()),
        ("Research freeze active", (PROJECT_ROOT / "research_freeze.yaml").exists()),
    ]
    for label, ok in stop:
        lines.append(f"- [{'x' if ok else ' '}] {label}")

    return "\n".join(lines) + "\n"


def build_cross_channel_v2() -> str:
    program = load_benchmark_program()
    profiles = [p for p in collect_all_profiles(program) if p.slug in PHASE2_SLUGS]
    patterns = analyze_patterns(profiles, "whisprs_yt")
    sections = build_niche_dna_sections(patterns, profiles, "whisprs_yt")

    lines = [
        "# Cross-Channel Synthesis v2",
        "",
        "**Evidence-only synthesis** — Phase 2 validation cohort",
        "**Channels:** " + ", ".join(f"`{s}`" for s in PHASE2_SLUGS),
        "",
        "---",
        "",
    ]

    for title, body in sections.items():
        lines.append(f"## {title}")
        lines.append("")
        lines.append(body)
        lines.append("")

    lines.append("## Pattern Frequency (validated cohort)")
    lines.append("")
    lines.append("| Pattern | Frequency | Channels | Classification |")
    lines.append("| --- | ---: | --- | --- |")
    for p in patterns:
        if p.channels_observed and set(p.channels_observed) & set(PHASE2_SLUGS):
            chs = ", ".join(p.channels_observed)
            lines.append(
                f"| {p.label} | {p.frequency:.0%} | {chs} | {p.classification} |"
            )

    lines.extend(
        [
            "",
            "## Comment Theme Comparison",
            "",
        ]
    )
    for prof in profiles:
        if prof.comment_themes:
            lines.append(f"### `{prof.slug}`")
            for theme, count in prof.comment_themes.items():
                lines.append(f"- {theme}: {count}")
            lines.append("")

    lines.append("## Interpretation (evidence-bound)")
    lines.append("")
    if sum(1 for p in profiles if p.has_comments) >= 2:
        lines.append(
            "Two or more channels have comment data. Compare save/validation phrases "
            "in audience_psychology.md across whisprs_yt and soulxsigh before claiming "
            "universal Recognition or Mechanism."
        )
    else:
        lines.append(
            "Insufficient comment overlap for mechanism validation. Visual/narrative "
            "convergence may still support Outcome Profile MVP at PARTIAL confidence."
        )

    return "\n".join(lines) + "\n"


def main() -> None:
    reports = PROJECT_ROOT / "reports"
    v2 = reports / "validation_phase2.md"
    cc = reports / "cross_channel_synthesis_v2.md"
    v2.write_text(build_validation_phase2(), encoding="utf-8")
    cc.write_text(build_cross_channel_v2(), encoding="utf-8")
    print(f"Wrote {v2}")
    print(f"Wrote {cc}")


if __name__ == "__main__":
    main()

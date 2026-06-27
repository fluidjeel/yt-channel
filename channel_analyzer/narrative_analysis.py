"""STEP 7 — Narrative Analysis: hook, reflection, insight, resolution patterns."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

import numpy as np

from channel_analyzer.config import Config
from channel_analyzer.utils import tokenize_sentences, word_count, write_markdown

logger = logging.getLogger(__name__)

REFLECTION_MARKERS = [
    r"\bi (used to|remember|realized|thought|felt|wondered)\b",
    r"\blooking back\b",
    r"\bwhen i was\b",
    r"\bfor (years|months|so long)\b",
]
INSIGHT_MARKERS = [
    r"\bthe (truth|thing|secret|lesson) is\b",
    r"\bi (learned|discovered|understood)\b",
    r"\bwhat (i|we) (need|must|should)\b",
    r"\bthat'?s (when|why|how)\b",
]
RESOLUTION_MARKERS = [
    r"\b(so|and now|today|from now)\b",
    r"\byou (can|will|deserve|are)\b",
    r"\bit'?s okay\b",
    r"\bstart\b",
    r"\bhealing\b",
    r"\blove yourself\b",
]


def _segment_narrative(sentences: list[str]) -> dict[str, Any]:
    if not sentences:
        return {
            "hook": [],
            "reflection": [],
            "insight": [],
            "resolution": [],
        }

    n = len(sentences)
    hook_end = max(1, min(2, n // 5))
    resolution_start = max(hook_end + 1, n - max(1, n // 4))

    hook = sentences[:hook_end]
    resolution = sentences[resolution_start:]
    middle = sentences[hook_end:resolution_start]

    reflection: list[str] = []
    insight: list[str] = []
    unassigned: list[str] = []

    for sent in middle:
        lower = sent.lower()
        if any(re.search(p, lower) for p in REFLECTION_MARKERS):
            reflection.append(sent)
        elif any(re.search(p, lower) for p in INSIGHT_MARKERS):
            insight.append(sent)
        else:
            unassigned.append(sent)

    # Distribute unassigned: first half → reflection, second → insight
    mid = len(unassigned) // 2
    reflection.extend(unassigned[:mid])
    insight.extend(unassigned[mid:])

    return {
        "hook": hook,
        "reflection": reflection,
        "insight": insight,
        "resolution": resolution,
    }


def _section_lengths(segments: dict[str, list[str]]) -> dict[str, int]:
    return {k: sum(word_count(s) for s in v) for k, v in segments.items()}


def analyze_narrative(config: Config) -> Path:
    """Analyze narrative structure across all transcribed videos."""
    config.ensure_dirs()
    analyses: list[dict[str, Any]] = []

    for vdir in sorted(config.downloads_dir.iterdir()):
        if not vdir.is_dir():
            continue
        tpath = vdir / "transcript.txt"
        if not tpath.exists():
            continue
        text = tpath.read_text(encoding="utf-8")
        sentences = tokenize_sentences(text)
        segments = _segment_narrative(sentences)
        lengths = _section_lengths(segments)
        total = sum(lengths.values()) or 1

        analyses.append(
            {
                "video_id": vdir.name,
                "hook_length": lengths["hook"],
                "reflection_length": lengths["reflection"],
                "insight_length": lengths["insight"],
                "resolution_length": lengths["resolution"],
                "hook_pct": round(100 * lengths["hook"] / total, 1),
                "reflection_pct": round(100 * lengths["reflection"] / total, 1),
                "insight_pct": round(100 * lengths["insight"] / total, 1),
                "resolution_pct": round(100 * lengths["resolution"] / total, 1),
                "hook_sample": " ".join(segments["hook"])[:150],
                "structure": " → ".join(
                    s
                    for s, l in [
                        ("Hook", lengths["hook"]),
                        ("Reflection", lengths["reflection"]),
                        ("Insight", lengths["insight"]),
                        ("Resolution", lengths["resolution"]),
                    ]
                    if l > 0
                ),
            }
        )

    if not analyses:
        body = "No transcripts available for narrative analysis."
    else:
        avg_hook = np.mean([a["hook_length"] for a in analyses])
        avg_refl = np.mean([a["reflection_length"] for a in analyses])
        avg_ins = np.mean([a["insight_length"] for a in analyses])
        avg_res = np.mean([a["resolution_length"] for a in analyses])

        common_structure = max(
            set(a["structure"] for a in analyses),
            key=lambda s: sum(1 for a in analyses if a["structure"] == s),
        )

        per_video = "\n".join(
            f"### {a['video_id']}\n"
            f"- Structure: {a['structure']}\n"
            f"- Lengths (words): Hook={a['hook_length']}, Reflection={a['reflection_length']}, "
            f"Insight={a['insight_length']}, Resolution={a['resolution_length']}\n"
            f"- Distribution: {a['hook_pct']}% / {a['reflection_pct']}% / "
            f"{a['insight_pct']}% / {a['resolution_pct']}%\n"
            f"- Hook: _{a['hook_sample']}_\n"
            for a in analyses
        )

        body = (
            f"**Videos analyzed:** {len(analyses)}\n\n"
            f"### Channel Narrative Template\n"
            f"Most common structure: **{common_structure}**\n\n"
            f"### Average Section Lengths (words)\n"
            f"| Section | Avg Words | Avg % |\n"
            f"|---------|-----------|-------|\n"
            f"| Hook | {avg_hook:.0f} | {np.mean([a['hook_pct'] for a in analyses]):.0f}% |\n"
            f"| Reflection | {avg_refl:.0f} | {np.mean([a['reflection_pct'] for a in analyses]):.0f}% |\n"
            f"| Insight | {avg_ins:.0f} | {np.mean([a['insight_pct'] for a in analyses]):.0f}% |\n"
            f"| Resolution | {avg_res:.0f} | {np.mean([a['resolution_pct'] for a in analyses]):.0f}% |\n\n"
            f"### Replication Guide\n"
            f"1. Open with a **{avg_hook:.0f}-word hook** (question, personal stake, or pattern interrupt)\n"
            f"2. Spend **{avg_refl:.0f} words** in reflective personal narrative\n"
            f"3. Deliver the insight in **{avg_ins:.0f} words** — the 'aha' moment\n"
            f"4. Close with **{avg_res:.0f} words** of resolution and call-to-feel\n\n"
            f"## Per-Video Breakdown\n\n{per_video}"
        )

    output = config.narrative_patterns_md
    write_markdown(output, "Narrative Pattern Analysis", {"Summary": body})
    logger.info("Wrote narrative patterns to %s", output)
    return output

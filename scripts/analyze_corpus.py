#!/usr/bin/env python3
"""
Analyze corpus of mvp_profile.json files — field emptiness, confidence, repetition.

Usage:
  python scripts/analyze_corpus.py
  python scripts/analyze_corpus.py --output reports/corpus_analysis.md
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORTS = PROJECT_ROOT / "reports"


def _walk_fields(obj: Any, prefix: str = "") -> list[tuple[str, Any, str | None]]:
    """Yield (path, value, confidence) for EvidenceField-shaped dicts."""
    rows: list[tuple[str, Any, str | None]] = []
    if isinstance(obj, dict):
        if set(obj.keys()) >= {"value", "confidence", "source"}:
            rows.append((prefix, obj.get("value"), obj.get("confidence")))
            return rows
        for k, v in obj.items():
            p = f"{prefix}.{k}" if prefix else k
            rows.extend(_walk_fields(v, p))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            rows.extend(_walk_fields(item, f"{prefix}[{i}]"))
    return rows


def _load_profiles() -> list[tuple[str, dict[str, Any]]]:
    out: list[tuple[str, dict[str, Any]]] = []
    for path in sorted(REPORTS.glob("*/mvp_profile.json")):
        slug = path.parent.name
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            out.append((slug, data))
        except json.JSONDecodeError:
            continue
    return out


def analyze(profiles: list[tuple[str, dict[str, Any]]]) -> dict[str, Any]:
    n = len(profiles)
    field_stats: dict[str, dict[str, int]] = defaultdict(lambda: Counter())
    dominant_outcomes: Counter[str] = Counter()
    rec_texts: Counter[str] = Counter()
    pipeline_status: Counter[str] = Counter()
    slugs_by_confidence: dict[str, list[str]] = defaultdict(list)

    for slug, profile in profiles:
        pipeline_status[str(profile.get("pipeline_status", "unknown"))] += 1
        for path, value, conf in _walk_fields(profile):
            if conf:
                field_stats[path][conf] += 1
                if conf in ("LOW", "N/A"):
                    slugs_by_confidence[f"{path}:{conf}"].append(slug)
            if value is None or value == [] or value == "":
                field_stats[path]["empty"] += 1
        dom = (
            profile.get("outcome_profile", {})
            .get("dominant_emotional_outcome", {})
            .get("value")
        )
        if dom:
            dominant_outcomes[str(dom)] += 1
        for item in profile.get("content_recommendations", {}).get("items", []):
            rec = item.get("recommendation", {}).get("value")
            if rec:
                rec_texts[str(rec)[:120]] += 1

    repetitive_recs = [(t, c) for t, c in rec_texts.most_common(20) if c > 1 and n > 3]

    low_fields = []
    for path, counts in field_stats.items():
        total = sum(counts.values()) - counts.get("empty", 0)
        if total == 0:
            continue
        low_na = counts.get("LOW", 0) + counts.get("N/A", 0)
        if n > 0 and low_na / max(n, 1) >= 0.5:
            low_fields.append((path, low_na, n, counts.get("empty", 0)))

    return {
        "channel_count": n,
        "pipeline_status": dict(pipeline_status),
        "dominant_outcomes": dominant_outcomes.most_common(15),
        "repetitive_recommendations": repetitive_recs,
        "frequently_low_or_empty_fields": sorted(low_fields, key=lambda x: -x[1])[:25],
        "empty_field_counts": {
            path: counts.get("empty", 0)
            for path, counts in field_stats.items()
            if counts.get("empty", 0) > 0
        },
    }


def render_markdown(stats: dict[str, Any]) -> str:
    lines = [
        "# Corpus Analysis",
        "",
        f"**Channels analyzed:** {stats['channel_count']}",
        "",
        "## Pipeline status",
        "",
    ]
    for k, v in stats.get("pipeline_status", {}).items():
        lines.append(f"- `{k}`: {v}")
    lines.extend(["", "## Dominant emotional outcomes (distinctiveness check)", ""])
    if stats.get("dominant_outcomes"):
        for val, count in stats["dominant_outcomes"]:
            lines.append(f"- `{val}`: {count} channel(s)")
    else:
        lines.append("- No data")
    lines.extend(["", "## Frequently empty fields", ""])
    empty = stats.get("empty_field_counts", {})
    if empty:
        for path, count in sorted(empty.items(), key=lambda x: -x[1])[:20]:
            lines.append(f"- `{path}`: empty on {count} channel(s)")
    else:
        lines.append("- None")
    lines.extend(["", "## Fields often LOW or N/A (≥50% of corpus)", ""])
    for path, low_na, n, empty in stats.get("frequently_low_or_empty_fields", [])[:15]:
        lines.append(f"- `{path}`: LOW/N/A on {low_na}/{n}, empty {empty}")
    lines.extend(["", "## Repetitive recommendations (same text on multiple channels)", ""])
    if stats.get("repetitive_recommendations"):
        for text, count in stats["repetitive_recommendations"][:10]:
            lines.append(f"- ({count}×) {text[:100]}...")
    else:
        lines.append("- None detected")
    lines.extend(
        [
            "",
            "## Questions this answers",
            "",
            "- Which fields collapse to empty on most channels?",
            "- Which confidence scores stay LOW outside comment-rich cohort?",
            "- Do recommendations repeat across unrelated channels?",
            "- Do dominant outcomes distinguish channels or converge to one label?",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Analyze MVP profile corpus")
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "reports" / "corpus_analysis.md",
    )
    args = parser.parse_args(argv)

    profiles = _load_profiles()
    if not profiles:
        print("No mvp_profile.json files under reports/*/")
        return 1

    stats = analyze(profiles)
    md = render_markdown(stats)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(md, encoding="utf-8")
    print(f"Wrote {args.output} ({stats['channel_count']} channels)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

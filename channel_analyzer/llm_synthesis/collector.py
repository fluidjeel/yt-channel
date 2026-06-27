"""Collect analyzer reports and structured data for LLM synthesis."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from channel_analyzer.config import Config
from channel_analyzer.utils import read_csv

logger = logging.getLogger(__name__)

# Primary report inputs for bible synthesis
REPORT_FILES = [
    "channel_playbook.md",
    "visual_analysis.md",
    "advanced_visual_analysis.md",
    "audio_analysis.md",
    "emotion_clusters.md",
    "narrative_patterns.md",
    "quote_patterns.md",
    "music_profile.md",
    "audience_psychology.md",
    "comment_patterns.md",
]

CSV_SUMMARIES = [
    "top_videos.csv",
    "advanced_visual_videos.csv",
    "emotion_scores.csv",
    "comment_clusters.csv",
]


@dataclass
class SynthesisContext:
    """Bundled inputs for Claude bible generation."""

    channel_name: str = ""
    reports: dict[str, str] = field(default_factory=dict)
    csv_summaries: dict[str, Any] = field(default_factory=dict)
    source_hash: str = ""

    def report_bundle(self, max_chars_per_report: int = 12000) -> str:
        parts = []
        for name, content in sorted(self.reports.items()):
            truncated = content[:max_chars_per_report]
            if len(content) > max_chars_per_report:
                truncated += f"\n\n_[truncated — {len(content)} chars total]_"
            parts.append(f"### SOURCE: {name}\n\n{truncated}")
        return "\n\n---\n\n".join(parts)

    def csv_bundle(self) -> str:
        return json.dumps(self.csv_summaries, indent=2, default=str)[:8000]


def _summarize_csv(path: Path, max_rows: int = 25) -> Any:
    if not path.exists():
        return None
    df = read_csv(path)
    if df.empty:
        return None
    summary: dict[str, Any] = {
        "row_count": len(df),
        "columns": list(df.columns),
    }
    if len(df) <= max_rows:
        summary["rows"] = df.to_dict(orient="records")
    else:
        summary["sample_rows"] = df.head(max_rows).to_dict(orient="records")
        # Numeric aggregates where useful
        numeric = df.select_dtypes(include="number")
        if not numeric.empty:
            summary["aggregates"] = numeric.mean(numeric_only=True).to_dict()
    return summary


def _detect_channel_name(reports: dict[str, str], top_df: pd.DataFrame) -> str:
    if not top_df.empty and "channel" in top_df.columns:
        val = str(top_df["channel"].iloc[0]).strip()
        if val:
            return val
    for content in reports.values():
        for line in content.splitlines()[:30]:
            if line.lower().startswith("**channel:**"):
                return line.split(":", 1)[1].strip().strip("*")
    return "unknown_channel"


def collect_synthesis_context(
    config: Config,
    extra_reports: list[str] | None = None,
) -> SynthesisContext:
    """Load all analyzer reports and CSV summaries from data/."""
    config.ensure_dirs()
    reports: dict[str, str] = {}

    report_names = list(REPORT_FILES)
    if extra_reports:
        report_names.extend(extra_reports)

    for name in report_names:
        path = config.reports_dir / name
        if path.exists():
            reports[name] = path.read_text(encoding="utf-8")
            logger.info("Loaded report: %s (%d chars)", name, len(reports[name]))
        else:
            logger.warning("Report not found: %s", name)

    csv_summaries: dict[str, Any] = {}
    for name in CSV_SUMMARIES:
        summary = _summarize_csv(config.data_dir / name)
        if summary:
            csv_summaries[name] = summary

    top_df = read_csv(config.top_videos_csv)
    channel = _detect_channel_name(reports, top_df)

    import hashlib

    hash_input = "".join(f"{k}:{len(v)}" for k, v in sorted(reports.items()))
    hash_input += json.dumps(csv_summaries, default=str, sort_keys=True)
    source_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:16]

    return SynthesisContext(
        channel_name=channel,
        reports=reports,
        csv_summaries=csv_summaries,
        source_hash=source_hash,
    )

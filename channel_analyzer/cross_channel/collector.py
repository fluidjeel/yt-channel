"""Collect per-channel artifacts for cross-channel comparison."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from channel_analyzer.benchmark.channels import BenchmarkProgram, load_benchmark_program
from channel_analyzer.benchmark.config import channel_config
from channel_analyzer.config import PROJECT_ROOT
from channel_analyzer.utils import read_csv

logger = logging.getLogger(__name__)

PATTERN_SIGNALS = {
    "acceptance_emotion": r"acceptance",
    "resilience_emotion": r"resilien",
    "peaceful_sadness": r"peaceful.?sadness|peaceful sadness",
    "tiny_human_large_world": r"tiny.?human|large.?world|negative space",
    "solitary_character": r"solitary|alone|dreamer",
    "looking_away_gaze": r"looking away|averted gaze|side profile",
    "self_love_theme": r"self.?love|self.?worth",
    "healing_journey": r"healing",
    "heartbreak": r"heartbreak|heart.?break",
    "recovery_not_love": r"recovery|not love|self-worth",
    "pain_acceptance_hope_arc": r"pain.*acceptance|acceptance.*hope|pain.*growth",
    "anime_aesthetic": r"anime",
    "gratitude": r"gratitude|thank you",
    "loneliness": r"loneliness|lonely",
}


@dataclass
class ChannelProfile:
    slug: str
    name: str
    group: str
    status: str
    video_count: int = 0
    top_video_count: int = 0
    median_views_per_day: float = 0.0
    max_views_per_day: float = 0.0
    has_bibles: bool = False
    has_comments: bool = False
    has_advanced_visual: bool = False
    text_corpus: str = ""
    patterns: dict[str, bool] = field(default_factory=dict)
    quote_themes: dict[str, int] = field(default_factory=dict)
    comment_themes: dict[str, int] = field(default_factory=dict)
    visual_signals: dict[str, Any] = field(default_factory=dict)


def _read_text(path: Path) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8", errors="replace")
    return ""


def _detect_patterns(text: str) -> dict[str, bool]:
    lower = text.lower()
    return {
        key: bool(re.search(pat, lower, re.IGNORECASE))
        for key, pat in PATTERN_SIGNALS.items()
    }


def _quote_themes(cfg_data_dir: Path) -> dict[str, int]:
    path = cfg_data_dir / "quote_database.csv"
    if not path.exists():
        return {}
    df = read_csv(path)
    if df.empty or "theme" not in df.columns:
        return {}
    return dict(df["theme"].value_counts().head(8))


def _comment_themes(cfg_data_dir: Path) -> dict[str, int]:
    path = cfg_data_dir / "comments.csv"
    if not path.exists():
        return {}
    df = read_csv(path)
    if df.empty or "theme" not in df.columns:
        return {}
    non_spam = df[df.get("is_spam", False) == False] if "is_spam" in df.columns else df  # noqa: E712
    return dict(non_spam["theme"].value_counts().head(8))


def _visual_signals(cfg_data_dir: Path) -> dict[str, Any]:
    path = cfg_data_dir / "advanced_visual_videos.csv"
    if not path.exists():
        return {}
    df = read_csv(path)
    if df.empty:
        return {}
    out: dict[str, Any] = {"videos_analyzed": len(df)}
    for col in (
        "dominant_archetype",
        "dominant_expression",
        "dominant_composition",
        "dominant_gaze",
    ):
        if col in df.columns:
            out[col] = dict(df[col].value_counts().head(3))
    if "avg_negative_space_pct" in df.columns:
        out["avg_negative_space_pct"] = float(df["avg_negative_space_pct"].mean())
    return out


def collect_channel_profile(slug: str, ch_meta: dict[str, str]) -> ChannelProfile:
    cfg = channel_config(slug)
    reports = cfg.reports_dir

    meta_path = reports / "benchmark_meta.json"
    status = "unknown"
    if meta_path.exists():
        try:
            status = json.loads(meta_path.read_text(encoding="utf-8")).get("status", "unknown")
        except json.JSONDecodeError:
            status = "unknown"

    corpus_parts = [
        _read_text(reports / "content_dna.md"),
        _read_text(reports / "master_emotional_bible.md"),
        _read_text(reports / "master_visual_bible.md"),
        _read_text(reports / "master_character_bible.md"),
        _read_text(reports / "audience_psychology.md"),
        _read_text(reports / "channel_playbook.md"),
    ]
    corpus = "\n".join(corpus_parts)

    top_df = read_csv(cfg.top_videos_csv)
    videos_df = read_csv(cfg.videos_csv)

    profile = ChannelProfile(
        slug=slug,
        name=ch_meta.get("name", slug),
        group=ch_meta.get("group", ""),
        status=status,
        video_count=len(videos_df),
        top_video_count=len(top_df),
        text_corpus=corpus,
        patterns=_detect_patterns(corpus),
        quote_themes=_quote_themes(cfg.data_dir),
        comment_themes=_comment_themes(cfg.data_dir),
        visual_signals=_visual_signals(cfg.data_dir),
        has_bibles=(reports / "content_dna.md").exists(),
        has_comments=(cfg.data_dir / "comments.csv").exists(),
        has_advanced_visual=(cfg.data_dir / "advanced_visual_videos.csv").exists(),
    )

    if not top_df.empty and "views_per_day" in top_df.columns:
        vpd = top_df["views_per_day"].astype(float)
        profile.median_views_per_day = float(vpd.median())
        profile.max_views_per_day = float(vpd.max())

    return profile


def collect_all_profiles(program: BenchmarkProgram | None = None) -> list[ChannelProfile]:
    program = program or load_benchmark_program()
    profiles: list[ChannelProfile] = []

    for ch in program.channels:
        # Also pick up any folder under reports/ not in yaml
        meta = {"name": ch.name, "group": ch.group}
        profiles.append(collect_channel_profile(ch.slug, meta))

    return profiles

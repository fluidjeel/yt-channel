"""Run existing pipeline per benchmark channel."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

from channel_analyzer.advanced_visual_analyzer import run_advanced_visual_analysis
from channel_analyzer.benchmark.channels import BenchmarkChannel, BenchmarkProgram
from channel_analyzer.benchmark.config import apply_pipeline_overrides, channel_config
from channel_analyzer.bible_synthesizer import run_bible_synthesis
from channel_analyzer.comment_intelligence import run_comment_intelligence
from channel_analyzer.config import PROJECT_ROOT, Config
from channel_analyzer.pipeline import Step, run_pipeline

logger = logging.getLogger(__name__)

# Files to copy when importing reference channel from root analysis
IMPORT_REPORTS = [
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
    "master_visual_bible.md",
    "master_emotional_bible.md",
    "master_character_bible.md",
    "master_narrative_bible.md",
    "master_motion_bible.md",
    "audience_persona.md",
    "content_dna.md",
]

IMPORT_DATA = [
    "videos.csv",
    "top_videos.csv",
    "quote_database.csv",
    "emotion_scores.csv",
    "comments.csv",
    "comment_clusters.csv",
    "advanced_visual_frames.csv",
    "advanced_visual_videos.csv",
]

BIBLE_OUTPUTS = [
    "content_dna.md",
    "audience_persona.md",
    "master_visual_bible.md",
    "master_emotional_bible.md",
    "master_character_bible.md",
]


def import_existing_channel(slug: str, root: Path | None = None) -> dict[str, Path]:
    """Copy root WhisprsYT analysis into reports/{slug}/ and data/channels/{slug}/."""
    root = root or PROJECT_ROOT
    cfg = channel_config(slug)
    cfg.ensure_dirs()

    copied: dict[str, Path] = {}
    src_reports = root / "reports"
    src_data = root / "data"
    src_artifacts = root / "artifacts"

    for name in IMPORT_REPORTS:
        src = src_reports / name
        if src.exists():
            dst = cfg.reports_dir / name
            shutil.copy2(src, dst)
            copied[name] = dst

    for name in IMPORT_DATA:
        src = src_data / name
        if src.exists():
            dst = cfg.data_dir / name
            shutil.copy2(src, dst)
            copied[name] = dst

    # Downloads + caches
    for sub in ("downloads", "top_frames", "comments_cache", "advanced_visual_cache"):
        src = src_artifacts / sub
        if src.exists():
            dst = cfg.artifacts_dir / sub
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            copied[f"artifacts/{sub}"] = dst

    meta = cfg.reports_dir / "benchmark_meta.json"
    meta.write_text(
        f'{{"slug":"{slug}","source":"imported_existing","status":"full"}}\n',
        encoding="utf-8",
    )
    copied["benchmark_meta.json"] = meta
    logger.info("Imported %d artifacts for %s", len(copied), slug)
    return copied


def run_channel_discovery(
    channel: BenchmarkChannel,
    program: BenchmarkProgram,
    base_config: Config | None = None,
) -> dict[str, Path]:
    """Steps 1-2 only — fast metadata for all benchmark channels."""
    cfg = channel_config(channel.slug, base_config)
    cfg = apply_pipeline_overrides(cfg, program.pipeline_overrides)
    cfg.ensure_dirs()

    results = run_pipeline(channel.url, cfg, Step.DISCOVERY, Step.PERFORMANCE)
    meta = cfg.reports_dir / "benchmark_meta.json"
    meta.write_text(
        f'{{"slug":"{channel.slug}","group":"{channel.group}","status":"discovery_only"}}\n',
        encoding="utf-8",
    )
    results["benchmark_meta.json"] = meta
    return results


def run_channel_full_pipeline(
    channel: BenchmarkChannel,
    program: BenchmarkProgram,
    base_config: Config | None = None,
    include_extensions: bool = True,
) -> dict[str, Path]:
    """Steps 1-11 + optional advanced visual, comments, bibles."""
    cfg = channel_config(channel.slug, base_config)
    cfg = apply_pipeline_overrides(cfg, program.pipeline_overrides)
    cfg.ensure_dirs()

    results = run_pipeline(channel.url, cfg, Step.DISCOVERY, Step.BONUS)

    if include_extensions:
        try:
            run_advanced_visual_analysis(config=cfg)
            results["advanced_visual"] = cfg.reports_dir / "advanced_visual_analysis.md"
        except Exception as exc:
            logger.warning("Advanced visual failed for %s: %s", channel.slug, exc)

        try:
            run_comment_intelligence(config=cfg)
            results["audience_psychology"] = cfg.reports_dir / "audience_psychology.md"
        except Exception as exc:
            logger.warning("Comment intelligence failed for %s: %s", channel.slug, exc)

        try:
            bible_paths = run_bible_synthesis(config=cfg, provider="openai")
            results.update(bible_paths)
        except Exception as exc:
            logger.warning("Bible synthesis failed for %s: %s", channel.slug, exc)

    meta = cfg.reports_dir / "benchmark_meta.json"
    meta.write_text(
        f'{{"slug":"{channel.slug}","group":"{channel.group}","status":"full"}}\n',
        encoding="utf-8",
    )
    results["benchmark_meta.json"] = meta
    return results


def ensure_channel_bibles(slug: str) -> list[str]:
    """Return which required bible outputs exist for a channel."""
    cfg = channel_config(slug)
    missing = []
    for name in BIBLE_OUTPUTS:
        if not (cfg.reports_dir / name).exists():
            missing.append(name)
    return missing

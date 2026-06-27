"""Pipeline orchestrator for Channel Intelligence Analyzer."""

from __future__ import annotations

import logging
from enum import IntEnum
from pathlib import Path

from channel_analyzer.audio_analysis import analyze_audio
from channel_analyzer.bonus import run_bonus_features
from channel_analyzer.config import Config
from channel_analyzer.discovery import discover_channel
from channel_analyzer.downloader import download_top_videos
from channel_analyzer.emotion_analysis import analyze_emotions
from channel_analyzer.music_analysis import analyze_music
from channel_analyzer.narrative_analysis import analyze_narrative
from channel_analyzer.performance import analyze_performance
from channel_analyzer.quote_analysis import analyze_quotes
from channel_analyzer.report import generate_playbook
from channel_analyzer.visual_analysis import analyze_visuals

logger = logging.getLogger(__name__)


class Step(IntEnum):
    DISCOVERY = 1
    PERFORMANCE = 2
    DOWNLOAD = 3
    AUDIO = 4
    VISUAL = 5
    EMOTION = 6
    NARRATIVE = 7
    MUSIC = 8
    QUOTES = 9
    REPORT = 10
    BONUS = 11


STEP_NAMES = {
    Step.DISCOVERY: "Channel Discovery",
    Step.PERFORMANCE: "Performance Analysis",
    Step.DOWNLOAD: "Download Assets",
    Step.AUDIO: "Audio Analysis",
    Step.VISUAL: "Visual Analysis",
    Step.EMOTION: "Emotional Analysis",
    Step.NARRATIVE: "Narrative Analysis",
    Step.MUSIC: "Audio Signature Analysis",
    Step.QUOTES: "Quote Pattern Analysis",
    Step.REPORT: "Final Report",
    Step.BONUS: "Bonus Features",
}


def run_pipeline(
    channel_url: str,
    config: Config | None = None,
    start_step: Step = Step.DISCOVERY,
    end_step: Step = Step.BONUS,
) -> dict[str, Path]:
    """
    Run the full or partial analysis pipeline.

    Returns dict mapping step names to output paths.
    """
    config = config or Config.from_yaml()
    config.ensure_dirs()
    results: dict[str, Path] = {}
    video_dirs: list[Path] = []

    steps = range(int(start_step), int(end_step) + 1)
    for step_num in steps:
        step = Step(step_num)
        name = STEP_NAMES[step]
        logger.info("=" * 60)
        logger.info("STEP %d: %s", step_num, name)
        logger.info("=" * 60)

        if step == Step.DISCOVERY:
            results["videos.csv"] = discover_channel(channel_url, config)
        elif step == Step.PERFORMANCE:
            results["top_videos.csv"] = analyze_performance(config)
        elif step == Step.DOWNLOAD:
            video_dirs = download_top_videos(config)
            results["downloads"] = config.downloads_dir
        elif step == Step.AUDIO:
            if not video_dirs:
                video_dirs = [
                    d
                    for d in config.downloads_dir.iterdir()
                    if d.is_dir() and (d / "video.mp4").exists()
                ]
            results["audio_analysis.md"] = analyze_audio(config, video_dirs)
        elif step == Step.VISUAL:
            if not video_dirs:
                video_dirs = [
                    d
                    for d in config.downloads_dir.iterdir()
                    if d.is_dir() and (d / "video.mp4").exists()
                ]
            results["visual_analysis.md"] = analyze_visuals(config, video_dirs)
        elif step == Step.EMOTION:
            results["emotion_clusters.md"] = analyze_emotions(config)
        elif step == Step.NARRATIVE:
            results["narrative_patterns.md"] = analyze_narrative(config)
        elif step == Step.MUSIC:
            results["music_profile.md"] = analyze_music(config)
        elif step == Step.QUOTES:
            csv_p, md_p = analyze_quotes(config)
            results["quote_database.csv"] = csv_p
            results["quote_patterns.md"] = md_p
        elif step == Step.REPORT:
            results["channel_playbook.md"] = generate_playbook(config)
        elif step == Step.BONUS:
            bonus = run_bonus_features(config)
            results.update({f"bonus_{k}": v for k, v in bonus.items()})

    logger.info("Pipeline complete. Outputs in data=%s reports=%s artifacts=%s",
                config.data_dir, config.reports_dir, config.artifacts_dir)
    return results

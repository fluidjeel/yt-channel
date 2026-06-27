#!/usr/bin/env python3
"""
Comment Intelligence Analyzer — audience psychology from YouTube comments.

Architecture: collector -> analyzer -> synthesizer -> report

Usage:
  python -m channel_analyzer.comment_intelligence
  python -m channel_analyzer.comment_intelligence --video-id FFUYW3587s0
  python -m channel_analyzer.comment_intelligence --llm-synthesis
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Any

import pandas as pd

from channel_analyzer.comments.analyzer import analyze_comments
from channel_analyzer.comments.collector import _filter_target_videos, collect_comments
from channel_analyzer.comments.synthesizer import synthesize_with_llm, write_reports
from channel_analyzer.config import Config, DEFAULT_CONFIG_PATH
from channel_analyzer.utils import read_csv, setup_logging

logger = logging.getLogger(__name__)


def _load_settings(config: Config) -> dict[str, Any]:
    import yaml

    defaults = {
        "max_comments_per_video": 500,
        "min_comment_length": 8,
        "n_clusters": 12,
        "embedding_model": "all-MiniLM-L6-v2",
        "llm_synthesis": False,
        "llm_provider": "anthropic",
    }
    config_path = DEFAULT_CONFIG_PATH
    if config_path.exists():
        with open(config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        ci = data.get("comment_intelligence", {})
        defaults.update({k: v for k, v in ci.items() if v is not None})
    return defaults


def _build_video_meta(config: Config, video_ids: list[str] | None = None) -> dict[str, dict[str, Any]]:
    top_df = read_csv(config.top_videos_csv)
    if top_df.empty:
        return {}
    if video_ids:
        top_df = top_df[top_df["video_id"].astype(str).isin(video_ids)]
    else:
        top_df = _filter_target_videos(top_df, config)

    meta: dict[str, dict[str, Any]] = {}
    for _, row in top_df.iterrows():
        vid = str(row["video_id"])
        meta[vid] = {
            "title": str(row.get("title", "")),
            "rank": int(row.get("rank", 0)),
            "views_per_day": float(row.get("views_per_day", 0)),
            "channel": str(row.get("channel", "")),
            "url": str(row.get("url", "")),
        }
    return meta


def run_comment_intelligence(
    config: Config | None = None,
    video_ids: list[str] | None = None,
    max_comments_per_video: int | None = None,
    min_comment_length: int | None = None,
    n_clusters: int | None = None,
    embedding_model: str | None = None,
    use_llm_synthesis: bool | None = None,
    llm_provider: str | None = None,
) -> dict[str, Path]:
    """Run full comment intelligence pipeline."""
    config = config or Config.from_yaml()
    config.ensure_dirs()
    settings = _load_settings(config)

    max_comments = max_comments_per_video or settings["max_comments_per_video"]
    min_len = min_comment_length if min_comment_length is not None else settings["min_comment_length"]
    clusters_n = n_clusters or settings["n_clusters"]
    emb_model = embedding_model or settings["embedding_model"]
    use_llm = (
        use_llm_synthesis
        if use_llm_synthesis is not None
        else bool(settings.get("llm_synthesis", False))
    )
    llm_prov = llm_provider or settings.get("llm_provider", "anthropic")

    video_meta = _build_video_meta(config, video_ids)
    if not video_meta:
        raise FileNotFoundError(f"No videos in {config.top_videos_csv}")

    raw = collect_comments(config, video_ids=video_ids, max_comments_per_video=max_comments)
    if not raw:
        raise RuntimeError("No comments collected")

    analyzed, clusters, stats = analyze_comments(
        raw,
        video_meta,
        embedding_model=emb_model,
        n_clusters=clusters_n,
        min_comment_length=min_len,
    )

    comments_csv = config.data_dir / "comments.csv"
    clusters_csv = config.data_dir / "comment_clusters.csv"
    pd.DataFrame([a.to_row() for a in analyzed]).to_csv(comments_csv, index=False)
    pd.DataFrame([c.to_row() for c in clusters]).to_csv(clusters_csv, index=False)
    logger.info("Wrote %d comments, %d clusters", len(analyzed), len(clusters))

    channel = next((a.channel for a in analyzed if a.channel), "")
    if not channel and video_meta:
        channel = next(iter(video_meta.values())).get("channel", "")

    llm_text = None
    if use_llm:
        from channel_analyzer.comments.synthesizer import build_audience_psychology_sections

        sections = build_audience_psychology_sections(analyzed, clusters, stats, channel)
        sections_text = "\n\n".join(f"## {k}\n{v}" for k, v in sections.items())
        llm_text = synthesize_with_llm(
            config.llm_cache_dir / "comment_intelligence",
            sections_text,
            stats,
            provider=llm_prov,
        )

    report_paths = write_reports(
        config.reports_dir,
        analyzed,
        clusters,
        stats,
        channel=channel,
        llm_text=llm_text,
    )

    return {
        "comments.csv": comments_csv,
        "comment_clusters.csv": clusters_csv,
        **report_paths,
    }


def main(argv: list[str] | None = None) -> int:
    setup_logging()
    parser = argparse.ArgumentParser(description="Comment Intelligence Analyzer")
    parser.add_argument("--config", type=str, help="Path to config.yaml")
    parser.add_argument("--video-id", action="append", dest="video_ids")
    parser.add_argument("--max-comments", type=int, default=None)
    parser.add_argument("--min-length", type=int, default=None)
    parser.add_argument("--clusters", type=int, default=None)
    parser.add_argument("--embedding-model", default=None)
    parser.add_argument("--llm-synthesis", action="store_true")
    parser.add_argument("--llm-provider", choices=["anthropic", "openai"], default=None)
    args = parser.parse_args(argv)

    config_path = Path(args.config) if args.config else None
    config = Config.from_yaml(config_path)

    results = run_comment_intelligence(
        config=config,
        video_ids=args.video_ids,
        max_comments_per_video=args.max_comments,
        min_comment_length=args.min_length,
        n_clusters=args.clusters,
        embedding_model=args.embedding_model,
        use_llm_synthesis=args.llm_synthesis or None,
        llm_provider=args.llm_provider,
    )
    print("\nComment intelligence complete:")
    for name, path in results.items():
        print(f"  {name}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

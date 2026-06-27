"""Collect YouTube comments for top-performing videos."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pandas as pd
import yt_dlp
from tqdm import tqdm

from channel_analyzer.comments.models import RawComment
from channel_analyzer.config import Config
from channel_analyzer.utils import load_json, merge_ytdlp_opts, read_csv, save_json

logger = logging.getLogger(__name__)


def _filter_target_videos(df: pd.DataFrame, config: Config) -> pd.DataFrame:
    """Limit to top-performing videos (top_20 flag or rank <= top_n_report)."""
    if df.empty:
        return df
    if "top_20" in df.columns:
        top = df[df["top_20"] == True]  # noqa: E712
        if not top.empty:
            return top
    if "rank" in df.columns:
        return df.nsmallest(config.top_n_report, "rank")
    return df.head(config.top_n_report)


def _parse_comment(raw: dict[str, Any], video_id: str, channel: str) -> RawComment | None:
    text = (raw.get("text") or "").strip()
    if not text:
        return None
    return RawComment(
        comment_id=str(raw.get("id", "")),
        video_id=video_id,
        text=text,
        like_count=int(raw.get("like_count") or 0),
        author=str(raw.get("author") or ""),
        parent_id=str(raw.get("parent") or ""),
        channel=channel,
    )


def fetch_video_comments(
    video_id: str,
    url: str,
    max_comments: int = 500,
    cache_path: Path | None = None,
    config: Config | None = None,
) -> list[RawComment]:
    """Fetch comments via yt-dlp; use cache when available."""
    if cache_path and cache_path.exists():
        data = load_json(cache_path)
        channel = str(data.get("channel", ""))
        return [
            c
            for item in data.get("comments", [])
            if (c := _parse_comment(item, video_id, channel)) is not None
        ]

    opts: dict[str, Any] = merge_ytdlp_opts(
        {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "getcomments": True,
            "extractor_args": {"youtube": {"max_comments": [str(max_comments)]}},
        },
        config,
    )

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)

    channel = str(info.get("channel") or info.get("uploader") or "")
    raw_comments = info.get("comments") or []
    comment_count = info.get("comment_count")
    if comment_count and not raw_comments:
        logger.warning(
            "Comment extraction mismatch for %s: comment_count=%s but fetched=0",
            video_id,
            comment_count,
        )
    if cache_path and raw_comments:
        save_json(
            cache_path,
            {
                "video_id": video_id,
                "channel": channel,
                "title": info.get("title"),
                "comment_count": comment_count,
                "comments": raw_comments,
            },
        )
    elif cache_path and comment_count == 0:
        save_json(
            cache_path,
            {
                "video_id": video_id,
                "channel": channel,
                "title": info.get("title"),
                "comment_count": 0,
                "comments": [],
            },
        )

    parsed: list[RawComment] = []
    for item in raw_comments:
        c = _parse_comment(item, video_id, channel)
        if c:
            parsed.append(c)
    return parsed


def collect_comments(
    config: Config,
    video_ids: list[str] | None = None,
    max_comments_per_video: int = 500,
) -> list[RawComment]:
    """Collect comments for top videos listed in top_videos.csv."""
    config.ensure_dirs()
    cache_dir = config.artifacts_dir / "comments_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    top_df = read_csv(config.top_videos_csv)
    if top_df.empty:
        raise FileNotFoundError(f"No videos in {config.top_videos_csv}")

    if video_ids:
        top_df = top_df[top_df["video_id"].astype(str).isin(video_ids)]
    else:
        top_df = _filter_target_videos(top_df, config)

    all_comments: list[RawComment] = []
    for _, row in tqdm(top_df.iterrows(), total=len(top_df), desc="Collecting comments"):
        video_id = str(row["video_id"])
        url = str(row.get("url") or f"https://www.youtube.com/shorts/{video_id}")
        channel = str(row.get("channel") or "")
        cache_path = cache_dir / f"{video_id}.json"
        comments = fetch_video_comments(
            video_id, url, max_comments=max_comments_per_video, cache_path=cache_path, config=config
        )
        for c in comments:
            if not c.channel and channel:
                c.channel = channel
        all_comments.extend(comments)
        logger.info("Collected %d comments for %s", len(comments), video_id)

    return all_comments

"""STEP 1 — Channel Discovery: extract all Shorts metadata."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yt_dlp
from tqdm import tqdm

from channel_analyzer.config import Config
from channel_analyzer.utils import (
    days_since_upload,
    merge_ytdlp_opts,
    normalize_channel_url,
    parse_upload_date,
    safe_float,
    safe_int,
    YTDLP_METADATA_FORMAT,
)

logger = logging.getLogger(__name__)


def _shorts_url(channel_url: str) -> str:
    url = normalize_channel_url(channel_url)
    if "/shorts" not in url:
        base = url.rstrip("/")
        for suffix in ("/videos", "/streams", "/playlists"):
            if base.endswith(suffix):
                base = base[: -len(suffix)]
        url = f"{base}/shorts"
    return url


def _videos_url(channel_url: str) -> str:
    url = channel_url.strip().rstrip("/")
    for suffix in ("/shorts", "/streams", "/playlists"):
        if url.endswith(suffix):
            url = url[: -len(suffix)]
    if not url.endswith("/videos"):
        if "/@" in url or "/channel/" in url or "/c/" in url or "/user/" in url:
            url = f"{url}/videos"
    return url


def _extract_flat_entries(channel_url: str, config: Config | None = None) -> tuple[list[dict[str, Any]], str]:
    """List all entries from channel Shorts tab, falling back to short videos."""
    shorts_url = _shorts_url(channel_url)
    opts = merge_ytdlp_opts(
        {
            "extract_flat": "in_playlist",
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": True,
        },
        config,
    )
    with yt_dlp.YoutubeDL(opts) as ydl:
        try:
            info = ydl.extract_info(shorts_url, download=False)
            if info:
                entries = [e for e in (info.get("entries") or []) if e and e.get("id")]
                if entries:
                    return entries, "shorts"
        except Exception as exc:
            logger.warning("Shorts tab unavailable: %s", exc)

    videos_url = _videos_url(channel_url)
    logger.info("Falling back to %s (filtering duration <= 60s)", videos_url)
    with yt_dlp.YoutubeDL(opts) as ydl:
        try:
            info = ydl.extract_info(videos_url, download=False)
        except Exception as exc:
            logger.warning("Videos tab unavailable: %s", exc)
            info = None
    if not info:
        return [], "videos"
    entries = [e for e in (info.get("entries") or []) if e and e.get("id")]
    return entries, "videos"


def _is_short_duration(duration: float) -> bool:
    return 0 < duration <= 60


def _enrich_entry(entry: dict[str, Any], source: str, config: Config | None = None) -> dict[str, Any] | None:
    """Fetch full metadata for a single video."""
    video_id = entry.get("id") or entry.get("url", "").split("=")[-1]
    urls = [
        f"https://www.youtube.com/shorts/{video_id}",
        f"https://www.youtube.com/watch?v={video_id}",
    ]
    opts = merge_ytdlp_opts(
        {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "format": YTDLP_METADATA_FORMAT,
        },
        config,
    )
    info: dict[str, Any] = entry
    for url in urls:
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False) or entry
            if info.get("title"):
                break
        except Exception as exc:
            logger.warning("Failed to enrich %s via %s: %s", video_id, url, exc)

    duration = safe_float(info.get("duration") or info.get("duration_string"), 0)
    if source == "videos" and duration > 0 and not _is_short_duration(duration):
        return None

    upload_raw = info.get("upload_date") or info.get("release_date")
    upload_dt = parse_upload_date(str(upload_raw) if upload_raw else None)

    return {
        "video_id": video_id,
        "title": info.get("title") or entry.get("title") or "",
        "url": url,
        "views": safe_int(info.get("view_count")),
        "likes": safe_int(info.get("like_count")),
        "upload_date": upload_dt.strftime("%Y-%m-%d") if upload_dt else "",
        "duration_seconds": duration,
        "description": (info.get("description") or "")[:500],
        "channel": info.get("channel") or info.get("uploader") or "",
        "tags": ",".join(info.get("tags") or [])[:300],
    }


def discover_channel(channel_url: str, config: Config) -> Path:
    """
    Extract all Shorts from a YouTube channel and write videos.csv.

    Returns path to videos.csv.
    """
    config.ensure_dirs()
    output_path = config.videos_csv

    logger.info("Discovering Shorts from %s", channel_url)
    entries, source = _extract_flat_entries(channel_url, config)
    if not entries:
        raise ValueError(
            f"No videos found for {channel_url}. "
            "Check the channel URL and ensure the channel has Shorts or short-form videos."
        )

    logger.info("Found %d entries via %s — fetching metadata...", len(entries), source)
    if config.max_videos_discover:
        entries = entries[: config.max_videos_discover]
        logger.info("Limited to %d videos (max_videos_discover)", len(entries))

    rows: list[dict[str, Any]] = []
    for entry in tqdm(entries, desc="Fetching metadata"):
        try:
            row = _enrich_entry(entry, source, config)
            if row:
                rows.append(row)
        except Exception as exc:
            logger.warning("Skipping entry: %s", exc)

    df = pd.DataFrame(rows)
    if df.empty and entries:
        logger.warning(
            "No enriched shorts; using flat playlist metadata for %d entries",
            len(entries),
        )
        for entry in entries:
            vid = entry.get("id") or ""
            if not vid:
                continue
            rows.append(
                {
                    "video_id": vid,
                    "title": entry.get("title") or "",
                    "url": f"https://www.youtube.com/watch?v={vid}",
                    "views": safe_int(entry.get("view_count")),
                    "likes": safe_int(entry.get("like_count")),
                    "upload_date": "",
                    "duration_seconds": safe_float(entry.get("duration"), 0),
                    "description": "",
                    "channel": entry.get("channel") or entry.get("uploader") or "",
                    "tags": "",
                }
            )
        df = pd.DataFrame(rows)

    if df.empty:
        raise ValueError("No video metadata could be retrieved.")

    df["days_since_upload"] = df["upload_date"].apply(
        lambda d: days_since_upload(parse_upload_date(d) if d else None)
    )
    df.to_csv(output_path, index=False)
    logger.info("Wrote %d videos to %s", len(df), output_path)
    return output_path

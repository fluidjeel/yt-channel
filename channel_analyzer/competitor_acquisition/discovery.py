"""Discover candidate channels via search and seed expansion."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yt_dlp

from channel_analyzer.competitor_acquisition.keywords import DEFAULT_SEED_URL, SEARCH_KEYWORDS
from channel_analyzer.utils import load_json, save_json
from market_intelligence.yt_helpers import (
    normalize_channel_base_url,
    search_channels_ytdlp,
    search_channels_youtube_api,
)

logger = logging.getLogger(__name__)

_YDL_QUIET = {"quiet": True, "no_warnings": True, "ignoreerrors": True}


def _normalize_url(url: str) -> str:
    if not url:
        return ""
    return normalize_channel_base_url(url)


def _channel_key(url: str) -> str:
    url = _normalize_url(url).lower()
    return url.rstrip("/")


def discover_from_keywords(
    keywords: list[str] | None = None,
    per_query: int = 15,
) -> list[dict[str, str]]:
    """Search YouTube for channels matching niche keywords."""
    keywords = keywords or SEARCH_KEYWORDS
    seen: set[str] = set()
    results: list[dict[str, str]] = []

    for kw in keywords:
        batch: list[dict[str, str]] = []
        batch.extend(search_channels_ytdlp(f"{kw} channel", limit=per_query))
        batch.extend(search_channels_youtube_api(kw, limit=min(per_query, 15)))

        # Also search shorts-style video results and extract channel
        batch.extend(_channels_from_video_search(f"{kw} #shorts", per_query))

        for item in batch:
            url = _normalize_url(item.get("channel_url", ""))
            if not url or "/@" not in url and "/channel/" not in url:
                continue
            key = _channel_key(url)
            if key in seen:
                continue
            seen.add(key)
            results.append(
                {
                    "channel_url": url,
                    "channel_name": item.get("channel_name") or item.get("title", ""),
                    "discovery_source": f"search:{kw}",
                }
            )
        logger.info("Keyword '%s': %d unique candidates so far", kw, len(results))

    return results


def _channels_from_video_search(query: str, limit: int) -> list[dict[str, str]]:
    """Extract channel URLs from video search results."""
    search_url = f"ytsearch{limit}:{query}"
    opts = {**_YDL_QUIET, "extract_flat": True}
    out: list[dict[str, str]] = []
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(search_url, download=False)
        for entry in info.get("entries") or []:
            if not entry:
                continue
            ch_url = entry.get("channel_url") or entry.get("uploader_url") or ""
            if ch_url:
                out.append(
                    {
                        "channel_url": _normalize_url(ch_url),
                        "channel_name": str(entry.get("channel") or entry.get("uploader") or ""),
                        "title": str(entry.get("title") or ""),
                    }
                )
    except Exception as exc:
        logger.debug("Video search failed for %s: %s", query, exc)
    return out


def discover_from_seed_videos(
    seed_url: str = DEFAULT_SEED_URL,
    max_videos: int = 5,
) -> list[dict[str, str]]:
    """Find channels via related/recommended videos on seed channel shorts."""
    seed_url = _normalize_url(seed_url)
    shorts_url = f"{seed_url}/shorts"
    opts = {**_YDL_QUIET, "extract_flat": "in_playlist", "playlistend": max_videos}
    results: list[dict[str, str]] = []
    seen: set[str] = set()

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            playlist = ydl.extract_info(shorts_url, download=False)
        entries = (playlist or {}).get("entries") or []
    except Exception as exc:
        logger.warning("Seed shorts listing failed: %s", exc)
        entries = []

    for entry in entries[:max_videos]:
        if not entry or not entry.get("id"):
            continue
        vid = entry["id"]
        # Related videos for each seed short
        results.extend(_related_channels_for_video(vid, seen))

    # Search for channels appearing near seed brand
    handle = seed_url.split("/@")[-1] if "/@" in seed_url else "WhisprsYT"
    for q in [f"channels like @{handle}", f"{handle} similar poetry shorts"]:
        for item in _channels_from_video_search(q, 10):
            key = _channel_key(item.get("channel_url", ""))
            if key and key not in seen:
                seen.add(key)
                results.append({**item, "discovery_source": "seed_expansion"})

    return results


def _related_channels_for_video(video_id: str, seen: set[str]) -> list[dict[str, str]]:
    """Pull channel URLs from related video recommendations."""
    out: list[dict[str, str]] = []
    url = f"https://www.youtube.com/watch?v={video_id}"
    opts = {**_YDL_QUIET, "skip_download": True}
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
        related = info.get("related") or []
        for rel in related[:8]:
            if not rel:
                continue
            ch = rel.get("channel_url") or rel.get("uploader_url") or ""
            ch = _normalize_url(ch)
            if not ch:
                continue
            key = _channel_key(ch)
            if key in seen:
                continue
            seen.add(key)
            out.append(
                {
                    "channel_url": ch,
                    "channel_name": str(rel.get("channel") or rel.get("uploader") or ""),
                    "discovery_source": f"related:{video_id}",
                }
            )
    except Exception as exc:
        logger.debug("Related fetch failed for %s: %s", video_id, exc)
    return out


def merge_candidates(*batches: list[dict[str, str]]) -> list[dict[str, str]]:
    """Deduplicate candidates by channel URL."""
    merged: dict[str, dict[str, str]] = {}
    for batch in batches:
        for item in batch:
            url = _normalize_url(item.get("channel_url", ""))
            if not url:
                continue
            key = _channel_key(url)
            if key not in merged:
                merged[key] = {**item, "channel_url": url}
            else:
                src = merged[key].get("discovery_source", "")
                new_src = item.get("discovery_source", "")
                if new_src and new_src not in src:
                    merged[key]["discovery_source"] = f"{src}; {new_src}" if src else new_src
    return list(merged.values())


def load_cached_candidates(cache_path: Path) -> list[dict[str, str]] | None:
    if cache_path.exists():
        data = load_json(cache_path)
        if isinstance(data, list) and data:
            return data
    return None


def save_cached_candidates(cache_path: Path, candidates: list[dict[str, str]]) -> None:
    save_json(cache_path, candidates)

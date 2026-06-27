"""YouTube data extraction helpers for Market Intelligence."""

from __future__ import annotations

import logging
import re
from typing import Any
from urllib.parse import urlparse

import yt_dlp

from channel_analyzer.utils import safe_float, safe_int
from market_intelligence.models import ChannelMetadata

logger = logging.getLogger(__name__)

_YDL_QUIET = {"quiet": True, "no_warnings": True, "ignoreerrors": True}


def normalize_channel_base_url(url: str) -> str:
    """Return canonical channel base URL without tab suffixes."""
    url = url.strip().rstrip("/")
    for suffix in ("/shorts", "/videos", "/streams", "/playlists", "/about"):
        if url.endswith(suffix):
            url = url[: -len(suffix)]
    return url


def channel_videos_url(url: str) -> str:
    base = normalize_channel_base_url(url)
    return f"{base}/videos"


def extract_channel_id(url: str) -> str:
    base = normalize_channel_base_url(url)
    if "/channel/" in base:
        return base.split("/channel/")[-1].split("/")[0]
    if "/@" in base:
        return base.split("/@")[-1].split("/")[0]
    return base.rsplit("/", 1)[-1]


def _ydl() -> yt_dlp.YoutubeDL:
    return yt_dlp.YoutubeDL(_YDL_QUIET)


def fetch_channel_info(channel_url: str) -> dict[str, Any]:
    """Fetch channel-level metadata via yt-dlp."""
    url = normalize_channel_base_url(channel_url)
    with _ydl() as ydl:
        info = ydl.extract_info(url, download=False)
    return info or {}


def fetch_video_titles(channel_url: str, limit: int = 20) -> list[str]:
    """Fetch recent video titles from a channel."""
    url = channel_videos_url(channel_url)
    opts = {**_YDL_QUIET, "extract_flat": "in_playlist", "playlistend": limit}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    entries = info.get("entries") or [] if info else []
    return [str(e.get("title", "")) for e in entries if e and e.get("title")]


def fetch_video_snippets(channel_url: str, limit: int = 10) -> list[dict[str, str]]:
    """Fetch title + description snippets for recent videos."""
    url = channel_videos_url(channel_url)
    opts = {**_YDL_QUIET, "extract_flat": "in_playlist", "playlistend": limit}
    with yt_dlp.YoutubeDL(opts) as ydl:
        playlist = ydl.extract_info(url, download=False)
    entries = playlist.get("entries") or [] if playlist else []
    snippets: list[dict[str, str]] = []
    for entry in entries:
        if not entry or not entry.get("id"):
            continue
        video_url = f"https://www.youtube.com/watch?v={entry['id']}"
        try:
            with _ydl() as ydl:
                info = ydl.extract_info(video_url, download=False)
            snippets.append(
                {
                    "title": str(info.get("title") or ""),
                    "description": str(info.get("description") or "")[:500],
                }
            )
        except Exception as exc:
            logger.debug("Snippet fetch failed for %s: %s", video_url, exc)
    return snippets


def metadata_from_info(
    info: dict[str, Any],
    discovery_source: str = "seed",
    niche_category: str = "",
) -> ChannelMetadata:
    channel_id = str(info.get("channel_id") or info.get("id") or "")
    channel_url = normalize_channel_base_url(
        info.get("channel_url") or info.get("uploader_url") or info.get("webpage_url") or ""
    )
    if not channel_url and channel_id:
        channel_url = f"https://www.youtube.com/channel/{channel_id}"

    return ChannelMetadata(
        channel_id=channel_id,
        channel_name=str(info.get("channel") or info.get("uploader") or ""),
        channel_url=channel_url,
        subscriber_count=safe_int(info.get("channel_follower_count")),
        video_count=safe_int(info.get("playlist_count") or info.get("n_entries")),
        total_views=safe_int(info.get("view_count")),
        description=str(info.get("description") or "")[:1000],
        niche_category=niche_category,
        discovery_source=discovery_source,
        tags=list(info.get("tags") or []),
    )


def build_channel_metadata(
    channel_url: str,
    discovery_source: str = "seed",
    niche_category: str = "",
    video_sample: int = 10,
) -> ChannelMetadata:
    info = fetch_channel_info(channel_url)
    meta = metadata_from_info(info, discovery_source, niche_category)
    meta.top_titles = fetch_video_titles(channel_url, limit=video_sample)
    return meta


def search_channels_ytdlp(query: str, limit: int = 25) -> list[dict[str, str]]:
    """Search YouTube for channels using yt-dlp search."""
    search_url = f"ytsearch{limit}:{query}"
    opts = {**_YDL_QUIET, "extract_flat": True}
    results: list[dict[str, str]] = []
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(search_url, download=False)
        for entry in info.get("entries") or []:
            if not entry:
                continue
            url = entry.get("url") or entry.get("webpage_url") or ""
            channel = entry.get("channel_url") or entry.get("uploader_url") or ""
            if channel:
                results.append(
                    {
                        "channel_url": normalize_channel_base_url(channel),
                        "channel_name": str(entry.get("channel") or entry.get("uploader") or ""),
                        "title": str(entry.get("title") or ""),
                    }
                )
            elif url and "/@" in url:
                results.append(
                    {
                        "channel_url": normalize_channel_base_url(url),
                        "channel_name": str(entry.get("title") or ""),
                        "title": str(entry.get("title") or ""),
                    }
                )
    except Exception as exc:
        logger.warning("yt-dlp search failed for '%s': %s", query, exc)
    return results


def search_channels_youtube_api(query: str, limit: int = 25) -> list[dict[str, str]]:
    """Search channels via youtube-search-python."""
    results: list[dict[str, str]] = []
    try:
        from youtubesearchpython import ChannelsSearch

        search = ChannelsSearch(query, limit=min(limit, 20))
        for item in search.result().get("result", []):
            link = item.get("link") or ""
            if link:
                results.append(
                    {
                        "channel_url": normalize_channel_base_url(link),
                        "channel_name": str(item.get("title") or ""),
                        "title": str(item.get("title") or ""),
                    }
                )
    except Exception as exc:
        logger.warning("ChannelsSearch failed for '%s': %s", query, exc)
    return results


def infer_niche_category(themes: list[str], description: str) -> str:
    """Heuristic niche classification from themes and description."""
    text = " ".join(themes + [description]).lower()
    niches = {
        "motivation": ["motivation", "inspire", "mindset", "success", "grind"],
        "spirituality": ["spiritual", "soul", "meditation", "faith", "universe"],
        "self_help": ["self help", "healing", "growth", "therapy", "mental health"],
        "relationships": ["relationship", "love", "dating", "marriage", "heart"],
        "education": ["learn", "education", "tutorial", "explained", "science"],
        "entertainment": ["funny", "comedy", "entertainment", "viral", "reaction"],
        "business": ["business", "entrepreneur", "startup", "money", "marketing"],
    }
    scores = {k: sum(1 for w in words if w in text) for k, words in niches.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "general"

"""Fast channel metadata for discovery scoring (timeouts, flat playlists)."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import yt_dlp

from channel_analyzer.utils import safe_int
from market_intelligence.yt_helpers import normalize_channel_base_url

logger = logging.getLogger(__name__)

_YDL_FAST = {
    "quiet": True,
    "no_warnings": True,
    "ignoreerrors": True,
    "socket_timeout": 20,
}


@dataclass
class FastChannelProfile:
    channel_name: str = ""
    channel_url: str = ""
    description: str = ""
    subscriber_count: int = 0
    video_count: int = 0
    total_views: int = 0
    avg_views: float = 0.0
    top_titles: list[str] = field(default_factory=list)


def _flat_titles(channel_url: str, tab: str, limit: int = 8) -> list[str]:
    url = f"{normalize_channel_base_url(channel_url)}/{tab}"
    opts = {**_YDL_FAST, "extract_flat": "in_playlist", "playlistend": limit}
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
        entries = (info or {}).get("entries") or []
        return [str(e.get("title", "")) for e in entries if e and e.get("title")]
    except Exception as exc:
        logger.debug("Flat %s failed for %s: %s", tab, channel_url, exc)
        return []


def fetch_fast_profile(channel_url: str, title_limit: int = 8) -> FastChannelProfile | None:
    """Two quick yt-dlp calls max: channel about + shorts/videos titles."""
    base = normalize_channel_base_url(channel_url)
    profile = FastChannelProfile(channel_url=base)

    try:
        with yt_dlp.YoutubeDL(_YDL_FAST) as ydl:
            info = ydl.extract_info(base, download=False)
    except Exception as exc:
        logger.debug("Channel info failed for %s: %s", base, exc)
        return None

    if not info:
        return None

    profile.channel_name = str(info.get("channel") or info.get("uploader") or "")
    profile.description = str(info.get("description") or "")[:1500]
    profile.subscriber_count = safe_int(info.get("channel_follower_count"))
    profile.video_count = safe_int(info.get("playlist_count") or info.get("n_entries"))
    profile.total_views = safe_int(info.get("view_count"))

    titles = _flat_titles(base, "shorts", title_limit)
    if len(titles) < 3:
        titles = titles or _flat_titles(base, "videos", title_limit)
    profile.top_titles = titles

    if profile.video_count > 0 and profile.total_views > 0:
        profile.avg_views = profile.total_views / profile.video_count
    elif titles:
        profile.avg_views = 0.0

    return profile

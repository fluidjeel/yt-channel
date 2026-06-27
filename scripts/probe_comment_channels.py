#!/usr/bin/env python3
"""Probe discovery candidates for shorts count + comment activity."""
from __future__ import annotations

import json
from typing import Any

import yt_dlp

CANDIDATES = [
    ("dark_poetry_hub", "https://www.youtube.com/channel/UCaJ-H9tCXwWMFt-sL7YQM1w"),
    ("unerase_poetry", "https://www.youtube.com/channel/UCX_7hEUHZCQhQI8oqHPsr0g"),
    ("love_journal", "https://www.youtube.com/channel/UCjStaNlesWDJZhXtS0958-A"),
    ("poetry_slow_life", "https://www.youtube.com/channel/UCpXLm3fQI7H-xgMwGkqZpRg"),
    ("breath_of_poetry", "https://www.youtube.com/channel/UC6sN5s9MiYr6rLN0RxMKlRg"),
    ("anime_quote_mindset", "https://www.youtube.com/channel/UC8n5SozUUAcAev1Gqh7OQZw"),
    ("ministry_of_poetry", "https://www.youtube.com/channel/UCVCStd-l7wOufxvHa4c9vEA"),
    ("deep_verse", "https://www.youtube.com/@DeepVerseYT"),
    ("thefallenpoet", "https://www.youtube.com/@thefallenpoet"),
    ("the_love_lines", "https://www.youtube.com/@TheLoveLinesYT"),
    ("poetic_mind", "https://www.youtube.com/@PoeticMindYT"),
    ("silent_poetry", "https://www.youtube.com/@SilentPoetryYT"),
    ("heartfelt_quotes", "https://www.youtube.com/@HeartfeltQuotesYT"),
]


def fetch_shorts(url: str, limit: int = 15) -> list[dict[str, Any]]:
    opts: dict = {
        "quiet": True,
        "extract_flat": True,
        "playlistend": limit,
    }
    shorts_url = url.rstrip("/") + "/shorts"
    with yt_dlp.YoutubeDL(opts) as ydl:
        try:
            info = ydl.extract_info(shorts_url, download=False)
        except Exception:
            return []
    entries = info.get("entries") or []
    return [e for e in entries if e and e.get("id")]


def probe_video(video_id: str) -> dict[str, Any]:
    url = f"https://www.youtube.com/shorts/{video_id}"
    opts: dict = {
        "quiet": True,
        "skip_download": True,
        "getcomments": True,
        "extractor_args": {"youtube": {"max_comments": ["20"]}},
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    comments = info.get("comments") or []
    return {
        "video_id": video_id,
        "title": (info.get("title") or "")[:60],
        "comment_count": info.get("comment_count"),
        "fetched": len(comments),
    }


def probe_channel(slug: str, url: str) -> dict[str, Any]:
    result: dict[str, Any] = {"slug": slug, "url": url}
    try:
        opts: dict = {"quiet": True, "skip_download": True}
        with yt_dlp.YoutubeDL(opts) as ydl:
            ch = ydl.extract_info(url, download=False)
        result["channel"] = ch.get("channel") or ch.get("title")
        result["alive"] = True
    except Exception as exc:
        result["alive"] = False
        result["error"] = str(exc)
        return result

    shorts = fetch_shorts(url)
    result["shorts_found"] = len(shorts)
    if not shorts:
        return result

    samples = []
    total_cc = 0
    for entry in shorts[:5]:
        try:
            s = probe_video(entry["id"])
            samples.append(s)
            total_cc += int(s.get("comment_count") or 0)
        except Exception as exc:
            samples.append({"video_id": entry["id"], "error": str(exc)})
    result["comment_samples"] = samples
    result["comment_count_sum_top5"] = total_cc
    result["avg_comment_count_top5"] = total_cc / max(len(samples), 1)
    return result


def main() -> None:
    out = [probe_channel(slug, url) for slug, url in CANDIDATES]
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()

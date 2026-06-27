#!/usr/bin/env python3
from __future__ import annotations

import json

import yt_dlp

HANDLES = [
    "@PoetryOfWhispers",
    "@SilentWhispersYT",
    "@DeepThoughtsQuotesYT",
    "@EmotionalQuotesYT",
    "@ThePoetryCornerYT",
    "@HeartbreakHealingYT",
    "@AnimeQuotesDaily",
    "@PoetryForTheSoulYT",
    "@FallenPoetryYT",
    "@DarkPoetryLines",
    "@SoulfulWhispersYT",
    "@WhisperedQuotesYT",
]

FLAT = {"quiet": True, "extract_flat": True, "playlistend": 8}
CMT = {
    "quiet": True,
    "skip_download": True,
    "getcomments": True,
    "extractor_args": {"youtube": {"max_comments": ["20"]}},
}


def probe_handle(handle: str) -> dict:
    url = f"https://www.youtube.com/{handle}/shorts"
    out: dict = {"handle": handle}
    try:
        with yt_dlp.YoutubeDL(FLAT) as ydl:
            pl = ydl.extract_info(url, download=False)
    except Exception as exc:
        out["error"] = str(exc)[:160]
        return out

    entries = [e for e in (pl.get("entries") or []) if e and e.get("id")]
    out["shorts"] = len(entries)
    out["name"] = pl.get("channel") or pl.get("title")
    total = 0
    fetched = 0
    for e in entries[:3]:
        with yt_dlp.YoutubeDL(CMT) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/shorts/{e['id']}", download=False)
        total += int(info.get("comment_count") or 0)
        fetched += len(info.get("comments") or [])
    out["comment_count_sum"] = total
    out["fetched"] = fetched
    return out


if __name__ == "__main__":
    for h in HANDLES:
        print(json.dumps(probe_handle(h)))

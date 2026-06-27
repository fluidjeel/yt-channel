#!/usr/bin/env python3
from __future__ import annotations

import json
import warnings

import yt_dlp

warnings.filterwarnings("ignore")

URLS = [
    ("writing_for_loneliness", "https://www.youtube.com/channel/UCwaN4zcDGKDMjxYhuBtP-GA"),
    ("3am_thoughts", "https://www.youtube.com/channel/UCOUV-GWZFgk0ImLYd7mCaKA"),
    ("soulxsigh", "https://www.youtube.com/channel/UC02xh2C0BZsEri175ZAU0tw"),
    ("beda_poetry", "https://www.youtube.com/channel/UCyGFT6wznWmxZa7snUnk0pA"),
    ("short_quotes_channel", "https://www.youtube.com/channel/UCPpQElu8z3Uw9raDHkaA_aQ"),
    ("unerase_poetry", "https://www.youtube.com/channel/UCX_7hEUHZCQhQI8oqHPsr0g"),
    ("dark_poetry_hub", "https://www.youtube.com/channel/UCaJ-H9tCXwWMFt-sL7YQM1w"),
]

OPTS = {
    "quiet": True,
    "skip_download": True,
    "getcomments": True,
    "extractor_args": {"youtube": {"max_comments": ["30"]}},
}


def probe(slug: str, url: str) -> dict:
    out: dict = {"slug": slug, "url": url}
    flat_opts = {"quiet": True, "extract_flat": True, "playlistend": 20}
    try:
        with yt_dlp.YoutubeDL(flat_opts) as ydl:
            pl = ydl.extract_info(f"{url.rstrip('/')}/shorts", download=False)
    except Exception as exc:
        out["error"] = str(exc)
        return out

    entries = [e for e in (pl.get("entries") or []) if e and e.get("id")]
    out["shorts_count"] = len(entries)
    samples = []
    for e in entries[:5]:
        vid = e["id"]
        try:
            with yt_dlp.YoutubeDL(OPTS) as ydl:
                info = ydl.extract_info(f"https://www.youtube.com/shorts/{vid}", download=False)
            comments = info.get("comments") or []
            samples.append(
                {
                    "video_id": vid,
                    "title": (info.get("title") or "")[:55],
                    "comment_count": info.get("comment_count"),
                    "fetched": len(comments),
                }
            )
        except Exception as exc:
            samples.append({"video_id": vid, "error": str(exc)})
    out["samples"] = samples
    out["comment_count_sum"] = sum(int(s.get("comment_count") or 0) for s in samples if "error" not in s)
    return out


if __name__ == "__main__":
    for slug, url in URLS:
        print(json.dumps(probe(slug, url)))

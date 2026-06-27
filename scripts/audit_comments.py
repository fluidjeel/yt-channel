#!/usr/bin/env python3
"""One-off audit: test yt-dlp comment extraction per benchmark channel."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import yt_dlp

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "channels"


def fetch_comments(url: str, max_comments: int = 50) -> dict:
    opts: dict = {
        "quiet": True,
        "skip_download": True,
        "getcomments": True,
        "extractor_args": {"youtube": {"max_comments": [str(max_comments)]}},
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    comments = info.get("comments") or []
    return {
        "title": info.get("title"),
        "comment_count": info.get("comment_count"),
        "availability": info.get("availability"),
        "comments_len": len(comments),
        "sample": (comments[0].get("text", "")[:120] if comments else ""),
    }


def audit_channel(slug: str) -> dict:
    top_csv = DATA / slug / "top_videos.csv"
    cache_dir = ROOT / "artifacts" / "channels" / slug / "comments_cache"
    if not top_csv.exists():
        return {"slug": slug, "status": "no_top_videos_csv"}

    df = pd.read_csv(top_csv)
    if df.empty:
        return {"slug": slug, "status": "empty_top_videos"}

    top = df[df["top_20"] == True] if "top_20" in df.columns else df.head(10)  # noqa: E712
    video_rows = []
    cache_empty = 0
    cache_with_comments = 0
    cache_total = 0

    if cache_dir.exists():
        for p in cache_dir.glob("*.json"):
            cache_total += 1
            data = json.loads(p.read_text(encoding="utf-8"))
            n = len(data.get("comments") or [])
            if n == 0:
                cache_empty += 1
            else:
                cache_with_comments += 1

    for _, row in top.head(3).iterrows():
        vid = str(row["video_id"])
        url = str(row.get("url") or f"https://www.youtube.com/shorts/{vid}")
        try:
            live = fetch_comments(url)
            live["video_id"] = vid
            live["error"] = None
        except Exception as exc:
            live = {"video_id": vid, "error": str(exc)}
        video_rows.append(live)

    comments_csv = DATA / slug / "comments.csv"
    cleaned = 0
    if comments_csv.exists():
        cleaned = len(pd.read_csv(comments_csv))

    return {
        "slug": slug,
        "status": "ok",
        "top_videos": len(top),
        "cache_total": cache_total,
        "cache_empty": cache_empty,
        "cache_with_comments": cache_with_comments,
        "cleaned_comments": cleaned,
        "live_samples": video_rows,
    }


def main() -> None:
    slugs = sorted(p.name for p in DATA.iterdir() if p.is_dir())
    results = [audit_channel(s) for s in slugs]
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()

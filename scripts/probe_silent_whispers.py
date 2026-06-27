#!/usr/bin/env python3
from __future__ import annotations

import json

import yt_dlp

URL = "https://www.youtube.com/@SilentWhispersYT/shorts"
FLAT = {"quiet": True, "extract_flat": True, "playlistend": 30}
CMT = {
    "quiet": True,
    "skip_download": True,
    "getcomments": True,
    "extractor_args": {"youtube": {"max_comments": ["30"]}},
}

with yt_dlp.YoutubeDL(FLAT) as ydl:
    pl = ydl.extract_info(URL, download=False)
entries = [e for e in (pl.get("entries") or []) if e and e.get("id")]
print("shorts", len(entries))
total = 0
for e in entries[:10]:
    with yt_dlp.YoutubeDL(CMT) as ydl:
        info = ydl.extract_info(f"https://www.youtube.com/shorts/{e['id']}", download=False)
    cc = int(info.get("comment_count") or 0)
    fetched = len(info.get("comments") or [])
    total += cc
    print(json.dumps({"id": e["id"], "title": (info.get("title") or "")[:50], "comment_count": cc, "fetched": fetched}))
print("sum top10", total)

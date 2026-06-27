#!/usr/bin/env python3
import yt_dlp

opts = {
    "quiet": True,
    "no_warnings": True,
    "extract_flat": "in_playlist",
    "cookiefile": "cookies/youtube.txt",
}
info = yt_dlp.YoutubeDL(opts).extract_info(
    "https://www.youtube.com/@WhisprsYT/shorts", download=False
)
entries = [e for e in (info.get("entries") or []) if e][:10]
print("shorts_entries", len(entries))
if entries:
    print("first_id", entries[0].get("id"))

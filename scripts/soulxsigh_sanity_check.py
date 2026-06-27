#!/usr/bin/env python3
"""Pre-pipeline sanity check: soulxsigh Shorts + comment quality."""
from __future__ import annotations

import json
import re
from pathlib import Path

import yt_dlp

CHANNEL = "https://www.youtube.com/channel/UC02xh2C0BZsEri175ZAU0tw"
FLAT = {"quiet": True, "extract_flat": True, "playlistend": 20}
CMT = {
    "quiet": True,
    "skip_download": True,
    "getcomments": True,
    "extractor_args": {"youtube": {"max_comments": ["30"]}},
}

EMOJI_ONLY = re.compile(r"^[\s\W\d]+$", re.UNICODE)


def is_emoji_or_trivial(text: str) -> bool:
    t = text.strip()
    if len(t) < 3:
        return True
    if not re.search(r"[a-zA-Z]{2,}", t):
        return True
    return False


def main() -> None:
    with yt_dlp.YoutubeDL(FLAT) as ydl:
        pl = ydl.extract_info(f"{CHANNEL}/shorts", download=False)
    entries = [e for e in (pl.get("entries") or []) if e and e.get("id")]

    all_comments: list[str] = []
    trivial = 0
    substantive = 0
    total_cc = 0
    rows: list[dict] = []

    for i, e in enumerate(entries[:15]):
        vid = e["id"]
        with yt_dlp.YoutubeDL(CMT) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/shorts/{vid}", download=False)
        title = (info.get("title") or "")[:70]
        upload = info.get("upload_date") or ""
        cc = int(info.get("comment_count") or 0)
        fetched = info.get("comments") or []
        total_cc += cc
        texts = [c.get("text", "").strip() for c in fetched if c.get("text")]
        for t in texts:
            all_comments.append(t)
            if is_emoji_or_trivial(t):
                trivial += 1
            else:
                substantive += 1
        rows.append(
            {
                "index": i + 1,
                "video_id": vid,
                "title": title,
                "upload": upload,
                "comment_count": cc,
                "fetched": len(texts),
                "sample": texts[0][:120] if texts else "",
            }
        )

    out = {
        "channel": pl.get("channel") or pl.get("title"),
        "shorts_count": len(entries),
        "inspected": len(rows),
        "comment_count_sum": total_cc,
        "comments_fetched": len(all_comments),
        "substantive": substantive,
        "trivial": trivial,
        "substantive_pct": round(100 * substantive / len(all_comments), 1) if all_comments else 0,
        "substantive_samples": [c[:120] for c in all_comments if not is_emoji_or_trivial(c)][:10],
        "videos": rows,
    }
    path = Path(__file__).resolve().parents[1] / "reports" / "soulxsigh_sanity_check.json"
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Convert semicolon cookie header to Netscape format for yt-dlp."""
from __future__ import annotations

import sys
from pathlib import Path

EXP = "1893456000"


def convert(raw: str) -> str:
    lines = ["# Netscape HTTP Cookie File", "# yt-dlp cookiefile — do not commit"]
    for part in raw.split(";"):
        part = part.strip()
        if not part or "=" not in part:
            continue
        name, val = part.split("=", 1)
        name, val = name.strip(), val.strip()
        if not name:
            continue
        secure = "TRUE" if name.startswith("__Secure-") or name in (
            "SSID", "SAPISID", "APISID", "HSID", "SID", "LOGIN_INFO"
        ) else "FALSE"
        lines.append(f".youtube.com\tTRUE\t/\t{secure}\t{EXP}\t{name}\t{val}")
    return "\n".join(lines) + "\n"


def main() -> int:
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("cookies/raw_header.txt")
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("cookies/youtube.txt")
    raw = src.read_text(encoding="utf-8").strip()
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(convert(raw), encoding="utf-8")
    print(f"Wrote {dst} ({len(raw.split(';'))} parts)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

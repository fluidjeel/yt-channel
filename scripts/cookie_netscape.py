"""Write Playwright / browser cookies in Netscape format for yt-dlp."""

from __future__ import annotations

from pathlib import Path
from typing import Any

YOUTUBE_DOMAINS = (".youtube.com", "youtube.com", ".www.youtube.com", "www.youtube.com")


def filter_youtube_cookies(cookies: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for c in cookies:
        domain = str(c.get("domain") or "")
        if any(d in domain or domain.endswith("youtube.com") for d in YOUTUBE_DOMAINS):
            out.append(c)
        elif "youtube.com" in domain:
            out.append(c)
    return out


def has_youtube_session(cookies: list[dict[str, Any]]) -> bool:
    names = {c.get("name") for c in cookies}
    return bool(names & {"SID", "__Secure-1PSID", "LOGIN_INFO"})


def to_netscape(cookies: list[dict[str, Any]]) -> str:
    lines = ["# Netscape HTTP Cookie File", "# Generated for yt-dlp — do not commit"]
    for c in cookies:
        domain = str(c.get("domain") or ".youtube.com")
        if not domain.startswith("."):
            domain = f".{domain.lstrip('.')}"
        path = str(c.get("path") or "/")
        secure = "TRUE" if c.get("secure") else "FALSE"
        expires = c.get("expires")
        if expires in (None, -1, 0):
            exp = "1893456000"
        else:
            try:
                exp = str(int(float(expires)))
            except (TypeError, ValueError):
                exp = "1893456000"
        name = str(c.get("name") or "")
        value = str(c.get("value") or "")
        if not name:
            continue
        lines.append(f"{domain}\tTRUE\t{path}\t{secure}\t{exp}\t{name}\t{value}")
    return "\n".join(lines) + "\n"


def write_netscape(path: Path, cookies: list[dict[str, Any]]) -> int:
    yt = filter_youtube_cookies(cookies)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(to_netscape(yt), encoding="utf-8")
    return len(yt)

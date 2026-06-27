"""Shared utilities for Channel Intelligence Analyzer."""

from __future__ import annotations

import json
import logging
import re
import shutil
from datetime import datetime, timezone
import os
from pathlib import Path
from typing import Any

import pandas as pd

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"


def setup_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(level=level, format=LOG_FORMAT)


def normalize_channel_url(url: str) -> str:
    """Normalize channel URL and ensure Shorts tab when appropriate."""
    url = url.strip().rstrip("/")
    if "/shorts" not in url and "/videos" not in url and "/streams" not in url:
        if "@" in url or "/channel/" in url or "/c/" in url or "/user/" in url:
            url = f"{url}/shorts"
    return url


def safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def parse_upload_date(date_str: str | None) -> datetime | None:
    if not date_str:
        return None
    for fmt in ("%Y%m%d", "%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(str(date_str)[:10].replace("/", "-"), fmt).replace(
                tzinfo=timezone.utc
            )
        except ValueError:
            continue
    return None


def days_since_upload(upload_date: datetime | None) -> float:
    if upload_date is None:
        return 1.0
    now = datetime.now(timezone.utc)
    if upload_date.tzinfo is None:
        upload_date = upload_date.replace(tzinfo=timezone.utc)
    delta = (now - upload_date).total_seconds() / 86400
    return max(delta, 1.0)


def slugify(text: str, max_len: int = 60) -> str:
    text = re.sub(r"[^\w\s-]", "", text.lower())
    text = re.sub(r"[\s_-]+", "-", text).strip("-")
    return text[:max_len] or "video"


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)


def load_json(path: Path) -> Any:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_markdown(path: Path, title: str, sections: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"# {title}", ""]
    for heading, body in sections.items():
        lines.extend([f"## {heading}", "", body.strip(), ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def _deno_executable() -> str | None:
    """Return deno path if installed (required by yt-dlp 2026+ for YouTube JS challenges)."""
    home_deno = Path.home() / ".deno" / "bin" / "deno"
    if home_deno.is_file():
        return str(home_deno)
    return shutil.which("deno")


def merge_ytdlp_opts(base: dict, config: Any | None = None) -> dict:
    """Add cookiefile to yt-dlp opts when configured (avoids YouTube bot blocks on VMs)."""
    opts = dict(base)
    cookies: Path | None = None
    if config is not None and getattr(config, "yt_dlp_cookies_file", None):
        cookies = config.yt_dlp_cookies_file
    env = os.environ.get("YTDLP_COOKIES_FILE")
    if env and Path(env).exists():
        cookies = Path(env)
    if cookies and cookies.exists():
        opts["cookiefile"] = str(cookies)
    # Flat playlist scans must not set format; metadata/download benefit from fallbacks.
    if not opts.get("extract_flat"):
        opts.setdefault("ignore_no_formats_error", True)
    deno = _deno_executable()
    if deno and "js_runtimes" not in opts and not opts.get("extract_flat"):
        opts["js_runtimes"] = {"deno": {"path": deno}}
        # yt-dlp 2026+ needs EJS solver scripts for YouTube signature challenges
        opts.setdefault("remote_components", {"ejs:github"})
    return opts


# Shorts-friendly format chains (strict mp4-only often fails on YouTube Shorts)
YTDLP_DOWNLOAD_FORMAT = "bestvideo*+bestaudio/best/b"
YTDLP_METADATA_FORMAT = "best/b"


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def tokenize_sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text.strip())
    if not text:
        return []
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [p.strip() for p in parts if p.strip()]


def word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))


def extract_ngrams(text: str, n: int = 3, min_freq: int = 2) -> list[tuple[str, int]]:
    words = re.findall(r"\b\w+\b", text.lower())
    if len(words) < n:
        return []
    from collections import Counter

    grams = [" ".join(words[i : i + n]) for i in range(len(words) - n + 1)]
    counts = Counter(grams)
    return sorted(
        [(g, c) for g, c in counts.items() if c >= min_freq],
        key=lambda x: x[1],
        reverse=True,
    )

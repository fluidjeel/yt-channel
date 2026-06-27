"""Resolve channel slug from URL — benchmark lookup first, then handle extraction."""

from __future__ import annotations

import re
from pathlib import Path

from channel_analyzer.benchmark.channels import load_benchmark_program
from channel_analyzer.utils import slugify


def _normalize_url_key(url: str) -> str:
    key = url.strip().rstrip("/").lower()
    key = key.replace("https://www.youtube.com", "https://youtube.com")
    key = key.replace("http://www.youtube.com", "https://youtube.com")
    for suffix in ("/shorts", "/videos", "/streams", "/playlists"):
        if key.endswith(suffix):
            key = key[: -len(suffix)]
    return key.rstrip("/")


def _handle_to_slug(handle: str) -> str:
    spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", handle)
    slug = re.sub(r"[^\w]", "_", spaced.lower())
    slug = re.sub(r"_+", "_", slug).strip("_")
    return slug[:60] or "channel"


def resolve_channel_slug(
    channel_url: str,
    *,
    benchmark_path: Path | None = None,
) -> str:
    """Return slug for reports/{slug}/ — matches benchmark_channels.yaml URLs when possible."""
    key = _normalize_url_key(channel_url)
    try:
        program = load_benchmark_program(benchmark_path)
        for ch in program.channels:
            if _normalize_url_key(ch.url) == key:
                return ch.slug
    except FileNotFoundError:
        pass

    handle_match = re.search(r"@([\w.-]+)", channel_url, re.I)
    if handle_match:
        return _handle_to_slug(handle_match.group(1))

    channel_match = re.search(r"/channel/([\w-]+)", channel_url, re.I)
    if channel_match:
        return _handle_to_slug(channel_match.group(1))

    tail = channel_url.rstrip("/").split("/")[-1] or "channel"
    return slugify(tail).replace("-", "_")

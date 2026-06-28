"""Shared helpers for corpus batch scripts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from assembler.slug import resolve_channel_slug

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass
class QueueEntry:
    url: str
    slug: str
    niche: str
    status: str = "pending"


def load_queue(path: Path) -> tuple[dict[str, Any], list[QueueEntry]]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    pipeline = raw.get("pipeline") or {}
    entries: list[QueueEntry] = []
    for niche, items in (raw.get("queue") or {}).items():
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict) or not item.get("url"):
                continue
            url = str(item["url"]).strip()
            slug = str(item.get("slug") or resolve_channel_slug(url))
            status = str(item.get("status") or "pending")
            entries.append(QueueEntry(url=url, slug=slug, niche=niche, status=status))
    return pipeline, entries


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, default=str) + "\n")


def dir_size_bytes(path: Path) -> int:
    if not path.exists():
        return 0
    total = 0
    for p in path.rglob("*"):
        if p.is_file():
            try:
                total += p.stat().st_size
            except OSError:
                continue
    return total


def channel_download_bytes(slug: str) -> int:
    return dir_size_bytes(PROJECT_ROOT / "artifacts" / "channels" / slug / "downloads")


def total_batch_download_bytes() -> int:
    base = PROJECT_ROOT / "artifacts" / "channels"
    if not base.exists():
        return 0
    return sum(channel_download_bytes(d.name) for d in base.iterdir() if d.is_dir())


def count_videos_on_disk(slug: str) -> int:
    dls = PROJECT_ROOT / "artifacts" / "channels" / slug / "downloads"
    if not dls.exists():
        return 0
    return sum(1 for d in dls.iterdir() if d.is_dir() and (d / "video.mp4").exists())


def mvp_exists(slug: str) -> bool:
    return (PROJECT_ROOT / "reports" / slug / "mvp_profile.json").exists()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

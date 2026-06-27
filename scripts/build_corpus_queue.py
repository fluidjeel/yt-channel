#!/usr/bin/env python3
"""Build corpus_queue.yaml from benchmark_channels.yaml + optional discovery cache."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from assembler.slug import resolve_channel_slug

NICHE_MAP = {
    "direct_competitors": "emotional_healing",
    "larger_channels": "quote_channels",
    "outlier_channels": "faceless_storytelling",
}

COMPLETE = {"whisprs_yt", "soulxsigh", "dark_poetry_hub", "soulful_lines", "the_faceless_storyteller"}


def _from_benchmark() -> dict[str, list[dict]]:
    path = PROJECT_ROOT / "benchmark_channels.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    buckets: dict[str, list[dict]] = {
        "emotional_healing": [],
        "quote_channels": [],
        "self_improvement": [],
        "faceless_storytelling": [],
    }
    seen: set[str] = set()
    for group, items in (data.get("channels") or {}).items():
        niche = NICHE_MAP.get(group, "emotional_healing")
        for ch in items:
            url = ch.get("url", "").strip()
            if not url:
                continue
            slug = ch.get("slug") or resolve_channel_slug(url)
            if slug in seen:
                continue
            seen.add(slug)
            entry: dict = {"slug": slug, "url": url}
            if slug in COMPLETE or (PROJECT_ROOT / "reports" / slug / "mvp_profile.json").exists():
                entry["status"] = "complete"
            buckets[niche].append(entry)
    return buckets


def _from_discovery_cache(buckets: dict[str, list[dict]], limit: int = 40) -> None:
    cache = PROJECT_ROOT / "artifacts" / "competitor_discovery" / "candidates.json"
    if not cache.exists():
        return
    try:
        candidates = json.loads(cache.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return
    seen = {e["slug"] for items in buckets.values() for e in items}
    for row in candidates[:limit]:
        url = row.get("channel_url") or row.get("url") or ""
        if not url:
            continue
        slug = resolve_channel_slug(url)
        if slug in seen:
            continue
        seen.add(slug)
        niche = row.get("niche") or "self_improvement"
        if niche not in buckets:
            niche = "self_improvement"
        buckets[niche].append({"slug": slug, "url": url})


def main() -> int:
    buckets = _from_benchmark()
    _from_discovery_cache(buckets)
    out = {
        "pipeline": {
            "top_n_download": 12,
            "top_n_report": 8,
            "max_videos_discover": 60,
            "whisper_model": "tiny",
            "run_advanced_visual": True,
            "run_comment_intelligence": True,
            "run_bible_synthesis": False,
        },
        "target_counts": {
            "emotional_healing": 25,
            "quote_channels": 25,
            "self_improvement": 25,
            "faceless_storytelling": 25,
        },
        "queue": buckets,
    }
    path = PROJECT_ROOT / "corpus_queue.yaml"
    path.write_text(yaml.dump(out, sort_keys=False, default_flow_style=False), encoding="utf-8")
    total = sum(len(v) for v in buckets.values())
    print(f"Wrote {path} ({total} channels)")
    for niche, items in buckets.items():
        pending = sum(1 for i in items if i.get("status") != "complete")
        print(f"  {niche}: {len(items)} total, {pending} pending")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

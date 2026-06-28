#!/usr/bin/env python3
"""
Phase A — Download batch: discover, rank, download top N per channel (cookie window).

Stops when max_batch_gb is reached. Analysis is separate (corpus_analyze.py).

Usage:
  python scripts/corpus_download.py --queue corpus_batch.yaml
  python scripts/corpus_download.py --queue corpus_batch.yaml --limit 2
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
import traceback
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from channel_analyzer.benchmark.config import apply_pipeline_overrides, channel_config
from channel_analyzer.config import Config, configure_ffmpeg_env
from channel_analyzer.pipeline import Step, run_pipeline
from channel_analyzer.utils import setup_logging
from scripts.corpus_common import (
    QueueEntry,
    append_jsonl,
    channel_download_bytes,
    count_videos_on_disk,
    load_queue,
    total_batch_download_bytes,
    utc_now,
)

logger = logging.getLogger(__name__)

DOWNLOAD_LOG = PROJECT_ROOT / "data" / "corpus" / "download_log.jsonl"


def _batch_gb_cap(pipeline: dict[str, Any]) -> float | None:
    gb = pipeline.get("max_batch_gb")
    return float(gb) if gb is not None else None


def _bytes_budget_remaining(pipeline: dict[str, Any]) -> float | None:
    cap = _batch_gb_cap(pipeline)
    if cap is None:
        return None
    used = total_batch_download_bytes()
    return max(0.0, cap * (1024**3) - used)


def download_one(
    entry: QueueEntry,
    pipeline: dict[str, Any],
    base: Config,
) -> dict[str, Any]:
    t0 = time.monotonic()
    record: dict[str, Any] = {
        "phase": "download",
        "slug": entry.slug,
        "url": entry.url,
        "niche": entry.niche,
        "started_at": utc_now(),
    }
    cfg = channel_config(entry.slug, base)
    cfg = apply_pipeline_overrides(cfg, pipeline)
    cfg.ensure_dirs()

    before = count_videos_on_disk(entry.slug)
    errors: list[str] = []

    try:
        run_pipeline(entry.url, cfg, Step.DISCOVERY, Step.PERFORMANCE)
    except Exception as exc:
        errors.append(f"discover: {exc}")
        logger.exception("Discovery failed for %s", entry.slug)

    budget = _bytes_budget_remaining(pipeline)
    if budget is not None and budget <= 0:
        errors.append("batch_gb_cap_reached_before_download")
    else:
        try:
            run_pipeline(entry.url, cfg, Step.DOWNLOAD, Step.DOWNLOAD)
        except Exception as exc:
            errors.append(f"download: {exc}")
            logger.exception("Download failed for %s", entry.slug)

    after = count_videos_on_disk(entry.slug)
    added = max(0, after - before)
    bytes_now = channel_download_bytes(entry.slug)

    record.update(
        {
            "status": "complete" if after > 0 and not errors else ("partial" if after > 0 else "failed"),
            "videos_on_disk": after,
            "videos_added": added,
            "download_bytes": bytes_now,
            "errors": errors,
            "duration_sec": round(time.monotonic() - t0, 1),
            "finished_at": utc_now(),
        }
    )
    return record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Corpus download batch (Phase A)")
    parser.add_argument("--queue", type=Path, default=PROJECT_ROOT / "corpus_batch.yaml")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--slug", type=str, help="Run single channel slug only")
    parser.add_argument("--skip-complete", action="store_true", help="Skip if top_n videos already on disk")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    setup_logging(logging.DEBUG if args.verbose else logging.INFO)
    configure_ffmpeg_env()

    if not args.queue.exists():
        logger.error("Queue not found: %s", args.queue)
        return 1

    pipeline, entries = load_queue(args.queue)
    if args.slug:
        entries = [e for e in entries if e.slug == args.slug]
        if not entries:
            logger.error("Slug not in queue: %s", args.slug)
            return 1
    target_n = int(pipeline.get("top_n_download") or 5)
    if args.limit > 0:
        entries = entries[: args.limit]

    cap_gb = _batch_gb_cap(pipeline)
    logger.info(
        "Download batch: %d channel(s), top_n=%d, max_batch_gb=%s",
        len(entries),
        target_n,
        cap_gb,
    )

    base = Config.from_yaml()
    stopped_for_cap = False

    for i, entry in enumerate(entries, 1):
        budget = _bytes_budget_remaining(pipeline)
        if budget is not None and budget <= 0:
            logger.warning("Batch GB cap reached (%.1f GB); stopping download phase", cap_gb)
            stopped_for_cap = True
            break

        if args.skip_complete and count_videos_on_disk(entry.slug) >= target_n:
            logger.info("[%d/%d] skip %s — already has %d videos", i, len(entries), entry.slug, target_n)
            continue

        logger.info("[%d/%d] download %s", i, len(entries), entry.slug)
        try:
            record = download_one(entry, pipeline, base)
        except Exception:
            record = {
                "phase": "download",
                "slug": entry.slug,
                "status": "failed",
                "errors": [traceback.format_exc()],
            }
        append_jsonl(DOWNLOAD_LOG, record)
        print(json.dumps(record, indent=2))

    used_gb = total_batch_download_bytes() / (1024**3)
    print(f"\nDownload phase done. On-disk batch: {used_gb:.2f} GB. Log: {DOWNLOAD_LOG}")
    if stopped_for_cap:
        print("(Stopped early: max_batch_gb reached)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

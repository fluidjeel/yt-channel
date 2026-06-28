#!/usr/bin/env python3
"""
Phase B — Analyze from disk: pipeline steps 4–11 + assembler (no YouTube cookies).

Run after corpus_download.py. Processes channels that have video.mp4 on disk.

Usage:
  python scripts/corpus_analyze.py --queue corpus_batch.yaml
  python scripts/corpus_analyze.py --queue corpus_batch.yaml --purge-artifacts
"""

from __future__ import annotations

import argparse
import json
import logging
import shutil
import sys
import time
import traceback
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from channel_analyzer.advanced_visual_analyzer import run_advanced_visual_analysis
from channel_analyzer.benchmark.config import apply_pipeline_overrides, channel_config
from channel_analyzer.comment_intelligence import run_comment_intelligence
from channel_analyzer.config import Config, configure_ffmpeg_env
from channel_analyzer.pipeline import Step, run_pipeline
from channel_analyzer.utils import setup_logging
from assembler.assemble import write_mvp_profile
from assembler.report_renderer import write_channel_report
from scripts.corpus_common import (
    QueueEntry,
    append_jsonl,
    count_videos_on_disk,
    load_queue,
    mvp_exists,
    utc_now,
)

logger = logging.getLogger(__name__)

ANALYZE_LOG = PROJECT_ROOT / "data" / "corpus" / "analyze_log.jsonl"

_PURGE_DIRS = (
    "downloads",
    "top_frames",
    "advanced_visual_cache",
    "_frames_cache",
    "comments_cache",
)


def _purge(cfg: Config) -> list[str]:
    removed: list[str] = []
    for sub in _PURGE_DIRS:
        path = cfg.artifacts_dir / sub
        if path.exists():
            shutil.rmtree(path)
            removed.append(sub)
    return removed


def analyze_one(
    entry: QueueEntry,
    pipeline: dict[str, Any],
    base: Config,
    *,
    purge: bool = False,
) -> dict[str, Any]:
    t0 = time.monotonic()
    record: dict[str, Any] = {
        "phase": "analyze",
        "slug": entry.slug,
        "url": entry.url,
        "niche": entry.niche,
        "started_at": utc_now(),
        "videos_on_disk": count_videos_on_disk(entry.slug),
    }

    if record["videos_on_disk"] == 0:
        record.update(
            {
                "status": "skipped",
                "pipeline_status": "failed",
                "errors": ["no_downloads_on_disk"],
                "duration_sec": 0,
                "finished_at": utc_now(),
            }
        )
        return record

    cfg = channel_config(entry.slug, base)
    cfg = apply_pipeline_overrides(cfg, pipeline)
    cfg.ensure_dirs()
    errors: list[str] = []

    try:
        run_pipeline(entry.url, cfg, Step.AUDIO, Step.BONUS)
    except Exception as exc:
        errors.append(f"pipeline: {exc}")
        logger.exception("Analysis pipeline failed for %s", entry.slug)

    if pipeline.get("run_advanced_visual", False):
        try:
            run_advanced_visual_analysis(config=cfg)
        except Exception as exc:
            errors.append(f"advanced_visual: {exc}")

    if pipeline.get("run_comment_intelligence", False):
        try:
            run_comment_intelligence(config=cfg)
        except Exception as exc:
            errors.append(f"comments: {exc}")

    mvp_ok = report_ok = False
    try:
        write_mvp_profile(entry.slug, channel_url=entry.url)
        mvp_ok = True
        write_channel_report(entry.slug)
        report_ok = True
    except Exception as exc:
        errors.append(f"assembler: {exc}")
        logger.exception("Assembler failed for %s", entry.slug)

    pipeline_status = "partial" if errors else "full"
    if not mvp_ok:
        pipeline_status = "failed"

    purged: list[str] = []
    if purge:
        try:
            purged = _purge(cfg)
        except Exception as exc:
            errors.append(f"purge: {exc}")

    record.update(
        {
            "status": "complete" if mvp_ok else "failed",
            "pipeline_status": pipeline_status,
            "mvp_profile": mvp_ok,
            "channel_report": report_ok,
            "errors": errors,
            "purged_artifacts": purged,
            "duration_sec": round(time.monotonic() - t0, 1),
            "finished_at": utc_now(),
        }
    )
    return record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Corpus analyze batch (Phase B, offline)")
    parser.add_argument("--queue", type=Path, default=PROJECT_ROOT / "corpus_batch.yaml")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--slug", type=str, help="Analyze single channel slug only")
    parser.add_argument("--force", action="store_true", help="Re-analyze even if mvp_profile exists")
    parser.add_argument("--purge-artifacts", action="store_true")
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
    purge = args.purge_artifacts or bool(pipeline.get("purge_artifacts_after_channel"))

    filtered: list[QueueEntry] = []
    for entry in entries:
        if count_videos_on_disk(entry.slug) == 0:
            continue
        if not args.force and mvp_exists(entry.slug):
            continue
        filtered.append(entry)
    entries = filtered

    if args.limit > 0:
        entries = entries[: args.limit]

    logger.info("Analyze batch: %d channel(s), purge=%s", len(entries), purge)
    if not entries:
        print("Nothing to analyze (no downloads or all MVP profiles exist).")
        return 0

    base = Config.from_yaml()
    ok = fail = 0

    for i, entry in enumerate(entries, 1):
        logger.info("[%d/%d] analyze %s (%d videos on disk)", i, len(entries), entry.slug, count_videos_on_disk(entry.slug))
        try:
            record = analyze_one(entry, pipeline, base, purge=purge)
        except Exception:
            record = {
                "phase": "analyze",
                "slug": entry.slug,
                "status": "failed",
                "errors": [traceback.format_exc()],
            }
        append_jsonl(ANALYZE_LOG, record)
        if record.get("status") == "complete":
            ok += 1
        else:
            fail += 1
        print(json.dumps(record, indent=2))

    print(f"\nAnalyze phase done: {ok} ok, {fail} failed. Log: {ANALYZE_LOG}")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

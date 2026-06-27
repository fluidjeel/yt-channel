#!/usr/bin/env python3
"""
Corpus Sprint — batch URL → pipeline → MVP profile → archive.

No new analyzers. No LLM in assembler path. Resumes on restart.

Usage:
  python scripts/corpus_sprint.py --queue corpus_queue.yaml
  python scripts/corpus_sprint.py --queue corpus_queue.yaml --niche emotional_healing
  python scripts/corpus_sprint.py --queue corpus_queue.yaml --limit 5 --dry-run
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from channel_analyzer.advanced_visual_analyzer import run_advanced_visual_analysis
from channel_analyzer.benchmark.config import apply_pipeline_overrides, channel_config
from channel_analyzer.bible_synthesizer import run_bible_synthesis
from channel_analyzer.comment_intelligence import run_comment_intelligence
from channel_analyzer.config import Config, configure_ffmpeg_env
from channel_analyzer.pipeline import Step, run_pipeline
from channel_analyzer.utils import setup_logging
from assembler.assemble import write_mvp_profile
from assembler.report_renderer import write_channel_report
from assembler.slug import resolve_channel_slug

logger = logging.getLogger(__name__)

CORPUS_LOG = PROJECT_ROOT / "data" / "corpus" / "run_log.jsonl"


@dataclass
class QueueEntry:
    url: str
    slug: str
    niche: str
    status: str = "pending"


def _load_queue(path: Path) -> tuple[dict[str, Any], list[QueueEntry]]:
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


def _append_log(record: dict[str, Any]) -> None:
    CORPUS_LOG.parent.mkdir(parents=True, exist_ok=True)
    with CORPUS_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, default=str) + "\n")


def _write_meta(cfg: Config, slug: str, niche: str, status: str) -> None:
    meta = cfg.reports_dir / "benchmark_meta.json"
    meta.write_text(
        json.dumps(
            {
                "slug": slug,
                "niche": niche,
                "status": status,
                "corpus_sprint": True,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def _is_complete(slug: str) -> bool:
    mvp = PROJECT_ROOT / "reports" / slug / "mvp_profile.json"
    return mvp.exists()


def run_one(
    entry: QueueEntry,
    pipeline_cfg: dict[str, Any],
    base: Config,
    *,
    dry_run: bool = False,
) -> dict[str, Any]:
    started = datetime.now(timezone.utc).isoformat()
    t0 = time.monotonic()
    record: dict[str, Any] = {
        "slug": entry.slug,
        "url": entry.url,
        "niche": entry.niche,
        "started_at": started,
        "status": "running",
    }

    if dry_run:
        record["status"] = "dry_run"
        return record

    cfg = channel_config(entry.slug, base)
    cfg = apply_pipeline_overrides(cfg, pipeline_cfg)
    cfg.ensure_dirs()

    errors: list[str] = []

    try:
        run_pipeline(entry.url, cfg, Step.DISCOVERY, Step.BONUS)
    except Exception as exc:
        errors.append(f"pipeline: {exc}")
        logger.exception("Pipeline failed for %s", entry.slug)

    if pipeline_cfg.get("run_advanced_visual", True):
        try:
            run_advanced_visual_analysis(config=cfg)
        except Exception as exc:
            errors.append(f"advanced_visual: {exc}")
            logger.warning("Advanced visual failed for %s: %s", entry.slug, exc)

    if pipeline_cfg.get("run_comment_intelligence", True):
        try:
            run_comment_intelligence(config=cfg)
        except Exception as exc:
            errors.append(f"comments: {exc}")
            logger.warning("Comments failed for %s: %s", entry.slug, exc)

    if pipeline_cfg.get("run_bible_synthesis", False):
        try:
            run_bible_synthesis(config=cfg, provider="openai")
        except Exception as exc:
            errors.append(f"bibles: {exc}")
            logger.warning("Bible synthesis failed for %s: %s", entry.slug, exc)

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
    _write_meta(cfg, entry.slug, entry.niche, pipeline_status)

    record.update(
        {
            "status": "complete" if mvp_ok else "failed",
            "pipeline_status": pipeline_status,
            "mvp_profile": mvp_ok,
            "channel_report": report_ok,
            "errors": errors,
            "duration_sec": round(time.monotonic() - t0, 1),
            "finished_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    return record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Corpus Sprint batch runner")
    parser.add_argument("--queue", type=Path, default=PROJECT_ROOT / "corpus_queue.yaml")
    parser.add_argument("--niche", type=str, help="Run only one niche bucket")
    parser.add_argument("--limit", type=int, default=0, help="Max channels this run (0=all)")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-run even if mvp_profile.json exists or status is complete",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    setup_logging(logging.DEBUG if args.verbose else logging.INFO)
    configure_ffmpeg_env()

    if not args.queue.exists():
        logger.error("Queue file not found: %s", args.queue)
        return 1

    pipeline_cfg, entries = _load_queue(args.queue)
    if args.niche:
        entries = [e for e in entries if e.niche == args.niche]

    if not args.force:
        entries = [e for e in entries if e.status != "complete" and not _is_complete(e.slug)]

    if args.limit > 0:
        entries = entries[: args.limit]

    logger.info("Corpus sprint: %d channel(s) queued", len(entries))
    if not entries:
        print("Nothing to run.")
        return 0

    base = Config.from_yaml()
    ok = fail = 0

    for i, entry in enumerate(entries, 1):
        logger.info("[%d/%d] %s (%s)", i, len(entries), entry.slug, entry.niche)
        try:
            record = run_one(entry, pipeline_cfg, base, dry_run=args.dry_run)
        except Exception:
            record = {
                "slug": entry.slug,
                "url": entry.url,
                "niche": entry.niche,
                "status": "failed",
                "errors": [traceback.format_exc()],
            }
        if not args.dry_run:
            _append_log(record)
        if record.get("status") in ("complete", "dry_run"):
            ok += 1
        else:
            fail += 1
        print(json.dumps(record, indent=2))

    print(f"\nCorpus sprint done: {ok} ok, {fail} failed. Log: {CORPUS_LOG}")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

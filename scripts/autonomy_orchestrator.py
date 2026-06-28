#!/usr/bin/env python3
"""
Unattended orchestrator for Oracle VM — safe retries, no duplicate tmux, resource guard.

Usage (on VM or via SSH):
  python scripts/autonomy_orchestrator.py --queue corpus_batch.yaml
"""

from __future__ import annotations

import argparse
import json
import logging
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.corpus_common import (
    count_videos_on_disk,
    load_queue,
    mvp_exists,
    utc_now,
)
from scripts.vm_guard import assess

logger = logging.getLogger(__name__)

STATUS_PATH = PROJECT_ROOT / "data" / "autonomy" / "status.json"
DOWNLOAD_LOG = PROJECT_ROOT / "data" / "corpus" / "download_log.jsonl"
ANALYZE_LOG = PROJECT_ROOT / "data" / "corpus" / "analyze_log.jsonl"


def _tmux_running(session: str) -> bool:
    r = subprocess.run(["tmux", "has-session", "-t", session], capture_output=True)
    return r.returncode == 0


def _last_log_by_slug(path: Path) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
            slug = rec.get("slug")
            if slug:
                out[str(slug)] = rec
        except json.JSONDecodeError:
            continue
    return out


def _download_runs_for_slug(slug: str, *, tail: int = 5) -> list[dict[str, Any]]:
    if not DOWNLOAD_LOG.exists():
        return []
    runs: list[dict[str, Any]] = []
    for line in DOWNLOAD_LOG.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if rec.get("slug") == slug and rec.get("phase") == "download":
            runs.append(rec)
    return runs[-tail:]


def _download_stuck(slug: str, target: int) -> bool:
    """Skip retry when recent runs add nothing (do not block analyze)."""
    runs = _download_runs_for_slug(slug, tail=3)
    if len(runs) < 2:
        return False
    recent = runs[-2:]
    if all(int(r.get("videos_added") or 0) == 0 for r in recent):
        on_disk = int(recent[-1].get("videos_on_disk") or 0)
        if 0 < on_disk < target:
            return True
    return False


def _cleanup_invalid_downloads(slug: str) -> int:
    """Remove download dirs without video.mp4 (partial/failed yt-dlp)."""
    dls = PROJECT_ROOT / "artifacts" / "channels" / slug / "downloads"
    if not dls.exists():
        return 0
    removed = 0
    for d in list(dls.iterdir()):
        if not d.is_dir():
            continue
        if (d / "video.mp4").exists():
            continue
        shutil.rmtree(d, ignore_errors=True)
        removed += 1
    return removed


def _run_py(script: str, *args: str) -> int:
    cmd = [sys.executable, str(PROJECT_ROOT / "scripts" / script), *args]
    logger.info("Running: %s", " ".join(cmd))
    return subprocess.call(cmd)


def orchestrate(queue_path: Path, *, dry_run: bool = False) -> dict[str, Any]:
    guard = assess()
    pipeline, entries = load_queue(queue_path)
    target = int(pipeline.get("top_n_download") or 5)

    status: dict[str, Any] = {
        "checked_at": utc_now(),
        "queue": queue_path.name,
        "guard": guard,
        "tmux_corpus_batch": _tmux_running("corpus-batch"),
        "action": "idle",
        "work_done": [],
    }

    if not guard["safe"]:
        status["action"] = "paused_resource_guard"
        _write_status(status)
        return status

    if status["tmux_corpus_batch"]:
        status["action"] = "batch_already_running"
        _write_status(status)
        return status

    dl_last = _last_log_by_slug(DOWNLOAD_LOG)
    an_last = _last_log_by_slug(ANALYZE_LOG)

    download_queue: list[str] = []
    analyze_queue: list[str] = []

    for entry in entries:
        n = count_videos_on_disk(entry.slug)
        cleaned = _cleanup_invalid_downloads(entry.slug)
        if cleaned:
            status.setdefault("cleaned", {})[entry.slug] = cleaned
            n = count_videos_on_disk(entry.slug)

        if n < target:
            if not _download_stuck(entry.slug, target):
                download_queue.append(entry.slug)
            else:
                status.setdefault("download_skipped_stuck", []).append(entry.slug)
        elif n >= target:
            dl = dl_last.get(entry.slug, {})
            an = an_last.get(entry.slug, {})
            dl_ts = dl.get("finished_at") or ""
            an_ts = an.get("finished_at") or ""
            if not mvp_exists(entry.slug) or an.get("pipeline_status") != "full":
                analyze_queue.append(entry.slug)
            elif dl_ts > an_ts:
                analyze_queue.append(entry.slug)

    status["download_queue"] = download_queue
    status["analyze_queue"] = analyze_queue

    if dry_run:
        status["action"] = "dry_run"
        _write_status(status)
        return status

    # Analyze ready channels before retrying partial downloads (unattended priority).
    if analyze_queue:
        slug = analyze_queue[0]
        status["action"] = f"analyze_{slug}"
        if not dry_run:
            code = _run_py(
                "corpus_analyze.py",
                "--queue",
                str(queue_path),
                "--slug",
                slug,
                "--force",
            )
            status["work_done"].append({"analyze": slug, "exit_code": code})
        _write_status(status)
        return status

    if download_queue:
        slug = download_queue[0]
        status["action"] = f"download_{slug}"
        if not dry_run:
            code = _run_py(
                "corpus_download.py",
                "--queue",
                str(queue_path),
                "--slug",
                slug,
            )
            status["work_done"].append({"download": slug, "exit_code": code})
        _write_status(status)
        return status

    status["action"] = "nothing_pending"
    _run_py("corpus_health.py", "--queue", str(queue_path))
    _write_status(status)
    return status


def _write_status(status: dict[str, Any]) -> None:
    STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATUS_PATH.write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Autonomy orchestrator (Oracle)")
    parser.add_argument("--queue", type=Path, default=PROJECT_ROOT / "corpus_batch.yaml")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)
    orchestrate(args.queue, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

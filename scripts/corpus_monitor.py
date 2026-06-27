#!/usr/bin/env python3
"""
Corpus sprint monitor — snapshot progress, detect cookie/bot failures, log status.

Usage:
  python scripts/corpus_monitor.py
  python scripts/corpus_monitor.py --json
  python scripts/corpus_monitor.py --watch   # loop every N minutes (default 30)

Cron (Oracle VM):
  */30 * * * * cd /home/ubuntu/yt-channel && .venv/bin/python scripts/corpus_monitor.py >> /home/ubuntu/logs/corpus_watch.log 2>&1
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUN_LOG = PROJECT_ROOT / "data" / "corpus" / "run_log.jsonl"
STATUS_FILE = PROJECT_ROOT / "data" / "corpus" / "last_status.json"
SPRINT_LOG = Path.home() / "logs" / "corpus_sprint.log"


def _tmux_running(session: str = "corpus") -> bool:
    try:
        out = subprocess.run(
            ["tmux", "has-session", "-t", session],
            capture_output=True,
            timeout=5,
        )
        return out.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _tail_log(path: Path, lines: int = 40) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    return "\n".join(text.splitlines()[-lines:])


def _load_run_log() -> list[dict]:
    if not RUN_LOG.exists():
        return []
    records = []
    for line in RUN_LOG.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def collect_status(queue_path: Path | None = None) -> dict:
    import yaml

    queue_path = queue_path or PROJECT_ROOT / "corpus_queue_phase1.yaml"
    queue_total = 0
    phase = "unknown"
    if queue_path.exists():
        q = yaml.safe_load(queue_path.read_text(encoding="utf-8")) or {}
        queue_total = sum(len(v) for v in (q.get("queue") or {}).values())
        phase = q.get("phase") or queue_path.name

    profiles = list((PROJECT_ROOT / "reports").glob("*/mvp_profile.json"))
    records = _load_run_log()
    full = sum(1 for r in records if r.get("pipeline_status") == "full")
    partial = sum(1 for r in records if r.get("pipeline_status") == "partial")
    failed = sum(1 for r in records if r.get("status") == "failed")

    tail = _tail_log(SPRINT_LOG)
    bot_hits = tail.lower().count("sign in to confirm") + tail.lower().count("not a bot")

    last_slug = records[-1].get("slug") if records else None
    last_status = records[-1].get("status") if records else None

    tmux = _tmux_running()
    sprint_done = queue_total > 0 and len(records) >= queue_total and not tmux

    status = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "phase": phase,
        "queue_file": queue_path.name,
        "queue_total": queue_total,
        "logged_runs": len(records),
        "mvp_profiles": len(profiles),
        "pipeline_full": full,
        "pipeline_partial": partial,
        "pipeline_failed": failed,
        "tmux_corpus_running": tmux,
        "sprint_likely_complete": sprint_done,
        "last_completed_slug": last_slug,
        "last_run_status": last_status,
        "recent_bot_errors_in_tail": bot_hits,
        "cookies_may_be_stale": bot_hits >= 2,
        "action": _recommend_action(tmux, sprint_done, bot_hits, queue_total, len(records)),
    }
    return status


def _recommend_action(
    tmux: bool, done: bool, bot_hits: int, queue_total: int, logged: int
) -> str:
    if bot_hits >= 2:
        return "refresh_youtube_cookies_and_restart"
    if done:
        return "run_analyze_corpus_then_consider_phase2"
    if not tmux and logged < queue_total:
        return "tmux_session_died_restart_start_corpus_tmux_sh"
    if tmux:
        return "ok_running"
    return "idle"


def render_text(s: dict) -> str:
    lines = [
        f"[{s['checked_at']}] corpus monitor",
        f"  phase: {s['phase']}",
        f"  progress: {s['logged_runs']}/{s['queue_total']} logged | {s['mvp_profiles']} mvp profiles",
        f"  pipeline: full={s['pipeline_full']} partial={s['pipeline_partial']} failed={s['pipeline_failed']}",
        f"  tmux corpus: {'running' if s['tmux_corpus_running'] else 'stopped'}",
        f"  last: {s['last_completed_slug']} ({s['last_run_status']})",
        f"  bot errors in log tail: {s['recent_bot_errors_in_tail']}",
        f"  action: {s['action']}",
    ]
    if s["sprint_likely_complete"]:
        lines.append("  >>> Phase batch likely complete — run analyze_corpus.py")
    if s["cookies_may_be_stale"]:
        lines.append("  >>> Cookies may be stale — paste fresh cookies")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Monitor corpus sprint progress")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--queue", type=Path, default=None)
    parser.add_argument("--watch", action="store_true", help="Loop forever")
    parser.add_argument("--interval-min", type=int, default=30)
    args = parser.parse_args(argv)

    def once() -> dict:
        s = collect_status(args.queue)
        STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATUS_FILE.write_text(json.dumps(s, indent=2) + "\n", encoding="utf-8")
        if args.json:
            print(json.dumps(s, indent=2))
        else:
            print(render_text(s))
        return s

    if not args.watch:
        once()
        return 0

    while True:
        once()
        print(f"\n--- sleeping {args.interval_min} min ---\n")
        time.sleep(args.interval_min * 60)


if __name__ == "__main__":
    raise SystemExit(main())

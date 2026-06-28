#!/usr/bin/env python3
"""
Corpus + VM health snapshot for unattended batch runs.

Writes:
  data/corpus/health.json
  reports/corpus_health.md

Usage:
  python scripts/corpus_health.py
  python scripts/corpus_health.py --watch --interval-min 15
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.corpus_common import (
    count_videos_on_disk,
    load_queue,
    mvp_exists,
    total_batch_download_bytes,
)

HEALTH_JSON = PROJECT_ROOT / "data" / "corpus" / "health.json"
HEALTH_MD = PROJECT_ROOT / "reports" / "corpus_health.md"
DOWNLOAD_LOG = PROJECT_ROOT / "data" / "corpus" / "download_log.jsonl"
ANALYZE_LOG = PROJECT_ROOT / "data" / "corpus" / "analyze_log.jsonl"


def _read_jsonl_tail(path: Path, n: int = 5) -> list[dict]:
    if not path.exists():
        return []
    lines = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    out = []
    for ln in lines[-n:]:
        try:
            out.append(json.loads(ln))
        except json.JSONDecodeError:
            continue
    return out


def _tmux_sessions() -> list[str]:
    try:
        r = subprocess.run(["tmux", "ls"], capture_output=True, text=True, timeout=5)
        if r.returncode != 0:
            return []
        return [ln.split(":")[0] for ln in r.stdout.splitlines() if ln.strip()]
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []


def _load_mem() -> dict:
    info: dict = {}
    try:
        with open("/proc/meminfo", encoding="utf-8") as f:
            for line in f:
                if line.startswith(("MemTotal:", "MemAvailable:", "SwapTotal:", "SwapFree:")):
                    k, v = line.split(":")
                    info[k.strip()] = int(v.split()[0])  # kB
        if "MemTotal" in info and "MemAvailable" in info:
            total = info["MemTotal"]
            avail = info["MemAvailable"]
            info["mem_used_pct"] = round(100 * (1 - avail / total), 1) if total else 0
    except OSError:
        pass
    return info


def _load_loadavg() -> list[float]:
    try:
        parts = open("/proc/loadavg", encoding="utf-8").read().split()[:3]
        return [float(x) for x in parts]
    except (OSError, ValueError):
        return []


def _disk_usage(path: Path) -> dict:
    try:
        u = os.statvfs(path)
        total = u.f_frsize * u.f_blocks
        free = u.f_frsize * u.f_bavail
        used = total - free
        return {
            "path": str(path),
            "total_gb": round(total / (1024**3), 2),
            "used_gb": round(used / (1024**3), 2),
            "free_gb": round(free / (1024**3), 2),
            "used_pct": round(100 * used / total, 1) if total else 0,
        }
    except OSError:
        return {}


def collect_health(queue_path: Path) -> dict:
    pipeline, entries = load_queue(queue_path)
    slugs = [e.slug for e in entries]

    dl_records = _read_jsonl_tail(DOWNLOAD_LOG, 20)
    an_records = _read_jsonl_tail(ANALYZE_LOG, 20)

    per_channel = []
    for slug in slugs:
        per_channel.append(
            {
                "slug": slug,
                "videos_on_disk": count_videos_on_disk(slug),
                "mvp_profile": mvp_exists(slug),
            }
        )

    batch_gb = round(total_batch_download_bytes() / (1024**3), 2)
    cap_gb = pipeline.get("max_batch_gb")

    mem = _load_mem()
    disk = _disk_usage(PROJECT_ROOT)
    sessions = _tmux_sessions()

    download_done = sum(1 for s in slugs if count_videos_on_disk(s) >= int(pipeline.get("top_n_download") or 5))
    analyze_done = sum(1 for s in slugs if mvp_exists(s))

    return {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "queue": queue_path.name,
        "phase": pipeline.get("phase") or "split_batch",
        "max_batch_gb": cap_gb,
        "batch_download_gb": batch_gb,
        "channels_total": len(slugs),
        "channels_downloaded": download_done,
        "channels_analyzed": analyze_done,
        "per_channel": per_channel,
        "tmux_sessions": sessions,
        "vm": {
            "disk_root": disk,
            "mem": mem,
            "loadavg_1_5_15": _load_loadavg(),
        },
        "last_download_runs": dl_records[-3:],
        "last_analyze_runs": an_records[-3:],
        "action": _recommend(sessions, batch_gb, cap_gb, download_done, analyze_done, len(slugs), disk),
    }


def _recommend(
    sessions: list[str],
    batch_gb: float,
    cap_gb: float | None,
    dl_done: int,
    an_done: int,
    total: int,
    disk: dict,
) -> str:
    if disk.get("used_pct", 0) > 90:
        return "disk_critical"
    if cap_gb and batch_gb >= float(cap_gb) * 0.95:
        return "batch_gb_near_cap_run_analyze"
    if "corpus-batch" in sessions or "corpus" in sessions:
        return "batch_running"
    if dl_done >= total and an_done < total:
        return "run_corpus_analyze"
    if an_done >= total:
        return "batch_complete_review_reports"
    if dl_done < total:
        return "run_or_resume_corpus_download"
    return "idle"


def render_md(h: dict) -> str:
    vm = h.get("vm") or {}
    disk = vm.get("disk_root") or {}
    mem = vm.get("mem") or {}
    lines = [
        f"# Corpus health — {h['checked_at']}",
        "",
        "## Progress",
        f"- Queue: `{h['queue']}` ({h['channels_total']} channels)",
        f"- Downloaded (≥target): **{h['channels_downloaded']}/{h['channels_total']}**",
        f"- Analyzed (MVP): **{h['channels_analyzed']}/{h['channels_total']}**",
        f"- Batch on disk: **{h['batch_download_gb']} GB** / cap {h.get('max_batch_gb')} GB",
        f"- **Action:** `{h['action']}`",
        "",
        "## Per channel",
        "| slug | videos on disk | MVP |",
        "|------|----------------|-----|",
    ]
    for row in h.get("per_channel") or []:
        lines.append(
            f"| {row['slug']} | {row['videos_on_disk']} | {'yes' if row['mvp_profile'] else 'no'} |"
        )
    lines.extend(
        [
            "",
            "## VM",
            f"- Disk `/`: {disk.get('used_gb')} / {disk.get('total_gb')} GB ({disk.get('used_pct')}% used, {disk.get('free_gb')} GB free)",
            f"- Memory used: {mem.get('mem_used_pct', '?')}%",
            f"- Load avg: {vm.get('loadavg_1_5_15')}",
            f"- tmux: {', '.join(h.get('tmux_sessions') or []) or '(none)'}",
            "",
        ]
    )
    if h.get("last_download_runs"):
        lines.append("## Last download runs")
        for r in h["last_download_runs"]:
            lines.append(f"- `{r.get('slug')}` status={r.get('status')} videos={r.get('videos_on_disk')} err={len(r.get('errors') or [])}")
        lines.append("")
    if h.get("last_analyze_runs"):
        lines.append("## Last analyze runs")
        for r in h["last_analyze_runs"]:
            lines.append(
                f"- `{r.get('slug')}` pipeline={r.get('pipeline_status')} dur={r.get('duration_sec')}s"
            )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Corpus + VM health report")
    parser.add_argument("--queue", type=Path, default=PROJECT_ROOT / "corpus_batch.yaml")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--watch", action="store_true")
    parser.add_argument("--interval-min", type=int, default=15)
    args = parser.parse_args(argv)

    def once() -> dict:
        h = collect_health(args.queue)
        HEALTH_JSON.parent.mkdir(parents=True, exist_ok=True)
        HEALTH_MD.parent.mkdir(parents=True, exist_ok=True)
        HEALTH_JSON.write_text(json.dumps(h, indent=2) + "\n", encoding="utf-8")
        HEALTH_MD.write_text(render_md(h), encoding="utf-8")
        if args.json:
            print(json.dumps(h, indent=2))
        else:
            print(render_md(h))
        return h

    if not args.watch:
        once()
        return 0

    while True:
        once()
        print(f"\n--- next check in {args.interval_min} min ---\n")
        time.sleep(args.interval_min * 60)


if __name__ == "__main__":
    raise SystemExit(main())

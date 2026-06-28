#!/usr/bin/env python3
"""VM resource guard — avoid starting heavy work when disk/memory/load is high."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Conservative limits for Oracle A1 (avoid OOM / disk full)
MAX_DISK_USED_PCT = 85.0
MAX_MEM_USED_PCT = 88.0
MAX_LOAD_1M = 3.5


def _disk_usage(path: Path) -> dict[str, float]:
    u = os.statvfs(path)
    total = u.f_frsize * u.f_blocks
    free = u.f_frsize * u.f_bavail
    used = total - free
    pct = (100.0 * used / total) if total else 0.0
    return {
        "total_gb": round(total / (1024**3), 2),
        "free_gb": round(free / (1024**3), 2),
        "used_pct": round(pct, 1),
    }


def _mem_usage() -> dict[str, Any]:
    info: dict[str, Any] = {}
    try:
        with open("/proc/meminfo", encoding="utf-8") as f:
            for line in f:
                if line.startswith(("MemTotal:", "MemAvailable:")):
                    k, v = line.split(":")
                    info[k.strip()] = int(v.split()[0])
        total = info.get("MemTotal", 0)
        avail = info.get("MemAvailable", 0)
        if total:
            info["mem_used_pct"] = round(100 * (1 - avail / total), 1)
    except OSError:
        pass
    return info


def _loadavg() -> list[float]:
    try:
        return [float(x) for x in open("/proc/loadavg", encoding="utf-8").read().split()[:3]]
    except (OSError, ValueError):
        return []


def assess(root: Path | None = None) -> dict[str, Any]:
    root = root or PROJECT_ROOT
    disk = _disk_usage(root)
    mem = _mem_usage()
    load = _loadavg()
    reasons: list[str] = []
    if disk["used_pct"] >= MAX_DISK_USED_PCT:
        reasons.append(f"disk_used_pct={disk['used_pct']}>={MAX_DISK_USED_PCT}")
    mem_pct = mem.get("mem_used_pct", 0)
    if mem_pct >= MAX_MEM_USED_PCT:
        reasons.append(f"mem_used_pct={mem_pct}>={MAX_MEM_USED_PCT}")
    if load and load[0] >= MAX_LOAD_1M:
        reasons.append(f"load1={load[0]}>={MAX_LOAD_1M}")
    return {
        "safe": not reasons,
        "reasons": reasons,
        "disk": disk,
        "mem": mem,
        "loadavg": load,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="VM resource guard")
    parser.add_argument("--check", action="store_true", help="Exit 0 if safe, 1 if blocked")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    result = assess()
    if args.json:
        print(json.dumps(result, indent=2))
    elif args.check:
        if result["safe"]:
            print("ok")
        else:
            print("blocked:", ", ".join(result["reasons"]))
    else:
        print(json.dumps(result, indent=2))
    if args.check:
        return 0 if result["safe"] else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

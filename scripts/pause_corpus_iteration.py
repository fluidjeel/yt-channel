#!/usr/bin/env python3
"""Stop unattended corpus batch iteration (batch 3 is final)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PAUSE_PATH = PROJECT_ROOT / "data" / "corpus" / "iteration_paused.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Pause corpus batch iteration")
    parser.add_argument("--reason", default="batch3 final — no further batches")
    parser.add_argument("--final-queue", default="corpus_batch3.yaml")
    parser.add_argument("--unpause", action="store_true")
    args = parser.parse_args(argv)

    if args.unpause:
        if PAUSE_PATH.exists():
            PAUSE_PATH.unlink()
            print(f"Removed {PAUSE_PATH}")
        else:
            print("Not paused")
        return 0

    PAUSE_PATH.parent.mkdir(parents=True, exist_ok=True)
    from scripts.corpus_common import utc_now

    payload = {
        "paused": True,
        "paused_at": utc_now(),
        "reason": args.reason,
        "final_queue": args.final_queue,
    }
    PAUSE_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {PAUSE_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

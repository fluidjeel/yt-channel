#!/usr/bin/env bash
# Periodic health snapshots while batch runs (default every 15 min).
set -euo pipefail
cd "${HOME}/yt-channel"
source .venv/bin/activate
QUEUE="${CORPUS_QUEUE:-corpus_batch.yaml}"
INTERVAL="${HEALTH_INTERVAL_MIN:-15}"
exec python scripts/corpus_health.py --queue "$QUEUE" --watch --interval-min "$INTERVAL"

#!/usr/bin/env bash
set -euo pipefail
cd /home/ubuntu/yt-channel
source .venv/bin/activate
QUEUE="${CORPUS_QUEUE:-corpus_queue_phase1.yaml}"
if [ "${CORPUS_FORCE:-1}" = "1" ]; then
  exec python scripts/corpus_sprint.py --queue "$QUEUE" --force
fi
exec python scripts/corpus_sprint.py --queue "$QUEUE"

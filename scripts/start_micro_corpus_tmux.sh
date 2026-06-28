#!/usr/bin/env bash
# Option A micro pilot: 5 videos/channel, purge media after each, no advanced visual.
set -euo pipefail
export PATH="${HOME}/.deno/bin:${PATH}"
cd "${HOME}/yt-channel"
source .venv/bin/activate
QUEUE="${CORPUS_QUEUE:-corpus_queue_micro.yaml}"
EXTRA=(--purge-artifacts)
if [ "${CORPUS_FORCE:-0}" = "1" ]; then
  EXTRA+=(--force)
fi
if [ -n "${CORPUS_LIMIT:-}" ]; then
  EXTRA+=(--limit "$CORPUS_LIMIT")
fi
exec python scripts/corpus_sprint.py --queue "$QUEUE" "${EXTRA[@]}"

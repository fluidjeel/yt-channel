#!/usr/bin/env bash
# Oracle autonomy loop — one safe work unit every 15 min (resource guard + no duplicate tmux).
set -euo pipefail
export PATH="${HOME}/.deno/bin:${PATH}"
cd "${HOME}/yt-channel"
source .venv/bin/activate
QUEUE="${CORPUS_QUEUE:-corpus_batch.yaml}"
INTERVAL="${AUTONOMY_INTERVAL_SEC:-900}"
LOG="${HOME}/logs/autonomy_watchdog.log"
mkdir -p "${HOME}/logs"

while true; do
  echo "=== $(date -Is) autonomy tick ===" >>"$LOG"
  if [ -f data/corpus/iteration_paused.json ]; then
    echo "corpus iteration paused — skipping orchestrator" >>"$LOG"
  else
    python scripts/autonomy_orchestrator.py --queue "$QUEUE" >>"$LOG" 2>&1 || true
  fi
  python scripts/corpus_health.py --queue "$QUEUE" >>"$LOG" 2>&1 || true
  sleep "$INTERVAL"
done

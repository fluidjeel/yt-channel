#!/usr/bin/env bash
# Unattended split batch: download all channels (Phase A) then analyze (Phase B).
set -euo pipefail
export PATH="${HOME}/.deno/bin:${PATH}"
cd "${HOME}/yt-channel"
source .venv/bin/activate
QUEUE="${CORPUS_QUEUE:-corpus_batch.yaml}"
LOG="${HOME}/logs/corpus_batch.log"
mkdir -p "${HOME}/logs"

exec >>"$LOG" 2>&1
echo "=== corpus batch start $(date -Is) queue=$QUEUE ==="

python scripts/corpus_download.py --queue "$QUEUE" --skip-complete

ANALYZE_EXTRA=()
if [ "${CORPUS_FORCE:-0}" = "1" ]; then
  ANALYZE_EXTRA+=(--force)
fi
echo "=== download phase done $(date -Is) ==="

python scripts/corpus_analyze.py --queue "$QUEUE" "${ANALYZE_EXTRA[@]}"
echo "=== analyze phase done $(date -Is) ==="

python scripts/corpus_health.py --queue "$QUEUE"
python scripts/analyze_corpus.py 2>/dev/null || true
echo "=== corpus batch complete $(date -Is) ==="

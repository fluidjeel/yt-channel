#!/usr/bin/env bash
# Run offline analyze for completed batch channels (long-running; use tmux).
set -euo pipefail
export PATH="${HOME}/.deno/bin:${PATH}"
cd "${HOME}/yt-channel"
source .venv/bin/activate
QUEUE="${CORPUS_QUEUE:-corpus_batch.yaml}"
mkdir -p "${HOME}/logs"

for slug in soulful_lines dark_poetry_hub; do
  echo "=== analyze $slug $(date -Is) ===" | tee -a "${HOME}/logs/corpus_analyze.log"
  python scripts/corpus_analyze.py --queue "$QUEUE" --slug "$slug" --force 2>&1 |
    tee "${HOME}/logs/corpus_analyze_${slug}.log"
done
echo "=== DONE $(date -Is) ===" >>"${HOME}/logs/corpus_analyze.log"

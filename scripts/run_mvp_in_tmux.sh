#!/usr/bin/env bash
# Run MVP profile pipeline inside tmux with logging.
# Usage: bash scripts/run_mvp_in_tmux.sh "https://www.youtube.com/@channel/shorts"
set -euo pipefail

URL="${1:?Channel URL required}"
PROJECT_DIR="${PROJECT_DIR:-$HOME/projects/yt-channel}"
SESSION="${TMUX_SESSION:-yt}"
LOG_DIR="${LOG_DIR:-$HOME/logs}"
STAMP="$(date +%Y%m%d_%H%M%S)"
LOG_FILE="$LOG_DIR/mvp_${STAMP}.log"

mkdir -p "$LOG_DIR"
cd "$PROJECT_DIR"
# shellcheck disable=SC1091
source .venv/bin/activate

if [ -f "$HOME/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  source "$HOME/.env"
  set +a
fi

CMD="cd '$PROJECT_DIR' && source .venv/bin/activate && \
  [ -f ~/.env ] && set -a && source ~/.env && set +a; \
  python main.py '$URL' --mvp-profile 2>&1 | tee '$LOG_FILE'"

if tmux has-session -t "$SESSION" 2>/dev/null; then
  tmux send-keys -t "$SESSION" "$CMD" Enter
  echo "Sent to existing tmux session '$SESSION'. Log: $LOG_FILE"
else
  tmux new-session -d -s "$SESSION" "$CMD"
  echo "Started tmux session '$SESSION'. Log: $LOG_FILE"
  echo "Attach: tmux attach -t $SESSION"
fi

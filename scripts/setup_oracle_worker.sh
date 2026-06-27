#!/usr/bin/env bash
# Reproducible Oracle VM worker setup (Ubuntu ARM64 / VM.Standard.A1.Flex).
# Usage: bash scripts/setup_oracle_worker.sh
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-$HOME/projects/yt-channel}"
REPO_URL="${REPO_URL:-https://github.com/fluidjeel/yt-channel.git}"

echo "==> System packages"
sudo apt-get update
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
  git python3-pip python3-venv ffmpeg libsndfile1 build-essential \
  tmux htop rsync

echo "==> Workspace dirs"
mkdir -p "$HOME/projects" "$HOME/data" "$HOME/logs"

echo "==> Clone or update repo at $PROJECT_DIR"
if [ -d "$PROJECT_DIR/.git" ]; then
  git -C "$PROJECT_DIR" pull --ff-only
else
  git clone "$REPO_URL" "$PROJECT_DIR"
fi
cd "$PROJECT_DIR"

echo "==> Python venv"
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -U pip wheel setuptools
# ARM64: install CPU PyTorch before whisper/sentence-transformers
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt

echo "==> API keys template (edit with nano; never commit)"
touch "$HOME/.env"
chmod 600 "$HOME/.env"
if ! grep -q "OPENAI_API_KEY" "$HOME/.env" 2>/dev/null; then
  cat >> "$HOME/.env" <<'EOF'
# Optional — MVP pipeline runs without these. Needed for LLM bible synthesis only.
# OPENAI_API_KEY=
# ANTHROPIC_API_KEY=
EOF
fi

echo "==> Dependency check"
python main.py --check-deps

echo ""
echo "Setup complete."
echo "  Project:  $PROJECT_DIR"
echo "  Logs:     $HOME/logs"
echo "  tmux:     tmux new -s yt   (detach: Ctrl+B then D)"
echo "  MVP run:  source .venv/bin/activate && python main.py \"URL\" --mvp-profile"

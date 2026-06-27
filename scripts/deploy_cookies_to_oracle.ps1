# Deploy fresh cookies/youtube.txt to Oracle VM and restart phase1 corpus sprint.
# HITL: export cookies from browser first (see docs/CORPUS_ORACLE_RUNBOOK.md).
param(
    [string]$Key = "ssh-key-2026-06-17.key",
    [string]$Host = "ubuntu@80.225.234.65"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$CookieFile = Join-Path $Root "cookies\youtube.txt"

if (-not (Test-Path $CookieFile)) {
    Write-Error "Missing $CookieFile — run scripts/convert_cookie_header.py after pasting header to cookies/raw_header.txt"
}

scp -i (Join-Path $Root $Key) $CookieFile "${Host}:~/yt-channel/cookies/youtube.txt"
ssh -i (Join-Path $Root $Key) $Host @'
cd ~/yt-channel && export PATH=$HOME/.deno/bin:$PATH
source .venv/bin/activate
yt-dlp --cookies cookies/youtube.txt -F 'https://www.youtube.com/shorts/ab3Zy4c32lw' | head -15
tmux kill-session -t corpus 2>/dev/null || true
tmux new-session -d -s corpus 'bash scripts/start_corpus_tmux.sh'
tmux ls
'@

Write-Host "Cookies deployed; corpus tmux restarted."

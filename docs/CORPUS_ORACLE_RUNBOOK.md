# Corpus Sprint — Oracle VM Runbook

**SHIPPED** worker path for phased corpus validation on Oracle (`ubuntu@80.225.234.65`).

## Prerequisites

1. SSH key: `ssh-key-2026-06-17.key` (gitignored)
2. **Fresh YouTube cookies** in Netscape format at `cookies/youtube.txt` (gitignored)
3. Deno on VM (`~/.deno/bin`) — installed by `scripts/setup_oracle_worker.sh`

## Cookie refresh

YouTube rotates session cookies. Stale cookies show bot-check errors on Oracle.

### Playwright sync (recommended) **SHIPPED**

```powershell
pip install -r requirements-cookies.txt
playwright install chromium

# First time — sign in when Chromium opens
python scripts/youtube_cookie_sync.py --headed --deploy --smoke --restart-batch

# Refresh profile + redeploy (after first login)
python scripts/youtube_cookie_sync.py --deploy --smoke --restart-batch

# Redeploy existing cookies/youtube.txt without opening browser
python scripts/youtube_cookie_sync.py --deploy-only --smoke --restart-batch
```

Profile: `cookies/browser_profile/` (gitignored). No API key replaces cookies for video download.

### Manual fallback

1. DevTools → copy **Cookie** header → `cookies/raw_header.txt`
2. `python scripts/convert_cookie_header.py`
3. `python scripts/youtube_cookie_sync.py --deploy-only --restart-batch`

## Phased corpus sprint

```bash
# Phase 1 — 10% pilot (5 channels)
CORPUS_QUEUE=corpus_queue_phase1.yaml CORPUS_FORCE=1 bash scripts/start_corpus_tmux.sh

# After gate (≥1 pipeline_status full)
python scripts/corpus_sprint.py --queue corpus_queue_phase2.yaml

# Analysis
python scripts/analyze_corpus.py   # → reports/corpus_analysis.md
```

Monitor: `tmux attach -t corpus` or `python scripts/corpus_monitor.py --watch`

## Current blockers (2025-06-27)

| Issue | Fix |
|-------|-----|
| `No video formats found` / bot check on Oracle IP | Fresh cookies + deno JS runtime |
| `my_mind_garden` no Shorts | Swapped to `dark_poetry_hub` in phase1 queue |
| Strict mp4 format | Fixed: `bestvideo*+bestaudio/best/b` |

Do **not** start phase 2 until phase 1 shows ≥1 `pipeline_status: full`.

## Split batch (download → analyze) **SHIPPED**

Cookie window for downloads only; analysis runs offline from disk.

| Script | Phase |
| --- | --- |
| `scripts/corpus_download.py` | A — discover + download (respects `max_batch_gb`, duration/MB caps) |
| `scripts/corpus_analyze.py` | B — steps 4–11 + assembler (no YouTube) |
| `scripts/corpus_health.py` | VM + progress snapshot → `reports/corpus_health.md` |
| `corpus_batch.yaml` | 3 channels, 5 videos, 25 GB cap |
| `scripts/start_batch_tmux.sh` | Download then analyze unattended |
| `scripts/start_health_watch_tmux.sh` | Health every 15 min |

```bash
tmux new-session -d -s corpus-batch 'bash scripts/start_batch_tmux.sh'
tmux new-session -d -s health 'bash scripts/start_health_watch_tmux.sh'
cat reports/corpus_health.md
```

Lite full pass: **5 videos**, no advanced visual/comments. **Downloads kept** under `artifacts/channels/{slug}/downloads/` (opt-in purge via `CORPUS_PURGE=1` or `--purge-artifacts`).

| File | Purpose |
| --- | --- |
| `corpus_queue_micro.yaml` | 3 channels, lite pipeline overrides |
| `scripts/start_micro_corpus_tmux.sh` | tmux runner (no purge by default) |

```bash
# One channel at a time (recommended first)
CORPUS_LIMIT=1 bash scripts/start_micro_corpus_tmux.sh

# All 3 micro channels (sequential)
bash scripts/start_micro_corpus_tmux.sh

# Optional: delete MP4s after each channel (disk-constrained VMs)
CORPUS_PURGE=1 bash scripts/start_micro_corpus_tmux.sh
```

Keeps `data/channels/{slug}/`, `reports/{slug}/`, and download artifacts unless purge is enabled.

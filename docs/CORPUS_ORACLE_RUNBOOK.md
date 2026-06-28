# Corpus Sprint — Oracle VM Runbook

**SHIPPED** worker path for phased corpus validation on Oracle (`ubuntu@80.225.234.65`).

## Prerequisites

1. SSH key: `ssh-key-2026-06-17.key` (gitignored)
2. **Fresh YouTube cookies** in Netscape format at `cookies/youtube.txt` (gitignored)
3. Deno on VM (`~/.deno/bin`) — installed by `scripts/setup_oracle_worker.sh`

## Cookie refresh (HITL — required when downloads fail with bot check)

YouTube rotates session cookies. Stale cookies show:

```text
Sign in to confirm you're not a bot
The provided YouTube account cookies are no longer valid
```

**Steps:**

1. In Chrome (logged into YouTube), open DevTools → Network → any `youtube.com` request → copy **Cookie** header value.
2. Save to `cookies/raw_header.txt` (gitignored).
3. Run: `python scripts/convert_cookie_header.py`
4. Deploy: `powershell scripts/deploy_cookies_to_oracle.ps1`

Smoke test on VM should list video formats (not just storyboard):

```bash
yt-dlp --cookies cookies/youtube.txt -F 'https://www.youtube.com/shorts/ab3Zy4c32lw' | head -20
```

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

## Option A — micro pilot (disk-safe) **SHIPPED**

Lite full pass: **5 videos**, no advanced visual/comments, **purge MP4s after each channel**.

| File | Purpose |
| --- | --- |
| `corpus_queue_micro.yaml` | 3 channels, lite pipeline overrides |
| `scripts/start_micro_corpus_tmux.sh` | tmux runner with `--purge-artifacts` |

```bash
# One channel at a time (recommended first)
CORPUS_LIMIT=1 bash scripts/start_micro_corpus_tmux.sh

# All 3 micro channels (sequential, purge between)
bash scripts/start_micro_corpus_tmux.sh

# Re-run completed slugs
CORPUS_FORCE=1 bash scripts/start_micro_corpus_tmux.sh
```

Keeps `data/channels/{slug}/` and `reports/{slug}/`; deletes `artifacts/.../downloads`, frames, caches.

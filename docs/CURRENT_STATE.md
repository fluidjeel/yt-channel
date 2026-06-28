# Current State — Source of Truth

> **Last verified:** 2026-06-27  
> If this doc conflicts with ChatGPT notes, Roadmap fantasies, or README marketing — **this doc wins**.

## One-line summary

**SHIPPED:** Single-channel YouTube Shorts reverse-engineering CLI (11 steps, local ML only).  
**ARCHITECTURE:** Universal 3-layer platform scaffold (Core / Niches / Brands) — **profiles SHIPPED as YAML**, code migration **PLANNED**.  
**NOT SHIPPED:** Profile loader, multi-channel discovery, LLM APIs, motion analysis, generation, knowledge graph.

## Platform layers (architecture pivot)

| Layer | Path | Status |
|-------|------|--------|
| 1 Core | `content_intelligence_core/` | **SCaffold** — README tree; code still in `channel_analyzer/` |
| 2 Niche | `niches/emotional_healing/` | **REFERENCE YAML** (6 files) |
| 3 Brand | `brands/whisprs_style/` | **REFERENCE YAML** |

Formula: **Core + Niche + Brand = Content**. See `docs/ARCHITECTURE_VISION.md`.

Default stack: `emotional_healing` + `whisprs_style` (not wired to CLI yet).

---

## What runs today

Entry point: `main.py` → `channel_analyzer.pipeline.run_pipeline()`

| Step | Module | Output | Status |
|------|--------|--------|--------|
| 1 | `discovery.py` | `data/videos.csv` | **SHIPPED** |
| 2 | `performance.py` | `data/top_videos.csv` | **SHIPPED** |
| 3 | `downloader.py` | `artifacts/downloads/{id}/` | **SHIPPED** |
| 4 | `audio_analysis.py` | `reports/audio_analysis.md`, transcripts | **SHIPPED** |
| 5 | `visual_analysis.py` | `reports/visual_analysis.md` | **SHIPPED** (heuristic) |
| 6 | `emotion_analysis.py` | `reports/emotion_clusters.md` | **SHIPPED** (local embeddings) |
| 7 | `narrative_analysis.py` | `reports/narrative_patterns.md` | **SHIPPED** (regex heuristics) |
| 8 | `music_analysis.py` | `reports/music_profile.md` | **SHIPPED** |
| 9 | `quote_analysis.py` | `data/quote_database.csv` | **SHIPPED** |
| 10 | `report.py` | `reports/channel_playbook.md` | **SHIPPED** |
| 11 | `bonus.py` | frames, style refs, `master_prompt_library.md` | **SHIPPED** |

### CLI (actual)

```bash
python main.py "CHANNEL_URL"                    # steps 1–11
python main.py "CHANNEL_URL" --step N           # N = 1..11
python main.py "CHANNEL_URL" --from 4 --to 7
python main.py "CHANNEL_URL" --config path.yaml
python main.py "CHANNEL_URL" --mvp-profile      # pipeline + MVP JSON + human report
python main.py --check-deps
```

**Does NOT work:** `python -m channel_analyzer.discovery` (no `__main__` in modules).

---

## Technology in use (today)

| Component | Library | Notes |
|-----------|---------|-------|
| Download | yt-dlp | Shorts + metadata |
| Transcription | openai-whisper (local) | Not OpenAI API |
| Embeddings | sentence-transformers | Local, not cloud |
| Vision | OpenCV + k-means | Not vision LLM |
| Audio features | librosa | Tempo, key, loudness |
| Video I/O | moviepy, ffmpeg | Via imageio-ffmpeg fallback |

**No cloud LLM APIs are integrated.** Claude/GPT/DeepSeek/Grok rules in `.cursor/rules/llm_usage.mdc` are **PLANNED** routing guidance only.

---

## Output directories

| Path | Created by | Gitignored |
|------|------------|------------|
| `data/` | Steps 1–2, 6, 9 | Yes |
| `reports/` | Steps 4–10, 11 | Yes |
| `artifacts/downloads/` | Step 3 | Yes |
| `artifacts/top_frames/` | Step 11 | Yes |
| `artifacts/style_reference/` | Step 11 | Yes |
| `artifacts/_frames_cache/` | Step 5 | Yes |
| `artifacts/llm_cache/` | `ensure_dirs()` only | Yes — **dir created, never written** |

---

## `market_intelligence/` — **SCaffold only**

Files exist:

- `config.py`, `models.py`, `storage.py`, `yt_helpers.py`

**Missing (do not assume these work):**

- `pipeline.py`, `channel_discovery.py`, `channel_similarity.py`, `cross_channel_analysis.py`, `opportunity_detector.py`
- CLI integration in `main.py`
- Any of: `discovered_channels.csv`, `channel_similarity.csv`, `common_patterns.md`, `niche_map.md`, `opportunities.md`, `knowledge_graph.graphml`, `dashboard/summary.json`

Config block `market_intelligence:` in `config.yaml` is loaded by `MarketConfig` only — **not** by the main pipeline.

Config block `llm:` in `config.yaml` defines provider routing — **PLANNED**, not wired. See `docs/TOKEN_ECONOMICS.md` and `channel_analyzer/llm/README.md`.

---

## Known limitations (honest)

1. **Visual analysis** — dominant colors, brightness, coarse scene labels. No typography, film grain, bokeh, anime style DNA, dual-palette taxonomy.
2. **Emotion analysis** — keyword + embedding clustering. `config.yaml` `emotion_dimensions` is **loaded but unused**; seeds are hardcoded in `emotion_analysis.py`.
3. **Narrative analysis** — regex Hook/Reflection/Insight/Resolution; not LLM-quality.
4. **Playbook** — merges prior reports; content calendar / gaps sections are template-ish.
5. **networkx** — in `requirements.txt` but **not imported** anywhere.
6. **Tests** — pytest in requirements; **no test files** in repo.
7. **Resume/checkpoints** — only scaffold in `market_intelligence/storage.py`; channel pipeline has no checkpoint resume.

---

## Niche reference docs (not code)

These describe the **target content style** (emotional lo-fi anime Shorts, e.g. Whisprs-style) for future analysis and generation — they are **REFERENCE**, not implemented analyzers:

- `docs/07_EmotionalTaxonomy.md`
- `docs/08_VisualTaxonomy.md`
- `docs/09_MotionBible.md`
- `docs/10_STYLE_BIBLE.md`

---

## Before implementing anything new

1. Read [NON_GOALS.md](./NON_GOALS.md)
2. Check this file — is the feature **SHIPPED**, **PARTIAL**, or **PLANNED**?
3. Update this file when you ship something

---

## MVP Phase 1 — Productization **PARTIAL**

Evidence gate cleared (2026-06-27). Field mapping audit: **no new analyzers required** (`reports/field_mapping_audit.md`).

| Doc / artifact | Status |
| --- | --- |
| `docs/MVP_SPEC.md` | **SHIPPED** — user flow + three output sections |
| `docs/MVP_DATA_CONTRACT.md` | **SHIPPED** — field schema + report mapping |
| `docs/MVP_SCORING.md` | **SHIPPED** — HIGH/MEDIUM/LOW from existing evidence only |
| `reports/mvp_readiness_review.md` | **SHIPPED** — conditional GO for user testing |
| `reports/field_mapping_audit.md` | **SHIPPED** — 38/47 fully mappable; 7 partial; 2 policy |
| `assembler/` | **SHIPPED** — thin JSON assembler (no LLM, no new analyzers) |
| `assembler/report_renderer.py` | **SHIPPED** — human markdown from `mvp_profile.json` |
| `docs/CREATOR_FEEDBACK_TEMPLATE.md` | **SHIPPED** — validation form + JSON schema |
| `scripts/record_creator_feedback.py` | **SHIPPED** — append to `data/feedback/creator_feedback.jsonl` |

**Assembler CLI:**

```bash
python -m assembler whisprs_yt
python -m assembler soulxsigh --url "https://www.youtube.com/@SoulxSigh/shorts"
```

**MVP end-to-end CLI:**

```bash
python main.py "https://www.youtube.com/@WhisprsYT" --mvp-profile
```

Outputs:

- `reports/{slug}/mvp_profile.json` — every leaf field uses `{ value, confidence, source }`
- `reports/{slug}/channel_intelligence_report.md` — six-section human report (no LLM)

**Not shipped:** Web UI, API server, billing, automatic creator outreach.

## Oracle worker (build server) **SHIPPED**

Reproducible VM setup — not agents, not GPU workloads:

| Script | Purpose |
| --- | --- |
| `scripts/setup_oracle_worker.sh` | apt deps, clone `~/projects/yt-channel`, venv, `--check-deps` |
| `scripts/run_mvp_in_tmux.sh` | Long runs in tmux; logs to `~/logs/` |
| `.env.example` | Optional keys in `~/.env` (MVP path needs none) |

VM layout: `~/projects/yt-channel`, `~/data`, `~/logs`, tmux session `yt`.

## Phase 3 — Corpus Sprint **SHIPPED** (phased)

Scale validation before creator interviews. No new analyzers.

| Artifact | Purpose |
| --- | --- |
| `corpus_queue.yaml` | Full list (52 channels; target 100) |
| `corpus_queue_phase1.yaml` | **10% pilot** (5 channels, full cycle + `--force`) |
| `corpus_queue_micro.yaml` | **Option A** — 3 channels, 5 videos each (downloads kept) |
| `corpus_queue_phase2.yaml` | **60% scale** (31 channels) — run after phase 1 gate |
| `scripts/build_corpus_phases.py` | Regenerate phase1/phase2 from main queue |
| `scripts/corpus_sprint.py` | Queue → pipeline → assembler; `data/corpus/run_log.jsonl` |
| `scripts/analyze_corpus.py` | Failure patterns → `reports/corpus_analysis.md` |
| `scripts/corpus_monitor.py` | Progress snapshot; `--watch` or cron every 30 min |
| `scripts/install_corpus_cron.sh` | Install monitor cron on Oracle VM |

**Phased workflow:**

```bash
# Phase 1 — 10% pilot (~5 channels, ~3–8 hours on Oracle)
python scripts/corpus_sprint.py --queue corpus_queue_phase1.yaml --force
python scripts/analyze_corpus.py

# Gate: ≥3 pipeline_status full OR clear failure taxonomy → then phase 2
python scripts/corpus_sprint.py --queue corpus_queue_phase2.yaml
```

Oracle: `tmux session corpus` via `scripts/start_corpus_tmux.sh` (defaults to phase1).

**2025-06-27:** yt-dlp format fallback (`bestvideo*+bestaudio/best/b`) + `ignore_no_formats_error`; phase1 swaps `my_mind_garden` → `dark_poetry_hub`. Deno JS runtime wired in `merge_ytdlp_opts`. **Blocker:** stale YouTube cookies on Oracle — refresh via `docs/CORPUS_ORACLE_RUNBOOK.md` + `scripts/deploy_cookies_to_oracle.ps1`.

Bible synthesis **off** in corpus queue (LLM-free scale path).

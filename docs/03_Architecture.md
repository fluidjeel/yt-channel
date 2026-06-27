# Architecture

> **Platform:** [ARCHITECTURE_VISION.md](./ARCHITECTURE_VISION.md) — Core + Niche + Brand.  
> Runnable today: `channel_analyzer/`. Scaffold: `content_intelligence_core/`, `niches/`, `brands/`.

## Current system **SHIPPED**

```
main.py
    └── channel_analyzer.pipeline.run_pipeline()
            ├── [1-3]  Collectors     discovery, performance, downloader
            ├── [4-9]  Analyzers      audio, visual, emotion, narrative, music, quotes
            ├── [10]   Synthesizer    report.generate_playbook()
            └── [11]   Bonus          bonus.run_bonus_features()
```

Pattern: **collector → analyzer → synthesizer → report**

Steps communicate via **files on disk** (CSV, Markdown, JSON, NPZ, images) — not message queues or agent RPC.

### Directory contract

| Layer | Path | Formats |
|-------|------|---------|
| Data | `data/` | CSV |
| Reports | `reports/` | Markdown |
| Artifacts | `artifacts/` | MP4, MP3, PNG, JSON, NPZ |

Config: `channel_analyzer.config.Config` from `config.yaml` (top-level keys only; not `market_intelligence` block).

---

## Module map **SHIPPED**

| File | Responsibility |
|------|----------------|
| `discovery.py` | yt-dlp channel/Shorts enumeration |
| `performance.py` | Weighted ranking |
| `downloader.py` | Top-N asset download |
| `audio_analysis.py` | ffmpeg + Whisper + text stats |
| `visual_analysis.py` | OpenCV frames + color/scene heuristics |
| `emotion_analysis.py` | sentence-transformers + KMeans |
| `narrative_analysis.py` | Section segmentation heuristics |
| `music_analysis.py` | librosa features |
| `quote_analysis.py` | Quote lines + theme clusters |
| `report.py` | Playbook merge |
| `bonus.py` | Representative frames + prompt library |

Shared: `config.py`, `utils.py`, `pipeline.py`

---

## Scaffold **NOT wired**

```
market_intelligence/
    config.py      → MarketConfig (reads market_intelligence: in yaml)
    models.py      → ChannelMetadata, SimilarityResult, etc.
    storage.py     → CSV/checkpoint helpers
    yt_helpers.py  → search + metadata fetch
```

**No entry point.** Not imported by `main.py`.

Intended future flow **PLANNED**:

```
seed URL → channel_discovery → similarity → cross_channel_analysis
         → opportunity_detector → knowledge_graph → dashboard/summary.json
```

---

## Future layers **PLANNED** (do not implement as part of unrelated tasks)

```
Layer 6: Critics        style, audience, quality scores
Layer 5: Generators     script, image, motion, voice, video compose
Layer 4: LLM synthesis  style bible from artifacts (Claude/GPT)
Layer 3: Knowledge      graph + taxonomies + vector store
Layer 2: Market intel   multi-channel (scaffold started)
Layer 1: Single channel **SHIPPED**
```

---

## Rules for new code

1. No business logic in `main.py` beyond CLI parsing
2. Each step module: single primary output path, log clearly
3. Steps must be rerunnable idempotently where possible (overwrite reports)
4. New collectors/analyzers follow same artifact paths
5. Do not call cloud APIs from analyzer steps without explicit config + user approval

---

## Dependency graph (runtime)

```
yt-dlp ──► downloads ──► whisper, opencv, librosa, moviepy
                              │
                              ▼
                    sentence-transformers (emotion, quotes)
                              │
                              ▼
                         report.py, bonus.py
```

No database. No Redis. No web server.

---

## LLM layer **PLANNED**

Intelligence workloads must follow [`TOKEN_ECONOMICS.md`](./TOKEN_ECONOMICS.md):

- Provider abstraction: `channel_analyzer/llm/` (scaffold README only)
- Config: `config.yaml` → `llm:` (analysis/classification/generation/research providers)
- Pattern: DeepSeek bulk extract → JSON → Claude synthesis → `artifacts/llm_cache/`
- Cursor builds scripts; user API keys execute — not Cursor chat at scale

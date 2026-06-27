# Product Requirements

> Split explicitly: **SHIPPED** = in repo today. **PLANNED** = not built.

---

## SHIPPED — Functional

### Single-channel analysis

- [x] Discover Shorts via yt-dlp → `data/videos.csv`
- [x] Rank by views, views/day, engagement, recency → `data/top_videos.csv`
- [x] Download top N videos + thumbnails → `artifacts/downloads/`
- [x] Extract audio, Whisper transcribe → `reports/audio_analysis.md`
- [x] Extract frames, colors, coarse scenes → `reports/visual_analysis.md`
- [x] Cluster emotions (local embeddings) → `reports/emotion_clusters.md`
- [x] Narrative heuristics → `reports/narrative_patterns.md`
- [x] Music profile (librosa) → `reports/music_profile.md`
- [x] Quote extraction → `data/quote_database.csv`
- [x] Synthesize playbook → `reports/channel_playbook.md`
- [x] Bonus: top frames, style refs, prompt library

### CLI

- [x] Full run, single step, step range, `--check-deps`, `--config`

---

## SHIPPED — Non-functional

- [x] Python 3.10+, modular step files
- [x] Config via `config.yaml`
- [x] Artifacts: CSV, Markdown under `data/`, `reports/`, `artifacts/`
- [x] Local processing (no API keys required for core pipeline)

---

## PARTIAL / SCaffold

- [ ] `market_intelligence/` — config, models, yt helpers only
- [ ] `artifacts/llm_cache/` — directory created, unused
- [ ] `emotion_dimensions` in config — loaded, unused in code
- [ ] Content calendar in playbook — template text, not data-driven

---

## PLANNED — Discovery & intelligence

- [ ] Seed channel → discover 100+ similar channels
- [ ] Similarity scoring (title, transcript, emotion, visual themes)
- [ ] Channel categories: direct, adjacent, emerging, outlier
- [ ] Cross-channel `common_patterns.md`
- [ ] Opportunity detector by theme
- [ ] Knowledge graph (networkx)
- [ ] Dashboard JSON summary
- [ ] Comment collection + audience psychology

---

## PLANNED — Deeper analysis

- [ ] Motion analysis (camera, particles, cloud drift)
- [ ] Visual taxonomy matching (see `08_VisualTaxonomy.md`)
- [ ] Typography / text overlay detection
- [ ] Texture stack detection (grain, matte grade)
- [ ] LLM synthesis layer (Claude/GPT) on **preprocessed** artifacts only

---

## PLANNED — Generation

- [ ] Script writer agent
- [ ] Image director + API or local Flux/SDXL
- [ ] Motion director + composer (MoviePy/Remotion)
- [ ] Voice (ElevenLabs or similar)
- [ ] Quality critics before publish
- [ ] Shorts export pipeline

---

## Constraints

- Never send raw video frames to cloud LLMs (preprocess first)
- No hardcoded API keys
- New features must update `CURRENT_STATE.md`
- Prefer extending existing step modules over parallel pipelines

## Success metrics **PLANNED**

- Style match score for generated images vs reference
- Reproducible reports from same inputs
- Analysis runtime and disk usage documented per channel size

# Module & Agent Catalog

> **Today:** Python **modules** in a linear pipeline — not separate autonomous agents.  
> **Future:** May split into agents that read/write artifacts only.

---

## SHIPPED — Pipeline modules

| Name | Step | Input | Output | "Agent"? |
|------|------|-------|--------|----------|
| Channel Discovery | 1 | Channel URL | `data/videos.csv` | Module |
| Performance Ranker | 2 | videos.csv | `data/top_videos.csv` | Module |
| Asset Downloader | 3 | top_videos.csv | `artifacts/downloads/` | Module |
| Audio Analyzer | 4 | downloads | `reports/audio_analysis.md` | Module |
| Visual Analyzer | 5 | downloads | `reports/visual_analysis.md` | Module |
| Emotion Analyzer | 6 | transcripts + text | `reports/emotion_clusters.md` | Module |
| Narrative Analyzer | 7 | transcripts | `reports/narrative_patterns.md` | Module |
| Music Analyzer | 8 | audio files | `reports/music_profile.md` | Module |
| Quote Analyzer | 9 | transcripts | `data/quote_database.csv` | Module |
| Playbook Synthesizer | 10 | all reports | `reports/channel_playbook.md` | Module |
| Bonus Features | 11 | frames + reports | frames, style refs, prompts | Module |

Orchestrator: `channel_analyzer.pipeline.run_pipeline()` — **not** an agent registry.

---

## SCaffold — Market intelligence (not runnable)

| Name | Status | Intended input | Intended output |
|------|--------|----------------|-----------------|
| Channel Discovery Engine | **SCaffold** | Seed URL | `data/discovered_channels.csv` |
| Similarity Engine | **PLANNED** | Profiles | `data/channel_similarity.csv` |
| Categorizer | **PLANNED** | Similarity scores | `data/channel_categories.csv` |
| Cross-Channel Analyzer | **PLANNED** | Top N channels | `reports/common_patterns.md` |
| Opportunity Detector | **PLANNED** | Themes + competition | `reports/opportunities.md` |
| Knowledge Graph Builder | **PLANNED** | All artifacts | `knowledge_graph/knowledge_graph.graphml` |
| Dashboard Data | **PLANNED** | Aggregates | `dashboard/summary.json` |

Helpers **SHIPPED** in scaffold: `yt_helpers.py`, `storage.py`, `models.py`, `config.py`

---

## PLANNED — Future agents (not in codebase)

| Agent | Model (planned) | Input artifacts | Output artifacts |
|-------|-----------------|-------------------|------------------|
| Style Bible Generator | Claude | analysis reports | `style_bibles/{channel}/` |
| Audience Psychology | Claude + DeepSeek | comments.csv | `audience_insights.md` |
| Trend Research | Grok | web + niche map | `trends.md` |
| Content Strategist | GPT | bibles + trends | `content_ideas.md` |
| Script Writer | Claude | theme + bible | `script.md` |
| Image Director | GPT | script + visual bible | `prompts.json` |
| Image Critic | Claude | image + bible | `scores.json` |
| Motion Director | GPT | script + motion bible | `motion_plan.yaml` |
| Voice Generator | ElevenLabs API | script | `narration.mp3` |
| Quality Council | Multi | all assets | `publish_decision.json` |

**None of these exist.** Do not create fake implementations.

---

## Communication pattern

**Current:** `pipeline.py` calls functions sequentially.

**Target **PLANNED**:** Each unit reads prior CSV/MD/JSON, writes new artifacts. No direct agent-to-agent calls.

Success metric for a future agent: given fixed inputs, reproducible output file + unit test on schema.

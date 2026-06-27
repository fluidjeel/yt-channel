# Data Model

Schemas derived from **actual code** in `channel_analyzer/` and `market_intelligence/models.py`.

---

## SHIPPED — `data/videos.csv`

Produced by `discovery.py`. Key columns (representative):

| Column | Type | Notes |
|--------|------|-------|
| video_id | str | YouTube ID |
| title | str | |
| url | str | |
| view_count | int | |
| like_count | int | nullable |
| duration | float | seconds |
| upload_date | str | ISO or yyyymmdd from yt-dlp |

---

## SHIPPED — `data/top_videos.csv`

Produced by `performance.py`. Adds ranking scores:

| Column | Type | Notes |
|--------|------|-------|
| composite_score | float | Weighted from config |
| views_per_day | float | |
| engagement_rate | float | likes/views proxy |
| recency_score | float | |

Weights in `config.yaml` → `ranking_weights`.

---

## SHIPPED — `artifacts/downloads/{video_id}/`

| File | Description |
|------|-------------|
| `{video_id}.mp4` | Video |
| `{video_id}.jpg` or thumbnail | Thumbnail |
| `metadata.json` | yt-dlp metadata |
| `audio.mp3` | After step 4 |
| `transcript.txt` | After step 4 |

---

## SHIPPED — Reports (Markdown)

| File | Producer |
|------|----------|
| `reports/audio_analysis.md` | step 4 |
| `reports/visual_analysis.md` | step 5 |
| `reports/emotion_clusters.md` | step 6 |
| `reports/narrative_patterns.md` | step 7 |
| `reports/music_profile.md` | step 8 |
| `reports/quote_patterns.md` | step 9 |
| `reports/channel_playbook.md` | step 10 |
| `reports/master_prompt_library.md` | step 11 |

---

## SHIPPED — `data/quote_database.csv`

| Column | Type | Notes |
|--------|------|-------|
| video_id | str | |
| quote | str | extracted line |
| theme | str | assigned cluster label |

---

## SHIPPED — `data/emotion_scores.csv`

Per-video emotion dimension scores from step 6 (when generated).

---

## SHIPPED — Frame cache

| Path | Format |
|------|--------|
| `artifacts/_frames_cache/` | PNG frames |
| `artifacts/_frame_bank.npz` | NumPy archive for bonus step |

---

## SCaffold — `market_intelligence/models.py`

### `ChannelMetadata.to_row()`

```
channel_name, channel_url, subscriber_count, video_count,
total_views, niche_category, discovery_source
```

### `SimilarityResult` **PLANNED output**

```
seed_channel, candidate_channel, similarity_score,
emotional_similarity, visual_similarity, narrative_similarity
```

### `ChannelCategory` enum

`DIRECT_COMPETITOR`, `ADJACENT_COMPETITOR`, `EMERGING_CHANNEL`, `OUTLIER_WINNER`

---

## PLANNED — Not implemented

- `data/discovered_channels.csv`
- `data/channel_similarity.csv`
- `data/channel_categories.csv`
- `knowledge_graph/knowledge_graph.graphml`
- `dashboard/summary.json`
- Comment entities
- Generated content entities (scripts, prompts, renders)

---

## Config entities

### `Config` (channel_analyzer)

Paths: `data_dir`, `reports_dir`, `artifacts_dir`  
Limits: `top_n_download`, `max_videos_discover`, `whisper_model`, frame settings

### `MarketConfig` (market_intelligence)

Separate loader; see `config.yaml` → `market_intelligence:` block.

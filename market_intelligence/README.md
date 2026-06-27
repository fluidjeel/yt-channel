# Market Intelligence — **SCaffold**

> **Not runnable.** No CLI integration. See [`docs/CURRENT_STATE.md`](../docs/CURRENT_STATE.md).

## What exists

| File | Purpose |
|------|---------|
| `config.py` | `MarketConfig` from `config.yaml` → `market_intelligence:` |
| `models.py` | `ChannelMetadata`, `ChannelProfile`, `SimilarityResult`, enums |
| `storage.py` | CSV append, checkpoint JSON, markdown writers |
| `yt_helpers.py` | Channel metadata, YouTube search helpers |

## What is missing

- `pipeline.py` or `channel_discovery.py`
- Similarity, cross-channel, opportunity modules
- Integration in `main.py`
- All report outputs (`common_patterns.md`, `niche_map.md`, etc.)

## Config

See root `config.yaml` section `market_intelligence:`.

## Next implementation step **PLANNED**

1. `channel_discovery.py` — seed URL → `data/discovered_channels.csv`
2. Unit test with mocked yt-dlp/search
3. Subcommand: `python main.py discover "SEED_URL"` (after user approves)
4. Update `CURRENT_STATE.md` when step 1 ships

## Do not

- Pretend this module runs when user runs default `main.py`
- Return hardcoded channel lists as if discovery worked

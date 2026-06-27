# Channel Intelligence Analyzer

**Universal Content Intelligence Platform** — Layer 1 CLI (single-channel analysis today).

```
Core + Niche + Brand = Content
```

First reference stack: `niches/emotional_healing/` + `brands/whisprs_style/` (YAML profiles; loader **PLANNED**).

> **Docs:** [`docs/00_INDEX.md`](docs/00_INDEX.md) · [`docs/ARCHITECTURE_VISION.md`](docs/ARCHITECTURE_VISION.md) · [`AGENTS.md`](AGENTS.md)

## What works today **SHIPPED**

11-step CLI (`channel_analyzer/`) — local processing, no cloud LLM APIs.

## Platform layout

| Layer | Path | Status |
|-------|------|--------|
| Core | `content_intelligence_core/` + `channel_analyzer/` | Pipeline **SHIPPED** |
| Niche | `niches/emotional_healing/` | Profile YAML |
| Brand | `brands/whisprs_style/` | Brand YAML |

## Quick start

```bash
python main.py --check-deps
python main.py "https://www.youtube.com/@channel"
```

See [`docs/CURRENT_STATE.md`](docs/CURRENT_STATE.md) for full step list.

## Configuration

`config.yaml` — pipeline limits, ranking, LLM routing (**PLANNED**).

Future: `platform.active_niche` / `active_brand` — see [`docs/MIGRATION_PLAN.md`](docs/MIGRATION_PLAN.md).

## License

MIT

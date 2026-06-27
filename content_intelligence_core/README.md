# Content Intelligence Core (Layer 1)

> **Status:** **ARCHITECTURE** — target home for niche-agnostic intelligence.  
> **Today:** Implemented as `channel_analyzer/` + partial `market_intelligence/`. **No code moved yet.**

Layer 1 must **never** mention anime, healing, horror, finance, or humor. Those belong in Layer 2 (niches) and Layer 3 (brands).

---

## Subsystems

| Directory | Responsibility | Current code (SHIPPED) | Status |
|-----------|----------------|------------------------|--------|
| `discovery/` | Channel/video discovery, benchmarks | `channel_analyzer/discovery.py`, `performance.py`, `downloader.py`; MI scaffold | **PARTIAL** |
| `analysis/` | Visual, audio, comment, narrative, motion | Steps 4–9 in `channel_analyzer/` | **PARTIAL** (no comments, motion) |
| `synthesis/` | Bibles, personas, content DNA | `report.py`, `bonus.py`; LLM layer **PLANNED** | **PARTIAL** |
| `knowledge/` | Taxonomy registry, graph, research DB | `market_intelligence/` scaffold | **SCaffold** |
| `evaluation/` | Confidence, evidence, validation | — | **PLANNED** |
| `generation/` | Script, image, motion, voice | — | **PLANNED** |

---

## Design rules

1. All inputs/outputs are **artifacts** (CSV, JSON, Markdown) — no niche terms in core module names.
2. Niche-specific interpretation happens **outside** core, via profile loaders reading `niches/*/`.
3. Brand-specific expression happens via `brands/*/brand.yaml`.
4. Generation formula: **Core + Niche Profile + Brand DNA = Content** (see `docs/ARCHITECTURE_VISION.md`).

---

## Migration

See [`docs/MIGRATION_PLAN.md`](../../docs/MIGRATION_PLAN.md). Phase M1 keeps `main.py` → `channel_analyzer` unchanged; new layout grows alongside until cutover.

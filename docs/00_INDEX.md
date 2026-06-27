# Documentation Index

Read these **before** writing code or suggesting features in this repo.

| Doc | Purpose | When to read |
|-----|---------|--------------|
| [CURRENT_STATE.md](./CURRENT_STATE.md) | **Source of truth** — what exists vs what does not | Every new task |
| [NON_GOALS.md](./NON_GOALS.md) | What not to build unless explicitly requested | Before expanding scope |
| [01_Vision.md](./01_Vision.md) | Long-term mission (mostly **FUTURE**) | Planning only |
| [02_PRD.md](./02_PRD.md) | Requirements split: **SHIPPED** vs **PLANNED** | Scoping work |
| [03_Architecture.md](./03_Architecture.md) | Current pipeline + future layers | Structural changes |
| [04_Roadmap.md](./04_Roadmap.md) | Phases with status tags | Prioritization |
| [05_AgentCatalog.md](./05_AgentCatalog.md) | Modules today; agents tomorrow | New features |
| [06_DataModel.md](./06_DataModel.md) | CSV/report schemas from actual code | Data changes |
| [07_EmotionalTaxonomy.md](./07_EmotionalTaxonomy.md) | **Reference** — target niche emotions | Analysis tuning |
| [08_VisualTaxonomy.md](./08_VisualTaxonomy.md) | **Reference** — target visual ontology | Analysis tuning |
| [09_MotionBible.md](./09_MotionBible.md) | **Reference + PLANNED** — motion patterns | Future motion work |
| [10_STYLE_BIBLE.md](./10_STYLE_BIBLE.md) | **Reference** — Whisprs-style reverse engineering | Prompt/style targets |
| [TOKEN_ECONOMICS.md](./TOKEN_ECONOMICS.md) | **Policy** — Cursor vs API keys, model routing, cost rules | Before any LLM feature |
| [ARCHITECTURE_VISION.md](./ARCHITECTURE_VISION.md) | **Platform** — 3-layer Core / Niche / Brand | Architecture work |
| [MIGRATION_PLAN.md](./MIGRATION_PLAN.md) | Move code without breaking CLI | Refactors |
| [NICHE_PROFILE_SPEC.md](./NICHE_PROFILE_SPEC.md) | Layer 2 YAML contract | New niches |
| [BRAND_DNA_SPEC.md](./BRAND_DNA_SPEC.md) | Layer 3 brand.yaml contract | New brands |
| [FUTURE_MULTI_CHANNEL_ROADMAP.md](./FUTURE_MULTI_CHANNEL_ROADMAP.md) | Many channels — **PLANNED** | Long-term only |

## Platform layout (architecture)

```
content_intelligence_core/   Layer 1 — niche-agnostic (scaffold + channel_analyzer today)
niches/                      Layer 2 — emotional_healing, …
brands/                      Layer 3 — whisprs_style, …
channel_analyzer/            SHIPPED implementation (migrates to core later)
```

## Status tags used everywhere

| Tag | Meaning |
|-----|---------|
| **SHIPPED** | Implemented and runnable via `python main.py` |
| **PARTIAL** | Code exists but incomplete or not wired to CLI |
| **SCaffold** | Models/config/helpers only; no pipeline |
| **PLANNED** | Documented intent; no code yet |
| **REFERENCE** | Knowledge for humans/LLMs; not implemented in code |

## Cursor rules (`.cursor/rules/`)

| Rule | Role |
|------|------|
| `project_context.mdc` | Current vs future boundary — **read first** |
| `anti_hallucination.mdc` | Do not claim unbuilt features exist |
| `architecture.mdc` | Layering and module boundaries |
| `agents.mdc` | Artifact-based communication |
| `llm_usage.mdc` | Model routing (**future** API use) |
| `token_economics.mdc` | **Cursor vs API keys** — no bulk analysis in chat |
| `coding_standards.mdc` | Python style for this repo |

## Quick start (what works today)

```bash
cd C:\Manasjit\ai\yt-channel
.venv\Scripts\activate
python main.py --check-deps
python main.py "https://www.youtube.com/@channelname"
```

Outputs: `data/`, `reports/`, `artifacts/` under project root.

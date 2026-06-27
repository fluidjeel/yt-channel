# Roadmap

Status: **DONE** | **IN PROGRESS** | **NEXT** | **PLANNED** | **DEFERRED**

Platform roadmap: [FUTURE_MULTI_CHANNEL_ROADMAP.md](./FUTURE_MULTI_CHANNEL_ROADMAP.md)  
Migration: [MIGRATION_PLAN.md](./MIGRATION_PLAN.md)

---

## Phase 0 — Platform architecture pivot **IN PROGRESS**

| Item | Status |
|------|--------|
| 3-layer scaffold (`content_intelligence_core/`, `niches/`, `brands/`) | **DONE** |
| `emotional_healing` niche YAML (6 files) | **DONE** |
| `whisprs_style` brand.yaml | **DONE** |
| ARCHITECTURE_VISION, NICHE/BRAND specs, migration plan | **DONE** |
| Profile loader (M1) | **NEXT** |
| `channel_analyzer` unchanged | **SHIPPED** |

---

## Phase 1 — Single-channel intelligence **DONE**

| Item | Status |
|------|--------|
| 11-step pipeline | **DONE** |
| CLI, config, docs, token economics | **DONE** |

---

## Phase 2 — Knowledge extraction **NEXT**

| Item | Status |
|------|--------|
| M1 profile loader + CLI `--niche` / `--brand` | **NEXT** |
| Run pipeline on 3–5 channels (emotional_healing lens) | **NEXT** |
| `market_intelligence/channel_discovery.py` | **PLANNED** |
| Cross-channel analysis | **PLANNED** |
| LLM synthesis (token-efficient) | **PLANNED** |

---

## Phase 3 — Second niche proof **PLANNED**

| Item | Status |
|------|--------|
| Full profile for `horror` or `tech_reviews` | **PLANNED** |
| Brand `dark_lantern` or `neural_brief` | **PLANNED** |
| Same core, different playbook via profiles | **PLANNED** |

---

## Phase 4 — Core migration **PLANNED**

Physical move `channel_analyzer` → `content_intelligence_core` with compat shims (M3–M5).

---

## Phase 5 — Motion + evaluation **PLANNED**

Motion analysis, evaluation/scoring from `quality_rules.yaml`.

---

## Phase 6 — Generation studio **PLANNED**

Core + Niche + Brand driven script/image/motion/voice.

---

## Phase 7 — Multi-channel scale **DEFERRED**

Portfolio of many brands — after Phase 3 proof.

---

## Immediate order

1. M1 profile loader (no breaking changes)
2. Run analyzer with default `emotional_healing` + `whisprs_style`
3. `channel_discovery.py`
4. Second niche proof — not 20 channels yet

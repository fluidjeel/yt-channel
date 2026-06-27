# Architecture Vision — Universal Content Intelligence Platform

> **Status:** **ARCHITECTURE** (target). **SHIPPED** code still lives in `channel_analyzer/` until migration.  
> Emotional healing / Whisprs is **niche + brand #1**, not the platform identity.

---

## Philosophy

Start by **understanding the art form deeply**, not optimizing for "20 faceless channels" on day one.

The platform must support dozens of distinct brands without a shared fingerprint:

```
Core + Niche + Brand = Content
```

**Wrong product name:** WhisprsYT Intelligence Platform  
**Right product name:** Universal Content Intelligence Platform

---

## Three layers

```
┌─────────────────────────────────────────────────────────┐
│  Layer 3 — brands/          Voice, look, pacing, music  │
├─────────────────────────────────────────────────────────┤
│  Layer 2 — niches/          Themes, emotions, visual    │
│                             language, narrative arcs    │
├─────────────────────────────────────────────────────────┤
│  Layer 1 — content_intelligence_core/                   │
│             Discovery · Analysis · Synthesis ·          │
│             Knowledge · Evaluation · Generation         │
│             (NEVER mentions anime, healing, horror…)    │
└─────────────────────────────────────────────────────────┘
```

---

## Layer 1 — Universal Content Intelligence Core

Path: `content_intelligence_core/`

| Subsystem | Purpose |
|-----------|---------|
| **discovery/** | YouTube discovery, competitors, benchmarks |
| **analysis/** | Visual, audio, comments, narrative, motion |
| **synthesis/** | Bibles, personas, content DNA |
| **knowledge/** | Taxonomy registry, knowledge graph, research DB |
| **evaluation/** | Confidence, evidence, validation |
| **generation/** | Script, image, motion, voice |

**Rule:** Core modules output **structured, niche-neutral artifacts**. Interpretation uses Layer 2 + 3 loaders.

**Today:** `channel_analyzer/` implements discovery + analysis + partial synthesis. See [MIGRATION_PLAN.md](./MIGRATION_PLAN.md).

---

## Layer 2 — Niche Profiles

Path: `niches/{niche_id}/`

Required files per niche:

| File | Role |
|------|------|
| `taxonomy.yaml` | Themes, arcs, symbolism, audience needs |
| `persona.yaml` | Audience personas |
| `emotion_model.yaml` | Emotion pairs, intensity rules |
| `visual_model.yaml` | Archetypes, palettes, composition |
| `narrative_model.yaml` | Hooks, structure, pacing |
| `quality_rules.yaml` | Evaluation gates |

Registry: `niches/registry.yaml`

**First profile:** `emotional_healing/` (from Whisprs-style research)  
**Spec:** [NICHE_PROFILE_SPEC.md](./NICHE_PROFILE_SPEC.md)

---

## Layer 3 — Brand DNA

Path: `brands/{brand_id}/brand.yaml`

Defines **differentiation within a niche**:

- Voice & narration identity
- Visual identity family
- Pacing & cut style
- Music identity
- Motion identity
- Typography identity

Registry: `brands/registry.yaml`

**First brand:** `whisprs_style` → niche `emotional_healing`  
**Spec:** [BRAND_DNA_SPEC.md](./BRAND_DNA_SPEC.md)

---

## Content formula (examples)

| Core | Niche | Brand | Output |
|------|-------|-------|--------|
| ✓ | emotional_healing | whisprs_style | Poetic lo-fi healing Shorts |
| ✓ | tech_reviews | neural_brief | AI review channel |
| ✓ | horror | dark_lantern | Faceless horror Shorts |

Same machinery. Different YAML profiles.

---

## Config model **PLANNED**

```yaml
active_niche: emotional_healing
active_brand: whisprs_style
# Core paths unchanged; profiles loaded at runtime
```

Not wired to `main.py` yet — see [MIGRATION_PLAN.md](./MIGRATION_PLAN.md).

---

## Related docs

- [CURRENT_STATE.md](./CURRENT_STATE.md) — what runs today
- [MIGRATION_PLAN.md](./MIGRATION_PLAN.md) — move code without breaking CLI
- [FUTURE_MULTI_CHANNEL_ROADMAP.md](./FUTURE_MULTI_CHANNEL_ROADMAP.md) — 20+ brands path
- [TOKEN_ECONOMICS.md](./TOKEN_ECONOMICS.md) — LLM cost rules

---

## Anti-patterns

- Hardcoding "healing" or "anime" in `channel_analyzer/` module names
- One global style bible with no brand split
- Building generation before evaluation + profiles exist
- Renaming the repo to a single channel brand

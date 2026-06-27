# Vision

> **Status:** **Universal Content Intelligence Platform** — emotional healing is niche #1, not the product name.  
> Runnable code: see [CURRENT_STATE.md](./CURRENT_STATE.md). Architecture: [ARCHITECTURE_VISION.md](./ARCHITECTURE_VISION.md).

## Mission

Build a **Universal Content Intelligence Platform** where:

```
Core + Niche Profile + Brand DNA = Content
```

1. **Layer 1 (Core):** Reverse-engineer channels — discovery, analysis, synthesis, knowledge, evaluation, generation — **niche-agnostic**
2. **Layer 2 (Niches):** Specialization profiles (`emotional_healing`, `horror`, `tech_reviews`, …)
3. **Layer 3 (Brands):** Distinct voice, visual, pacing per channel (`whisprs_style`, `dark_lantern`, …)

**First stack:** Core + `emotional_healing` + `whisprs_style` (current art-form deep dive)

## Philosophy

Understand the **mechanics** of a content form before automating output at scale.

We extract **principles**, not copies. Many faceless brands, one platform — no shared AI fingerprint.

## What exists today **SHIPPED**

- Single-channel pipeline (`channel_analyzer/`, 11 steps)
- Architecture scaffold: `content_intelligence_core/`, `niches/`, `brands/`
- Reference profiles: `emotional_healing` + `whisprs_style`

## What is **PLANNED**

- Profile loaders wired to CLI
- Core code migration (see [MIGRATION_PLAN.md](./MIGRATION_PLAN.md))
- Multi-niche / multi-brand generation
- 20+ channels — **only after** second niche proof ([FUTURE_MULTI_CHANNEL_ROADMAP.md](./FUTURE_MULTI_CHANNEL_ROADMAP.md))

## Failure modes to avoid

- Naming the platform after one channel (WhisprsYT)
- Hardcoding healing/anime in Layer 1
- Scaling to 20 channels before one niche is deeply understood
- Docs/code claiming migration is complete before M5

## Legacy reference docs

Prose style research (pre-YAML): `07`–`10_*.md` — superseded for machine use by `niches/emotional_healing/` + `brands/whisprs_style/`.

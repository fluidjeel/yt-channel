# Future Multi-Channel Roadmap

> **Status:** **PLANNED** — platform direction after Layer 1 migration.  
> Does **not** mean "build 20 channels now." Means architecture supports N brands.

---

## Strategic sequence

```
1. Understand one art form deeply     ← you are here (emotional healing)
2. Universal core + profile system    ← this pivot (architecture)
3. Prove second niche + brand         ← validate Lego model
4. Scale channels with shared core      ← many brands, one platform
```

---

## Phase A — Platform foundation **IN PROGRESS**

| Item | Status |
|------|--------|
| 3-layer folder scaffold | **DONE** (this pivot) |
| `emotional_healing` niche YAML | **DONE** |
| `whisprs_style` brand YAML | **DONE** |
| Architecture docs | **DONE** |
| `channel_analyzer` CLI unchanged | **SHIPPED** |
| Profile loader in Python | **PLANNED** |
| Config `active_niche` / `active_brand` | **PLANNED** |

---

## Phase B — Core migration **PLANNED**

See [MIGRATION_PLAN.md](./MIGRATION_PLAN.md).

- Move analyzers under `content_intelligence_core/` (compat shims)
- Finish `market_intelligence` as `discovery/` extension
- Add `evaluation/` scoring using niche + brand YAML
- Comment analysis (niche-neutral extractor → niche-tagged themes)

---

## Phase C — Second niche proof **PLANNED**

Pick one contrasting niche (e.g. `horror` or `tech_reviews`):

1. Full six-file niche profile
2. One brand (`dark_lantern` or `neural_brief`)
3. Run same core pipeline on seed channel in that niche
4. Prove reports differ only via profile interpretation layer

**Exit criteria:** Same code path, two visibly different playbooks.

---

## Phase D — Multi-brand studio **PLANNED**

| Capability | Enables |
|------------|---------|
| Brand registry + switching | Multiple channels from one repo |
| Batch analysis | Benchmark sets per niche |
| Generation with Core+Niche+Brand | Distinct output per brand |
| Quality gates per `quality_rules.yaml` | No homogenized "AI channel" look |

Target: **many brands**, not one template with swapped quotes.

---

## Phase E — Scale **DEFERRED**

- 10+ niche profiles
- 20+ brand DNAs
- Automated opportunity detection per niche
- Publish adapters (Shorts export) per brand config

**Not a day-one goal.** Depth before breadth.

---

## Channel portfolio model (future)

```yaml
portfolio:
  - brand_id: whisprs_style
    channels: ["@channel_a"]
    status: active
  - brand_id: dark_lantern
    channels: []
    status: planned
```

Stored under `data/portfolio.yaml` — **PLANNED**.

---

## What stays constant across 20 channels

Layer 1: discovery, analysis engines, synthesis pipeline, evaluation framework, generation orchestration.

## What changes per channel

Layer 2 niche + Layer 3 brand YAML only.

---

## Success metrics (platform-level)

| Metric | Meaning |
|--------|---------|
| Profile swap test | Change brand YAML → output fingerprint changes, core unchanged |
| Niche isolation | No anime/healing strings in core imports |
| Cost per channel | Token economics preserved at scale |
| Time to new brand | New `brand.yaml` + optional visual tweaks, not new codebase |

---

## Immediate next steps (grounded)

1. Implement niche/brand YAML loader (read-only)
2. Add `--niche` / `--brand` flags to CLI (**optional**, default whisprs stack)
3. Tag synthesis reports with active profile IDs
4. Complete `channel_discovery.py` in core
5. Prove second niche when first brand is validated manually

Do **not** skip to mass channel factory before Phase C proof.

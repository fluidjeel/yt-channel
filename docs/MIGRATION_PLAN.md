# Migration Plan — 3-Layer Architecture

> **Rule:** Do not break `python main.py "URL"` until explicit cutover phase.  
> **Current:** All runnable code stays in `channel_analyzer/` and `main.py`.

---

## Mapping: today → target

| Today (SHIPPED) | Target layer | Target path |
|-----------------|--------------|-------------|
| `channel_analyzer/discovery.py` | L1 discovery | `content_intelligence_core/discovery/` |
| `channel_analyzer/performance.py` | L1 discovery | same |
| `channel_analyzer/downloader.py` | L1 discovery | same |
| `channel_analyzer/*_analysis.py` | L1 analysis | `content_intelligence_core/analysis/` |
| `channel_analyzer/report.py` | L1 synthesis | `content_intelligence_core/synthesis/` |
| `channel_analyzer/bonus.py` | L1 synthesis | same |
| `market_intelligence/*` | L1 discovery + knowledge | merge when implemented |
| `docs/07–10_*.md` | L2 reference | → `niches/emotional_healing/*.yaml` |
| Whisprs style notes | L3 reference | → `brands/whisprs_style/brand.yaml` |

---

## Migration phases

### M0 — Architecture only **DONE**

- [x] Create `content_intelligence_core/` README tree
- [x] Create `niches/emotional_healing/` profiles
- [x] Create `brands/whisprs_style/brand.yaml`
- [x] Schemas + architecture docs
- [x] No changes to `channel_analyzer/` behavior

### M1 — Profile loader **NEXT**

- [ ] `content_intelligence_core/profiles/loader.py` — load niche + brand YAML
- [ ] Validate against `schemas/`
- [ ] Unit tests with `emotional_healing` + `whisprs_style`
- [ ] CLI: optional `--niche`, `--brand` (defaults from registry)
- [ ] Playbook footer: `active_niche`, `active_brand` metadata

**No module moves yet.**

### M2 — Interpretation layer

- [ ] Post-process reports: map generic signals → niche taxonomy labels
- [ ] `evaluation/scorer.py` stub using `quality_rules.yaml`
- [ ] Keep analyzers niche-neutral; tagging happens after step 9

### M3 — Physical module move

- [ ] Copy (then re-export) modules into `content_intelligence_core/`
- [ ] `channel_analyzer/` becomes thin compatibility shim:

  ```python
  # channel_analyzer/discovery.py
  from content_intelligence_core.discovery.channel import discover_channel
  ```

- [ ] Update imports incrementally; run smoke test after each step

### M4 — market_intelligence merge

- [ ] Move MI into `content_intelligence_core/discovery/competitors.py`
- [ ] Deprecate top-level `market_intelligence/` package

### M5 — Cutover

- [ ] Remove shim when all tests pass
- [ ] Update `CURRENT_STATE.md` paths
- [ ] Optional: rename repo display name only (not required for git)

---

## What NOT to do during migration

- Big-bang rename breaking imports
- Embed niche YAML content into Python constants
- Move files without compatibility re-exports
- Claim migration complete before M5 tests pass

---

## Compatibility contract (until M5)

```bash
python main.py "https://www.youtube.com/@channel"
```

Must produce identical artifact paths:

- `data/videos.csv`
- `reports/channel_playbook.md`
- etc.

New metadata lines (niche/brand IDs) are additive only.

---

## Config evolution **PLANNED**

```yaml
# config.yaml (future)
platform:
  active_niche: emotional_healing
  active_brand: whisprs_style
```

Loader reads registries:

- `niches/registry.yaml`
- `brands/registry.yaml`

---

## Documentation updates per phase

| Phase | Update |
|-------|--------|
| M0 | ARCHITECTURE_VISION, this file |
| M1 | CURRENT_STATE, 04_Roadmap |
| M3 | README, 03_Architecture |
| M5 | Remove "compat shim" notes |

---

## Cursor task prompt (when ready for M1)

See `prompts/VIBE_CODING.md` → "Implement niche/brand profile loader (M1)".

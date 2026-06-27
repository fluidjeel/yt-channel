# Brand DNA Specification

> Layer 3 contract. Differentiates channels **within the same niche**.

---

## Why brands exist

Two "emotional healing" channels can share a niche profile but feel completely different:

| Brand | Voice | Visual | Pace |
|-------|-------|--------|------|
| whisprs_style | poetic | anime lo-fi | slow |
| (hypothetical) stoic_minimal | blunt aphorism | monochrome photo | medium |

Same Core + same Niche + different Brand = different fingerprint.

---

## Folder layout

```
brands/
├── registry.yaml
└── {brand_id}/
    └── brand.yaml
```

JSON Schema: `schemas/brand/brand.schema.json`

---

## brand.yaml required sections

| Section | Purpose |
|---------|---------|
| `id`, `name`, `niche_id`, `version`, `status` | Identity & link to Layer 2 |
| `voice` | style, tone, pace, avoid list |
| `narration_identity` | delivery, pauses, voice traits |
| `visual_identity` | family (e.g. anime_lofi, cinematic_horror), signature elements |
| `pacing` | video tempo, scene duration, cut frequency |
| `music_identity` | genre, layers, volume vs voice |
| `motion_identity` | motion budget, signature moves, avoid |
| `typography_identity` | fonts, placement (if applicable) |

Optional: `branding_elements`, `content_formula`, `sources`

---

## Reference implementation

**SHIPPED as YAML:** `brands/whisprs_style/brand.yaml`  
- `niche_id: emotional_healing`  
- Poetic voice, anime lo-fi visual, slow pace, ambient music

---

## Example contrasts (placeholders)

### dark_lantern (horror)

```yaml
voice:
  style: ominous_whisper
  pace: medium
visual_identity:
  family: cinematic_horror
music_identity:
  genre: tension
  layers: [drone, stingers]
```

### neural_brief (tech_reviews)

```yaml
voice:
  style: concise_analytical
  pace: fast
visual_identity:
  family: clean_motion_graphics
music_identity:
  genre: upbeat_corporate_light
```

---

## Composition at generation time **PLANNED**

```
prompt_context = merge(
  core_artifact_summary,
  load_niche(niche_id),
  load_brand(brand_id),
)
```

Evaluation uses `niches/{id}/quality_rules.yaml` **and** brand-specific overrides if present.

---

## Registry

`brands/registry.yaml` maps `brand_id` → path + `niche_id`.

A brand **must** reference a valid niche.

---

## Checklist for new brand

- [ ] Create `brands/{id}/brand.yaml`
- [ ] Set `niche_id` to registered niche
- [ ] Register in `brands/registry.yaml`
- [ ] Verify distinct voice/visual from other brands in same niche
- [ ] Do not duplicate niche taxonomy in brand file — reference niche for themes/arcs

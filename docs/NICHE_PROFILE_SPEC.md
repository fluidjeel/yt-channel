# Niche Profile Specification

> Layer 2 contract. Core (Layer 1) loads these by `niche_id` — never embeds niche content in Python.

---

## Folder layout

```
niches/
├── registry.yaml
└── {niche_id}/
    ├── taxonomy.yaml
    ├── persona.yaml
    ├── emotion_model.yaml
    ├── visual_model.yaml
    ├── narrative_model.yaml
    └── quality_rules.yaml
```

JSON Schema: `schemas/niche/niche_profile.schema.json`

---

## File responsibilities

### taxonomy.yaml

- `id`, `name`, `version`, `status`
- `description`, `audience_needs`
- `content_themes` (primary / secondary)
- `narrative_arcs` (id + label)
- `symbolism` (element → meaning map)
- Optional: `performance_signals`, `sources`

### persona.yaml

- `primary_persona` (mindset, pain_points, desires, language_style)
- `secondary_personas`
- Optional: `comment_sentiment_targets`

### emotion_model.yaml

- `intensity_scale` (target range, rules)
- `dominant_emotions`
- `dual_emotion_pairs` (primary, secondary, expression)
- `expression_channels` (eyes, mouth, posture)
- Optional: `cultural_notes`, `forbidden`

### visual_model.yaml

- `visual_language` (tags)
- `character_archetypes`, `environments`
- `composition_templates`
- `color_palettes`, `lighting`, `texture_stack`
- `canvas`, `typography`, `motion_defaults`

### narrative_model.yaml

- `structure.default_arc` (hook → reflection → insight → resolution)
- `hook_patterns`, `pacing`, `voice_narrative_style`
- `narrative_arcs` with beats
- `forbidden` patterns

### quality_rules.yaml

- `evaluation_gates` (min scores)
- Per-modality checks: `visual_checks`, `emotional_checks`, `narrative_checks`, `audio_checks`, `motion_checks`
- `final_test_question`, `publish_block_if`

---

## Reference implementation

**SHIPPED as YAML:** `niches/emotional_healing/` (from Whisprs-style analysis)

**Placeholder:** `niches/horror/taxonomy.yaml` (stub only)

---

## Horror example (contrast)

```yaml
# taxonomy.yaml excerpt — horror niche (when built)
dominant_emotions: [fear, suspense, uncertainty]
narrative_arcs:
  - mystery_to_reveal
  - safety_to_danger
visual_language: [darkness, isolation, contrast]
```

Same six files. Different values. Core unchanged.

---

## Loader behavior **PLANNED**

```python
profile = load_niche("emotional_healing")
# Returns validated dict from six YAML files
```

Validation against schema before synthesis or generation.

---

## Adding a niche checklist

- [ ] Create `niches/{id}/` with all six files
- [ ] Register in `niches/registry.yaml`
- [ ] Add at least one brand in `brands/` or mark placeholder
- [ ] Do **not** modify Layer 1 with niche-specific strings
- [ ] Optional: reference doc in `docs/niches/{id}.md`

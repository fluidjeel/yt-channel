# Niche Profiles (Layer 2)

Specialization lives here — **not** in `content_intelligence_core/`.

Each niche is a folder with validated YAML profiles. The core platform loads a niche by ID (e.g. `emotional_healing`).

## Formula

```
Core artifacts + Niche profile + Brand DNA = Interpreted intelligence / generated content
```

## Registered niches

| ID | Status | Description |
|----|--------|-------------|
| `emotional_healing` | **REFERENCE** | Poetic reflection, dual-emotion, healing arcs — first profile |
| `horror` | **PLACEHOLDER** | Example profile structure only |
| `humor` | **PLACEHOLDER** | — |
| `tech_reviews` | **PLACEHOLDER** | — |

## Adding a niche

1. Copy `schemas/niche/_template/` or follow [NICHE_PROFILE_SPEC.md](../docs/NICHE_PROFILE_SPEC.md)
2. Add `niches/{id}/` with required YAML files
3. Register in `niches/registry.yaml`
4. Do **not** add niche terms to Layer 1 Python modules

## Spec

- [docs/NICHE_PROFILE_SPEC.md](../docs/NICHE_PROFILE_SPEC.md)
- JSON Schema: `schemas/niche/niche_profile.schema.json`

# Emotional Taxonomy

> **Status:** **REFERENCE** — target niche ontology.  
> Not fully implemented in code; `emotion_analysis.py` uses overlapping hardcoded seeds + clustering.

Use this when tuning analyzers, LLM prompts, or future generators for **emotional lo-fi anime Shorts**.

---

## Primary emotions

Hope · Healing · Love · Loneliness · Purpose · Growth · Acceptance · Resilience · Self-worth · Gratitude · Faith · Belonging

---

## Secondary emotions

Longing · Nostalgia · Reflection · Wonder · Melancholy · Determination · Patience · Forgiveness · Inner peace

---

## Dual-emotion pairings (core creative rule)

Characters should show **transition emotions**, not extremes (target intensity 3–5/10).

| Emotion A | Emotion B | Viewer read |
|-----------|-----------|-------------|
| Love | Acceptance | Deep love, not desperate |
| Sadness | Hope | Hurts, will survive |
| Loneliness | Peace | Alone, okay for now |
| Exhaustion | Determination | Tired, still moving |
| Longing | Self-respect | Miss you, don't need you |
| Pain | Growth | Changed, learned |
| Fear | Courage | Afraid, acting anyway |
| Happiness | Reflection | Quiet gratitude, not laughing |
| Grief | Gratitude | Loss acknowledged |

**Master character line:** *Experienced pain, learned something, still believes tomorrow can be better.*

---

## East Asian emotional storytelling **REFERENCE**

Prefer internal carrying over external breakdown:

- Looking away, silence, small gestures
- Eyes carry emotion; mouth stays neutral or slight curve
- Avoid exaggerated crying, screaming joy, anime shock faces

---

## Mapping to pipeline **PARTIAL**

`config.yaml` lists 8 dimensions (hope, loneliness, love, healing, growth, spirituality, self-worth, acceptance) but code uses `EMOTION_SEEDS` in `emotion_analysis.py` — align in Phase 2.

---

## For future LLM synthesis **PLANNED**

When generating scripts or image prompts, always specify **two** emotions from the pairing table, never a single pure emotion at 9/10 intensity.

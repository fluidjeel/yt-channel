# Visual Taxonomy

> **Status:** **REFERENCE** — target style ontology (Whisprs / emotional lo-fi anime Shorts).  
> Current `visual_analysis.py` only approximates: colors, brightness, coarse scene labels.

---

## Art direction **REFERENCE**

Not traditional anime — **emotional visual poetry**:

- Minimalist lo-fi anime / manga silhouettes / painterly digital
- Clean outlines, low facial detail, simplified anatomy
- Imperfect hand-drawn lines; matte, grainy finish
- Emotion > technical detail

---

## Character types

| Archetype | Visual cues | Themes |
|-----------|---------------|--------|
| Quiet Thinker | Sky gaze, side profile | Reflection, existence |
| Hopeful Dreamer | Window, sunset | Future, healing |
| Wounded Soul | Hidden face, blindfold | Pain + standing |
| Traveler | Roads, stairs, bridges | Growth, journey |
| Ordinary Girl | Soft smile, everyday clothes | Connection, comfort |
| Elder Sage | Warm light, stillness | Wisdom (Rumi-style) |

**Demographics:** Predominantly East Asian–inspired, ages 18–30, ordinary clothing (hoodies, sweaters).

---

## Environments

Ocean · Field · Forest · Mountain · Rooftop · Window · Waterfall · Sky · Cloudscape · Night street · Moonlit horizon · Telephone poles

---

## Composition templates

| Template | Layout | Emotion |
|----------|--------|---------|
| A — Tiny human | Character 15–25%, environment 75–85% | Humility, wonder |
| B — Portrait | Character 50–70% | Face-forward emotion |
| C — Window observer | Character + frame | Hope |
| D — Journey | Path, motion implied | Growth |
| E — Metaphor | Stairs to clouds, surreal scale | Spirituality |

Rules: one focal subject, 40–80% negative space, vertical 9:16, rule of thirds.

---

## Color palettes

| Name | Colors | Mood |
|------|--------|------|
| Reflection | Teal + orange | Wisdom, healing |
| Longing | Navy + amber | Distance, memory |
| Spiritual | Teal + white | Faith, meaning |
| Connection | Warm skin + muted teal | Intimacy |
| Dream | Pink clouds + cyan sky | Wonder |

Grading: 70–85% saturation, low contrast, lifted blacks, teal shadows, amber highlights.

---

## Lighting

Sunset (most common) · Window light · Overcast · Moonlight · Golden hour · Fog

Always soft — no harsh spotlights.

---

## Texture stack **REFERENCE** (post-process target)

1. Paper texture 5–10%
2. Film grain 15–25%
3. Sparse dust/scratches
4. Light atmospheric haze
5. Subtle vignette

---

## Symbolism library

| Element | Meaning |
|---------|---------|
| Moon | Distance |
| Clouds | Possibility |
| Waterfall | Overwhelm |
| Ocean | Reflection |
| Tree | Endurance |
| Window | Hope |
| Road | Journey |
| Bridge | Transition |
| Stairs | Growth |
| Field | Solitude |
| Rain | Healing |
| Sunrise | New beginning |
| Sunset | Acceptance |

---

## Typography **REFERENCE** (not detected in code)

Handwritten cursive, off-white, upper-middle negative space, subtle shadow — never over faces.

---

## Gap vs analyzer **honest**

To detect this taxonomy automatically requires **PLANNED** work: palette classifier, composition metrics, optional vision LLM on downsampled frames — not current OpenCV heuristics alone.

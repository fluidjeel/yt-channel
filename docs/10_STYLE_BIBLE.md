# Style Bible — Emotional Lo-Fi Anime (Whisprs-style)

> **Status:** **REFERENCE** — reverse-engineered from channel analysis.  
> **Machine-readable profiles:** `niches/emotional_healing/` + `brands/whisprs_style/brand.yaml`  
> Platform architecture: [ARCHITECTURE_VISION.md](./ARCHITECTURE_VISION.md)

---

## Executive summary

The product is **emotional resonance**, not anime art. Viewers should think: *"I know this feeling."*

```
Ordinary East Asian character
+ Subtle dual-emotion (3–5/10 intensity)
+ Large negative space (40–80%)
+ Atmospheric environment
+ Soft lighting
+ Painterly anime + heavy grain/dust
+ Muted teal-orange grade
+ Visual symbolism
+ Memory-like atmosphere
= Emotional lo-fi visual poetry
```

---

## Core philosophy

Images should feel like: a memory, quiet conversation, journal page, moment between pain and healing.

Never: dramatic, loud, flashy, heroic, exaggerated.

Always: quiet, reflective, gentle, human, hopeful despite hardship.

---

## Emotional matrix

See [07_EmotionalTaxonomy.md](./07_EmotionalTaxonomy.md) for full pairing table.

**Rule:** Every character carries pain + hope simultaneously.

---

## Character design

- East Asian–inspired, subtle natural features
- Age 18–30 (occasional elder sage)
- Messy bob / loose hair, wind-blown strands
- Hoodies, sweaters, plain shirts — no luxury fashion
- Eyes = main emotion carrier; mouth neutral or slight curve

---

## Composition

| Template | Use |
|----------|-----|
| Tiny human + vast sky | Existential quotes |
| Portrait 50–70% | Face-heavy engagement |
| Window observer | Hope, healing |
| Journey (road/stairs) | Growth |
| Visual metaphor | Spirituality, destiny |

One subject only. Clear focal point. Vertical 9:16 (1080×1920).

Safe zones: top 15% UI; upper-middle quote; bottom 10–15% minimal detail.

---

## Color & light

**Palettes:** Teal+orange (default), navy+amber, teal+white, pink+cyan for dream scenes.

**Light:** sunset, window, overcast, moonlight — all diffused.

**Grade:** muted saturation, low contrast, lifted blacks, teal shadows, amber highlights.

---

## Texture stack (critical)

Film grain + paper texture + dust + soft haze + mild vignette = ~40% of the "premium" feel.

Nothing razor-sharp. Matte finish throughout.

---

## Rendering

Painterly anime: soft 2-step shading (base → soft shadow → ambient bounce). Imperfect outlines. Hair lines thinner than clothing lines.

Detail budget: high texture, medium face/hair, low clothing, low sky complexity.

---

## Typography

Handwritten cursive, off-white, centered in negative space, subtle shadow — integrated, not slapped on.

---

## Symbolism

Moon=distance · Clouds=possibility · Waterfall=overwhelm · Window=hope · Tree=endurance · Stairs=growth · Field=solitude

---

## Virality mechanics **REFERENCE**

Optimized for **emotional resonance per second**:

1. Stop scroll (memory-like image)
2. Feel something personal
3. Read quote
4. Share with someone who needs it

Formula:

```
Simple character + huge environment + soft palette + heavy grain
+ reflective quote + negative space + melancholy mood → retention
```

---

## Master prompt keywords

Use in `master_prompt_library.md` or image APIs:

```text
painterly anime illustration, east asian inspired character,
quiet emotional realism, soft atmospheric lighting,
film grain, paper texture, matte color grading,
teal and amber palette, subtle melancholy, hopeful expression,
large negative space, single focal subject, visual poetry,
nostalgic mood, soft shadows, clean silhouette,
minimalist composition, dreamlike atmosphere, memory-like scene,
gentle emotional storytelling, vertical 9:16 composition
```

---

## Ranked importance

1. Negative space  
2. Color palette  
3. Film grain / texture  
4. Solitary character  
5. Atmospheric sky  
6. Soft lighting  
7. Typography integration  
8. Minimal facial detail  

---

## Production workflow **REFERENCE** (target channel)

```
Quote theme → visual metaphor → character emotion → palette
→ composition → render → grain grade → text overlay
→ (optional) micro-motion → poetic narration + ambient audio
```

---

## What the pipeline captures today **honest**

Steps 5 and 11 give: dominant colors, sample frames, heuristic prompts.  
They do **not** automatically enforce this bible — human or LLM synthesis **PLANNED** on top of reports.

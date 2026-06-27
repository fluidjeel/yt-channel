# Motion Bible

> **Status:** **REFERENCE + PLANNED** — no `motion_analysis.py` exists yet.  
> Use when building motion analysis or video composition in Phase 3+.

---

## Motion philosophy

Target niche uses **micro-motion** — viewer almost asks "is this animated?"

```
Motion budget:   10–20%
Stillness:       80–90%
```

Excessive movement reads as cheap AI video. Restraint = premium feel.

---

## Motion types

### Camera

Push in · Pull out · Slow pan · Tilt · Static · Very slow orbit

**Avoid:** aggressive angles, action cuts, handheld shake

### Character

Breathing · occasional blink · hair drift · clothing micro-move · slow walk

### Environment

Cloud drift (1–3%/frame feel) · rain · falling particles · water ripple · fog drift · dust motes

---

## Emotional → motion mapping **REFERENCE**

| Emotion | Motion language |
|---------|-----------------|
| Hope | Rising clouds, upward camera, light expansion |
| Longing | Slow push-in, wind in hair, distant drift |
| Healing | Rain, gentle particles, soft environmental sway |
| Growth | Forward walk, forward camera, expanding horizon |
| Reflection | Near-static, ambient drift only |
| Wonder | Upward motion, cloud glow pulse |
| Loneliness | Static character, vast slow sky |

---

## Production tiers **REFERENCE**

| Tier | Technique | Effort |
|------|-----------|--------|
| 1 | Ken Burns + layered parallax on still | Low |
| 2 | Image-to-video AI (Runway, Luma, Kling) | Medium |
| 3 | Hybrid: decompose layers → plan motion → compose | High (target for agentic system) |

---

## Planned analyzer metrics **PLANNED**

When implementing `motion_analysis.py`, measure per video:

- Zoom rate (scale change over time)
- Pan velocity
- Cut frequency / scene duration
- Optical flow magnitude (overall motion energy)
- Region-specific flow (sky vs character)

Output: `reports/motion_analysis.md` + entries in playbook

---

## Planned composer **PLANNED**

`Motion Director` agent output schema (future):

```yaml
camera: slow_push_in
duration_sec: 4.2
layers:
  - id: sky
    motion: drift_right
    speed: 0.02
  - id: character
    motion: subtle_breathing
  - id: particles
    motion: float_up
    density: medium
```

Composer: MoviePy or ffmpeg filter graphs — not built.

---

## Integration with audio **REFERENCE**

Motion should follow narration pacing:

- Pauses → hold camera
- Emotional peak → minimal motion increase, not cuts
- Ambient rain/wind in audio → match particle layers

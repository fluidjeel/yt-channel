# Analysis — Layer 1

**Purpose:** Extract signals from media and text. Outputs structured artifacts only — no niche labels hardcoded in core.

**Planned analyzers:**
- Visual (frames, color, composition metrics)
- Audio (transcription, music features)
- Comments (sentiment, themes) — **PLANNED**
- Narrative (structure, hooks)
- Motion (camera, flow) — **PLANNED**

**Current implementation:**
- `channel_analyzer/audio_analysis.py`
- `channel_analyzer/visual_analysis.py`
- `channel_analyzer/emotion_analysis.py`
- `channel_analyzer/narrative_analysis.py`
- `channel_analyzer/music_analysis.py`
- `channel_analyzer/quote_analysis.py`

Niche-specific *interpretation* of analysis output uses `niches/{id}/` profiles.

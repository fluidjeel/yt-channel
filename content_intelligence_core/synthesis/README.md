# Synthesis — Layer 1

**Purpose:** Turn analysis artifacts into bibles, personas, and content DNA summaries.

**Planned outputs:**
- Channel / niche bibles
- Audience personas
- Content DNA documents

**Current implementation:** `channel_analyzer/report.py`, `bonus.py`  
**Planned:** LLM synthesis via `channel_analyzer/llm/` + token economics (DeepSeek extract → Claude synthesize).

Synthesis **templates** are niche-neutral; **content** is filled using active niche profile from config.

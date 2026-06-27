# Token Economics

> **Status:** Policy for all **PLANNED** LLM work. Core pipeline steps 1–11 remain **local** (no API spend).  
> Goal: Cursor builds the machinery; **your API keys** run intelligence at scale — without burning Cursor Pro quota on bulk analysis.

---

## The mistake to avoid

Using Cursor's premium models to:

- Analyze thousands of comments
- Read hundreds of full reports end-to-end
- Classify every transcript chunk with Claude
- Re-synthesize the same channel on every vibe-coding session

That burns monthly Cursor allocation fast. Channel analysis workload belongs in **your** API billing with a **tiered** model strategy.

---

## Split: Cursor vs your APIs

### Cursor included models → **software only**

| Use for | Examples |
|---------|----------|
| Coding | New modules, parsers, refactors |
| Tests | pytest, mocks, schema tests |
| Architecture | Provider abstraction, config wiring |
| Bug fixes | Pipeline steps 1–11 |
| Plumbing | `LLMProvider`, CLI flags, artifact I/O |

**Good Cursor tasks:**

- Build comment analyzer **module**
- Build knowledge graph **code**
- Build discovery engine
- Build style evidence engine

Cursor writes the machine; it does not run 1000-comment classification inside the chat.

### Your API keys → **intelligence workload**

| Use for | Examples |
|---------|----------|
| Bulk extraction | Comment themes, emotion tags |
| Final synthesis | Master bibles, personas |
| Generation planning | Prompt packs, taxonomies |
| Sparse research | Trend / competitor scans |

**Run via scripts** (e.g. `python -m tools.synthesize ...`), not by pasting entire `reports/` trees into Cursor chat.

---

## Model allocation (default policy)

| Task | Provider | Rationale |
|------|----------|-----------|
| **Coding** | Cursor included | Best ROI for dev |
| **Bulk classification** | DeepSeek | ~80% cheaper than Claude for tagging/clustering |
| **Final synthesis** | Claude | Master bibles, cross-channel synthesis, audience persona |
| **Prompt / plan generation** | GPT (OpenAI) | Structured outputs, prompt engineering, agent plans |
| **Trend / competitor research** | Grok | Sparingly — real-time context |
| **Steps 1–11 today** | Local only | Whisper, sentence-transformers, OpenCV — $0 API |

### DeepSeek — first pass on volume

- Comment clustering
- Emotion tagging
- Theme classification
- Bulk labeling
- Extract structured JSON from long text

### Claude — reserve for high-value synthesis

- `master_visual_bible.md`
- `master_emotional_bible.md`
- `audience_persona.md`
- Cross-channel synthesis (from **summaries**, not raw dumps)

### GPT — generation & structure

- Prompt engineering
- Generation planning
- Taxonomy generation
- Agent / pipeline planning

### Grok — sparse

- Trend discovery
- Competitor research
- Emerging channel signals

---

## Required pipeline pattern **PLANNED**

Never: `Raw reports → Claude (everything)`

Always: **compress before synthesize**

```
Raw artifacts (reports, comments.csv, transcripts)
        ↓
DeepSeek extraction  →  structured JSON (counts, labels, clusters)
        ↓
Optional GPT         →  prompt packs / plans (if needed)
        ↓
Claude synthesis     →  final bibles (small input)
        ↓
Versioned artifacts  →  reports/synthesis/
```

**Example:** 1000 comments

1. DeepSeek → `{ "self_love": 23, "healing": 14, "gratitude": 18, ... }`
2. Claude receives **summary JSON only** → `audience_persona.md`

---

## Provider abstraction **PLANNED**

Implement once under `channel_analyzer/llm/` (see README there). Config in `config.yaml` → `llm:` block.

```yaml
llm:
  analysis_provider: anthropic      # final synthesis
  classification_provider: deepseek # bulk work
  generation_provider: openai
  research_provider: grok
```

Every call goes through provider interface — never hardcode `anthropic.messages.create` in step modules.

---

## Per-call discipline

Before any LLM API call in code or docs:

1. **Estimate** input tokens (chars / 4 rough)
2. **Estimate** cost (provider price sheet)
3. **State expected value** (e.g. "replaces 50 manual labels")
4. **Cache** result under `artifacts/llm_cache/{provider}/{hash}.json`
5. **Log** provider + model + token count in artifact metadata

### Hard rules

- **Never** use premium models (Claude/GPT-4 class) for large-scale classification
- **Prefer** local models (Whisper, sentence-transformers) or DeepSeek first
- **Reserve** Claude for synthesis on **compressed** inputs
- **Reserve** GPT for generation / structured planning
- **Do not** send raw video frames to any LLM
- **Do not** paste full `reports/` into Cursor chat for "analysis" — run scripts with API keys

---

## 30-day default schedule

| Task | Where it runs |
|------|----------------|
| Pipeline code, tests, refactors | Cursor included models |
| Comment/theme bulk labeling | DeepSeek API (script) |
| Style / emotional / audience bibles | Claude API (script, summary in) |
| Prompt libraries, taxonomies | GPT API (script) |
| Trend scans | Grok API (script, occasional) |
| Transcription, embeddings, vision heuristics | Local (steps 1–11) |

---

## Cursor vibe-coding checklist

When adding LLM features:

- [ ] Uses provider abstraction + `config.yaml` `llm:` routing
- [ ] Bulk step uses `classification_provider` (DeepSeek)
- [ ] Synthesis step uses `analysis_provider` (Claude) on JSON summaries only
- [ ] Outputs cached with hash key
- [ ] Documented in `CURRENT_STATE.md` as **PARTIAL** when wired
- [ ] README states approximate cost per channel run

See also: [`prompts/VIBE_CODING.md`](../prompts/VIBE_CODING.md) — LLM prompts section.

# Vibe Coding Prompts

Copy-paste prompts for Cursor. Each prompt states **scope** so the model does not build future phases.

---

## Prompt: Fix or extend current pipeline only

```
Read docs/CURRENT_STATE.md and docs/NON_GOALS.md first.

Task: [describe bug or small enhancement in channel_analyzer steps 1-11]

Rules:
- Do NOT add generation agents, LLM APIs, or market_intelligence pipeline unless I explicitly ask
- Follow docs/TOKEN_ECONOMICS.md — Cursor for code only; bulk LLM via user API scripts
- Update docs/CURRENT_STATE.md if behavior changes
- Add tests if touching ranking or CSV schemas
```

---

## Prompt: Run analysis on a channel (human task)

```
No code changes. Run:
python main.py "https://www.youtube.com/@CHANNEL" --from 1 --to 3
Review data/videos.csv and top_videos.csv, then full run if disk/time OK.
```

---

## Prompt: Implement market intelligence Phase 2a (discovery only) **PLANNED**

```
Read docs/CURRENT_STATE.md — market_intelligence is SCaffold only.

Implement ONLY market_intelligence/channel_discovery.py:
- Input: seed channel URL
- Output: data/discovered_channels.csv (schema in docs/06_DataModel.md)
- Reuse yt_helpers.py and storage.py
- Add tests/tests/test_channel_discovery.py with mocks
- Do NOT implement similarity, knowledge graph, or dashboard yet
- Add CLI subcommand or separate main entry only if minimal change to main.py
- Update docs/CURRENT_STATE.md when done

Do not claim Phase 3/4 generation features exist.
```

---

## Prompt: Add motion analysis step **PLANNED — user must approve**

```
Read docs/09_MotionBible.md (REFERENCE) and docs/CURRENT_STATE.md.

Add channel_analyzer/motion_analysis.py as Step 12 OR extend step 5:
- Input: artifacts/downloads/{id}/*.mp4
- Output: reports/motion_analysis.md
- Use OpenCV optical flow / frame diff — no cloud LLM
- Wire in pipeline.py + update docs

Do not build video generation or Motion Director agent yet.
```

---

## Prompt: LLM style bible from existing reports **PLANNED**

```
Read docs/TOKEN_ECONOMICS.md and docs/CURRENT_STATE.md — no LLM in default pipeline today.

Implement token-efficient synthesis (NOT bulk analysis in Cursor chat):

1. channel_analyzer/llm/ provider abstraction (base + anthropic + deepseek + openai + grok stubs)
2. Read config.yaml llm: block for routing
3. tools/synthesize_bibles.py:
   - Step A: DeepSeek extracts structured JSON from reports/*.md (classification_provider)
   - Step B: Claude synthesizes final bible from JSON only (analysis_provider)
   - Cache each step under artifacts/llm_cache/{provider}/{hash}.json
   - Log estimated tokens + cost per call
4. Output: reports/synthesis/master_emotional_bible.md (etc.)

Rules:
- Never send full raw comment dumps to Claude
- Never hardcode API keys
- Document as PARTIAL in CURRENT_STATE.md when wired
```

---

## Prompt: Build LLM provider plumbing only **PLANNED**

```
Read docs/TOKEN_ECONOMICS.md and channel_analyzer/llm/README.md.

Implement provider abstraction ONLY — no synthesis scripts yet:
- channel_analyzer/llm/base.py (LLMProvider protocol)
- channel_analyzer/llm/providers/{anthropic,openai,deepseek,grok}.py
- channel_analyzer/llm/router.py reads config.yaml llm:
- channel_analyzer/llm/cache.py + cost.py helpers
- Unit tests with mocked HTTP — no real API calls in CI

Do NOT wire into pipeline steps 1-11.
Do NOT use Cursor to analyze reports — only write the code.
Update docs/CURRENT_STATE.md when done.
```

---

## Prompt: M1 — Niche/brand profile loader **NEXT**

```
Read docs/MIGRATION_PLAN.md (M1), docs/NICHE_PROFILE_SPEC.md, docs/BRAND_DNA_SPEC.md, docs/CURRENT_STATE.md.

Implement ONLY migration phase M1:

1. content_intelligence_core/profiles/loader.py
   - load_niche(niche_id) → merged dict from niches/{id}/*.yaml
   - load_brand(brand_id) → brand.yaml + validate niche_id match
   - load_stack(niche_id, brand_id) → combined context for synthesis
2. Read platform.active_niche / active_brand from config.yaml (defaults from registries)
3. Optional CLI flags: --niche, --brand (defaults: emotional_healing, whisprs_style)
4. Append to channel_playbook.md footer: active_niche, active_brand IDs
5. Unit tests: tests/test_profile_loader.py

Rules:
- Do NOT move channel_analyzer modules yet (no M3)
- Do NOT break existing pipeline outputs
- Do NOT embed YAML content as Python constants
- Update docs/CURRENT_STATE.md when done
```

---

## Prompt: Add second niche profile (Phase C prep) **PLANNED**

```
Read docs/NICHE_PROFILE_SPEC.md and copy structure from niches/emotional_healing/.

Create full profile for niches/horror/ (all 6 YAML files) + brands/dark_lantern/brand.yaml.
Register in registries. Horror example themes: fear, suspense, mystery_to_reveal.

Do NOT modify channel_analyzer analyzers with horror-specific code.
Do NOT claim second niche is validated until pipeline run with profile loader.
```

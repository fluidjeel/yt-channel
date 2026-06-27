# AGENTS.md — Cursor / AI Assistant Guide

## Start here

1. Read [`docs/CURRENT_STATE.md`](docs/CURRENT_STATE.md)
2. Read [`docs/ARCHITECTURE_VISION.md`](docs/ARCHITECTURE_VISION.md) for 3-layer model
3. Read [`docs/NON_GOALS.md`](docs/NON_GOALS.md)
4. Read [`docs/TOKEN_ECONOMICS.md`](docs/TOKEN_ECONOMICS.md) before any LLM work
5. Browse [`docs/00_INDEX.md`](docs/00_INDEX.md)

## Project in one sentence

**Universal Content Intelligence Platform** (3-layer architecture) with a **SHIPPED** single-channel CLI in `channel_analyzer/`.

```
Core + Niche + Brand = Content
```

Default reference stack: `emotional_healing` + `whisprs_style` (YAML only until M1 loader).

## Commands that work

```bash
python main.py --check-deps
python main.py "https://www.youtube.com/@channel"
python main.py "URL" --step 5
python main.py "URL" --from 4 --to 10
```

## Do not hallucinate

| Claim | Reality |
|-------|---------|
| Multi-channel discovery | **SCaffold** only |
| Profile loader / `--niche` `--brand` | **PLANNED** (M1) |
| Core code in `content_intelligence_core/` | **SCaffold** — still `channel_analyzer/` |
| Motion analysis | **PLANNED** |
| LLM API in pipeline | **Not wired** |
| Image/voice generation | **PLANNED** |
| `python -m channel_analyzer.discovery` | **Does not work** |

## Safe tasks for vibe coding

- Fix/enhance steps 1–11
- Add tests, fix config dead keys
- Implement `market_intelligence/channel_discovery.py` (one file at a time)
- Improve reports from existing artifacts

## Unsafe without explicit user ask

- Full agentic generation studio
- Fake dashboard / knowledge graph
- Rewriting entire architecture

## Niche reference (not auto-detected)

Whisprs-style emotional lo-fi anime: [`docs/10_STYLE_BIBLE.md`](docs/10_STYLE_BIBLE.md)

## Cursor rules

`.cursor/rules/project_context.mdc`, `anti_hallucination.mdc`, `token_economics.mdc`, `architecture.mdc`, `agents.mdc`, `llm_usage.mdc`, `coding_standards.mdc`

## Token economics (summary)

- **Cursor:** code, tests, refactors — not 1000-comment analysis in chat
- **Your APIs:** bulk work via scripts — DeepSeek → JSON → Claude synthesis
- Policy: [`docs/TOKEN_ECONOMICS.md`](docs/TOKEN_ECONOMICS.md)

# Non-Goals (unless user explicitly asks)

Cursor and contributors must **not** implement or claim the following exist without an explicit user request and an update to `CURRENT_STATE.md`.

## Do not hallucinate as "done"

- Multi-channel discovery pipeline
- Channel similarity scoring
- Cross-channel `common_patterns.md`
- Knowledge graph (`knowledge_graph.graphml`)
- Dashboard (`dashboard/summary.json`)
- Motion analysis module
- Comment scraping / audience psychology agent
- Script / image / voice / video **generation** agents
- Quality council / critic agents
- OpenAI / Anthropic / DeepSeek / Grok API integration
- Qdrant / PostgreSQL vector stores
- ComfyUI / Flux / SDXL local generation
- Uncached repeat synthesis of the same artifacts
- Pasting full `reports/` or large comment CSVs into Cursor chat for "analysis" (use API scripts per `docs/TOKEN_ECONOMICS.md`)
- Claiming `content_intelligence_core/` code migration is complete (profiles YAML ≠ core moved)
- Naming the platform after one brand (Whisprs = Layer 3 brand, not product name)

## Do not refactor prematurely

- Do not rewrite the 11-step pipeline as microservices
- Do not move `channel_analyzer/` without `docs/MIGRATION_PLAN.md` compat shims
- Do not hardcode niche terms (anime, healing, horror) in Layer 1 Python
- Do not add FastAPI/UI unless requested
- Do not replace heuristics with LLM calls "for quality" without approval (cost + scope)

## Do not merge future vision into current tasks

When the user asks to fix a bug or add a small feature:

- **Do not** also build Phase 3 generation stack
- **Do not** update docs to imply generation exists
- **Do not** create stub agents that look complete but return fake data

## Safe default next work (when user says "what's next")

1. M1 profile loader (`content_intelligence_core/profiles/loader.py`) — see `docs/MIGRATION_PLAN.md`
2. Run pipeline on 3–5 real channels; validate outputs
3. Finish `market_intelligence/channel_discovery.py` only
4. Add tests for ranking + CSV schemas + profile loading

## Doc hygiene

- Tag new sections: **SHIPPED** | **PARTIAL** | **PLANNED** | **REFERENCE**
- After shipping code, update `CURRENT_STATE.md` and `04_Roadmap.md`

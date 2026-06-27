# LLM Provider Layer — **PLANNED**

> Not wired to pipeline steps 1–11. See [`docs/TOKEN_ECONOMICS.md`](../../docs/TOKEN_ECONOMICS.md).

## Purpose

Single abstraction so intelligence workloads use **your API keys** with correct model routing — not Cursor quota for bulk work.

## Intended layout (implement when adding synthesis)

```
channel_analyzer/llm/
├── README.md           (this file)
├── base.py             LLMProvider protocol / ABC
├── providers/
│   ├── anthropic.py    ClaudeProvider — synthesis only
│   ├── openai.py       GPTProvider — generation / planning
│   ├── deepseek.py     DeepSeekProvider — bulk classification
│   └── grok.py         GrokProvider — research
├── router.py           reads config.yaml llm: block
├── cache.py            artifacts/llm_cache/{provider}/{hash}.json
└── cost.py             token estimate + log helper
```

## Config (`config.yaml` → `llm:`)

```yaml
llm:
  analysis_provider: anthropic
  classification_provider: deepseek
  generation_provider: openai
  research_provider: grok
```

Env vars (never commit): `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `DEEPSEEK_API_KEY`, `GROK_API_KEY` (or provider-specific names documented in config).

## Usage pattern

```python
# Bulk (cheap)
labels = router.classify(comments_batch)  # → DeepSeek

# Synthesize (expensive, small input)
bible = router.synthesize(summary_json)   # → Claude
```

Do not call providers from `discovery.py`, `visual_analysis.py`, etc. — only from dedicated `tools/` or `synthesis/` entry points.

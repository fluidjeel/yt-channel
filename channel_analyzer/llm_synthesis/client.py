"""Cached LLM client for text synthesis."""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path

from channel_analyzer.llm_synthesis.keys import load_api_keys

logger = logging.getLogger(__name__)

DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-4-20250514"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"


def _cache_path(cache_dir: Path, bible_id: str, source_hash: str) -> Path:
    return cache_dir / f"{bible_id}_{source_hash}.md"


def call_llm(
    prompt: str,
    cache_dir: Path,
    bible_id: str,
    source_hash: str,
    provider: str = "anthropic",
    max_tokens: int = 6000,
    force_refresh: bool = False,
) -> str | None:
    """
    Call Claude or GPT with caching. Returns markdown text or None on failure.
    """
    keys = load_api_keys()
    if provider == "anthropic" and not keys["anthropic"]:
        provider = "openai"
    if provider == "openai" and not keys["openai"]:
        if keys["anthropic"]:
            provider = "anthropic"
        else:
            logger.error("No LLM API keys found")
            return None

    cache_dir.mkdir(parents=True, exist_ok=True)
    path = _cache_path(cache_dir, bible_id, source_hash)
    if path.exists() and not force_refresh:
        logger.info("Cache hit: %s", path.name)
        return path.read_text(encoding="utf-8")

    try:
        if provider == "anthropic":
            text = _call_anthropic(keys["anthropic"], prompt, max_tokens)
        else:
            text = _call_openai(keys["openai"], prompt, max_tokens)
        if text:
            path.write_text(text, encoding="utf-8")
            logger.info("Wrote cache: %s", path.name)
        return text
    except Exception as exc:
        logger.error("LLM call failed for %s: %s", bible_id, exc)
        return None


def _call_anthropic(api_key: str, prompt: str, max_tokens: int) -> str:
    import httpx

    resp = httpx.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": DEFAULT_ANTHROPIC_MODEL,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=300,
    )
    resp.raise_for_status()
    return resp.json()["content"][0]["text"]


def _call_openai(api_key: str, prompt: str, max_tokens: int) -> str:
    import httpx

    resp = httpx.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": DEFAULT_OPENAI_MODEL,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=300,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]

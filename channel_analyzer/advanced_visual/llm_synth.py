"""Optional LLM synthesis layer — preprocessed thumbnails only, cached."""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
from io import BytesIO
from pathlib import Path

from PIL import Image

logger = logging.getLogger(__name__)

ENV_SEARCH_PATHS = [
    Path(__file__).resolve().parents[2] / ".env",
    Path.home() / ".env",
    Path("C:/Manasjit/ai/swarm-ai/.env"),
]


def load_api_keys() -> dict[str, str]:
    """Load API keys from environment or known .env locations (no hardcoded secrets)."""
    keys = {
        "openai": os.environ.get("OPENAI_API_KEY", ""),
        "anthropic": os.environ.get("ANTHROPIC_API_KEY", ""),
    }
    if keys["openai"] and keys["anthropic"]:
        return keys

    for env_path in ENV_SEARCH_PATHS:
        if not env_path.exists():
            continue
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k == "OPENAI_API_KEY" and not keys["openai"]:
                keys["openai"] = v
            if k == "ANTHROPIC_API_KEY" and not keys["anthropic"]:
                keys["anthropic"] = v
    return keys


def _thumbnail_b64(image: Image.Image, size: int = 384) -> str:
    """Resize and JPEG-encode — never send full-resolution frames."""
    img = image.copy()
    img.thumbnail((size, size))
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return base64.standard_b64encode(buf.getvalue()).decode("ascii")


def _cache_key(payload: str) -> str:
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def synthesize_insights(
    cache_dir: Path,
    aggregate_stats: dict,
    sample_thumbnails: list[Image.Image],
    provider: str = "anthropic",
) -> str | None:
    """
    Optional LLM pass to synthesize human-readable visual insights.
    Returns None if no API key or on failure.
    """
    keys = load_api_keys()
    if provider == "anthropic" and not keys["anthropic"]:
        provider = "openai"
    if provider == "openai" and not keys["openai"]:
        if keys["anthropic"]:
            provider = "anthropic"
        else:
            logger.info("No LLM API keys found — skipping vision synthesis")
            return None

    stats_json = json.dumps(aggregate_stats, indent=2, default=str)[:4000]
    cache_path = cache_dir / f"synthesis_{_cache_key(stats_json)}.md"
    if cache_path.exists():
        return cache_path.read_text(encoding="utf-8")

    thumbs = sample_thumbnails[:6]
    b64_images = [_thumbnail_b64(t) for t in thumbs]

    prompt = (
        "You are analyzing visual patterns in a poetry YouTube Shorts channel (anime-aesthetic). "
        "Given aggregate CLIP/heuristic stats and sample thumbnails, synthesize:\n"
        "1. Dominant character archetypes and what they signal emotionally\n"
        "2. Gaze and expression patterns (hopeful melancholy, quiet resilience, etc.)\n"
        "3. Composition patterns (tiny human / large world, negative space)\n"
        "4. Symbolism recurrence\n"
        "5. What high-performing vs lower-performing videos differ on visually\n"
        "6. What the creator likely does intentionally vs unconsciously\n\n"
        f"AGGREGATE STATS:\n{stats_json}\n\n"
        "Be specific and cite percentages from the stats. Do not invent data."
    )

    try:
        if provider == "anthropic":
            text = _call_anthropic(keys["anthropic"], prompt, b64_images)
        else:
            text = _call_openai(keys["openai"], prompt, b64_images)
        if text:
            cache_dir.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(text, encoding="utf-8")
        return text
    except Exception as exc:
        logger.warning("LLM synthesis failed: %s", exc)
        return None


def _call_anthropic(api_key: str, prompt: str, b64_images: list[str]) -> str:
    import httpx

    content: list[dict] = [{"type": "text", "text": prompt}]
    for b64 in b64_images:
        content.append(
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": b64,
                },
            }
        )
    resp = httpx.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 2000,
            "messages": [{"role": "user", "content": content}],
        },
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["content"][0]["text"]


def _call_openai(api_key: str, prompt: str, b64_images: list[str]) -> str:
    import httpx

    content: list[dict] = [{"type": "text", "text": prompt}]
    for b64 in b64_images:
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{b64}", "detail": "low"},
            }
        )
    resp = httpx.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": "gpt-4o-mini",
            "max_tokens": 2000,
            "messages": [{"role": "user", "content": content}],
        },
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]

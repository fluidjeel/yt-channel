"""API key loading — environment or known .env paths (no hardcoded secrets)."""

from __future__ import annotations

import os
from pathlib import Path

ENV_SEARCH_PATHS = [
    Path(__file__).resolve().parents[2] / ".env",
    Path("C:/Manasjit/ai/swarm-ai/.env"),
]


def load_api_keys() -> dict[str, str]:
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

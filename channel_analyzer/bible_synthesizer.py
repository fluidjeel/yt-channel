#!/usr/bin/env python3
"""
Claude Style Bible Synthesizer — master bibles from analyzer reports.

Architecture: collector -> synthesizer -> report

Usage:
  python -m channel_analyzer.bible_synthesizer
  python -m channel_analyzer.bible_synthesizer --bible emotional
  python -m channel_analyzer.bible_synthesizer --refresh
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Any

from channel_analyzer.config import Config, DEFAULT_CONFIG_PATH
from channel_analyzer.llm_synthesis.collector import collect_synthesis_context
from channel_analyzer.llm_synthesis.synthesizer import (
    BIBLE_OUTPUTS,
    SYNTHESIS_ORDER,
    synthesize_all_bibles,
)
from channel_analyzer.utils import setup_logging

logger = logging.getLogger(__name__)

BIBLE_ALIASES: dict[str, str] = {
    "visual": "master_visual_bible",
    "emotional": "master_emotional_bible",
    "emotion": "master_emotional_bible",
    "character": "master_character_bible",
    "narrative": "master_narrative_bible",
    "motion": "master_motion_bible",
    "persona": "audience_persona",
    "audience": "audience_persona",
    "dna": "content_dna",
    "content": "content_dna",
}


def _load_settings() -> dict[str, Any]:
    import yaml

    defaults = {
        "provider": "anthropic",
        "force_refresh": False,
    }
    if DEFAULT_CONFIG_PATH.exists():
        with open(DEFAULT_CONFIG_PATH, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        bs = data.get("bible_synthesis", {})
        defaults.update({k: v for k, v in bs.items() if v is not None})
    return defaults


def run_bible_synthesis(
    config: Config | None = None,
    bible_ids: list[str] | None = None,
    provider: str | None = None,
    force_refresh: bool = False,
) -> dict[str, Path]:
    """Run full bible synthesis pipeline."""
    config = config or Config.from_yaml()
    config.ensure_dirs()
    settings = _load_settings()

    provider = provider or settings.get("provider", "anthropic")
    if not force_refresh:
        force_refresh = bool(settings.get("force_refresh", False))

    ctx = collect_synthesis_context(config)
    if not ctx.reports:
        raise FileNotFoundError(
            f"No analyzer reports found in {config.reports_dir}. Run the core pipeline first."
        )

    cache_dir = config.llm_cache_dir / "bibles"
    return synthesize_all_bibles(
        ctx=ctx,
        reports_dir=config.reports_dir,
        cache_dir=cache_dir,
        provider=provider,
        force_refresh=force_refresh,
        bible_ids=bible_ids,
    )


def main(argv: list[str] | None = None) -> int:
    setup_logging()
    parser = argparse.ArgumentParser(description="Claude Style Bible Synthesizer")
    parser.add_argument("--config", type=str, help="Path to config.yaml")
    parser.add_argument(
        "--bible",
        action="append",
        dest="bibles",
        help=f"Bible to generate: {', '.join(BIBLE_ALIASES.keys())} (repeatable)",
    )
    parser.add_argument(
        "--provider",
        choices=["anthropic", "openai"],
        default=None,
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Ignore cache and regenerate",
    )
    args = parser.parse_args(argv)

    config_path = Path(args.config) if args.config else None
    config = Config.from_yaml(config_path)

    bible_ids: list[str] | None = None
    if args.bibles:
        bible_ids = []
        for b in args.bibles:
            key = b.lower().replace("-", "_")
            resolved = BIBLE_ALIASES.get(key, key)
            if resolved not in BIBLE_OUTPUTS:
                parser.error(f"Unknown bible: {b}. Choose from: {list(BIBLE_ALIASES.keys())}")
            bible_ids.append(resolved)
        # If content_dna requested, ensure dependencies run first unless only dna
        if "content_dna" in bible_ids and len(bible_ids) == 1:
            bible_ids = [x for x in SYNTHESIS_ORDER if x != "content_dna"] + ["content_dna"]

    results = run_bible_synthesis(
        config=config,
        bible_ids=bible_ids,
        provider=args.provider,
        force_refresh=args.refresh,
    )

    print("\nBible synthesis complete:")
    for name, path in results.items():
        print(f"  {name}: {path}")
    if not results:
        print("  No bibles generated — check API keys and reports.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

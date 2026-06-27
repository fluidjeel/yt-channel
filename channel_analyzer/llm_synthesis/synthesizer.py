"""Synthesize master bibles from analyzer context."""

from __future__ import annotations

import logging
from pathlib import Path

from channel_analyzer.llm_synthesis.client import call_llm
from channel_analyzer.llm_synthesis.collector import SynthesisContext
from channel_analyzer.llm_synthesis.prompts import (
    BIBLE_SPECS,
    build_bible_prompt,
    build_content_dna_prompt,
)
from channel_analyzer.utils import write_markdown

logger = logging.getLogger(__name__)

# bible_id -> output filename
BIBLE_OUTPUTS: dict[str, str] = {
    "master_visual_bible": "master_visual_bible.md",
    "master_emotional_bible": "master_emotional_bible.md",
    "master_character_bible": "master_character_bible.md",
    "master_narrative_bible": "master_narrative_bible.md",
    "master_motion_bible": "master_motion_bible.md",
    "audience_persona": "audience_persona.md",
    "content_dna": "content_dna.md",
}

SYNTHESIS_ORDER = [
    "master_visual_bible",
    "master_emotional_bible",
    "master_character_bible",
    "master_narrative_bible",
    "master_motion_bible",
    "audience_persona",
    # content_dna last — uses prior bibles
    "content_dna",
]


def synthesize_bible(
    ctx: SynthesisContext,
    bible_id: str,
    cache_dir: Path,
    provider: str = "anthropic",
    force_refresh: bool = False,
    prior_bibles: dict[str, str] | None = None,
) -> str | None:
    """Generate one bible document."""
    if bible_id == "content_dna" and prior_bibles:
        prompt = build_content_dna_prompt(ctx, prior_bibles)
    else:
        prompt = build_bible_prompt(ctx, bible_id)

    return call_llm(
        prompt=prompt,
        cache_dir=cache_dir,
        bible_id=bible_id,
        source_hash=ctx.source_hash,
        provider=provider,
        max_tokens=8000 if bible_id == "content_dna" else 6000,
        force_refresh=force_refresh,
    )


def synthesize_all_bibles(
    ctx: SynthesisContext,
    reports_dir: Path,
    cache_dir: Path,
    provider: str = "anthropic",
    force_refresh: bool = False,
    bible_ids: list[str] | None = None,
) -> dict[str, Path]:
    """Generate all master bibles and write to reports/."""
    ids = bible_ids or SYNTHESIS_ORDER
    prior: dict[str, str] = {}
    outputs: dict[str, Path] = {}

    for bible_id in ids:
        if bible_id not in BIBLE_OUTPUTS:
            logger.warning("Unknown bible_id: %s", bible_id)
            continue

        logger.info("Synthesizing %s...", bible_id)
        text = synthesize_bible(
            ctx,
            bible_id,
            cache_dir,
            provider=provider,
            force_refresh=force_refresh,
            prior_bibles=prior if bible_id == "content_dna" else None,
        )
        if not text:
            logger.error("Failed to synthesize %s", bible_id)
            continue

        prior[bible_id] = text
        title = BIBLE_SPECS.get(bible_id, {}).get("title", bible_id)
        out_path = reports_dir / BIBLE_OUTPUTS[bible_id]

        # Wrap with metadata header if not already a full doc
        sections = {
            "Document": text,
            "Metadata": (
                f"- **Source hash:** `{ctx.source_hash}`\n"
                f"- **Channel:** {ctx.channel_name}\n"
                f"- **Inputs:** {', '.join(sorted(ctx.reports.keys()))}\n"
                f"- **Synthesizer:** {provider}\n"
                f"- **Type:** {'interpretive synthesis — verify facts against raw reports' if bible_id != 'content_dna' else 'master formula — source of truth for generation'}"
            ),
        }
        write_markdown(out_path, title, sections)
        outputs[BIBLE_OUTPUTS[bible_id]] = out_path
        logger.info("Wrote %s", out_path)

    return outputs

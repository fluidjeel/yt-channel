"""Prompt templates for bible synthesis."""

from __future__ import annotations

from channel_analyzer.llm_synthesis.collector import SynthesisContext

STRUCTURE_RULES = """
REQUIRED OUTPUT STRUCTURE (use these exact ## headings):

## Executive Summary
2-4 sentences. What this bible defines and why it matters for content generation.

## Facts (Evidence-Based)
Bullet list. Each bullet MUST cite a source report in parentheses, e.g. (advanced_visual_analysis.md).
Include specific numbers/percentages ONLY if they appear in the source material.
Assign each fact a confidence tag: [HIGH], [MEDIUM], or [LOW].

## Interpretations
Bullet list. Clearly label as analyst inference, not raw data.
Assign confidence: [HIGH], [MEDIUM], or [LOW].

## Contradictions
List any tensions between reports. If none found, state "No major contradictions detected" and explain.

## Unknowns / Gaps
What the analyzer cannot yet confirm. Be explicit about missing data (e.g. no motion analysis yet).

## Generation Guidelines
Actionable rules for creating new content in this niche. Numbered list, 5-12 items.
Each guideline should be reusable by an image/video generation system.

## Taxonomy Candidates
New concept labels discovered (e.g. "Peaceful Sadness", "Recovery Content") that should become
formal taxonomy nodes for a future knowledge graph.

RULES:
- Never invent statistics. If uncertain, say so and mark [LOW].
- Separate facts from interpretations visually and linguistically.
- Write for a creator building anime-aesthetic recovery/self-worth Shorts, NOT generic motivation.
- The emerging emotional product is: Pain → Understanding → Acceptance → Growth (not revenge, not hype motivation).
"""


def _base_context(ctx: SynthesisContext) -> str:
    return (
        f"CHANNEL: {ctx.channel_name}\n\n"
        f"STRUCTURED DATA (CSV summaries):\n{ctx.csv_bundle()}\n\n"
        f"ANALYZER REPORTS:\n{ctx.report_bundle()}\n"
    )


BIBLE_SPECS: dict[str, dict[str, str]] = {
    "master_visual_bible": {
        "title": "Master Visual Bible",
        "focus": (
            "Synthesize ALL visual patterns: composition (tiny human/large world, negative space), "
            "color/lighting from visual_analysis.md, advanced visual archetypes, gaze, symbolism, "
            "anime style score, high-performer visual correlations. "
            "Define mandatory vs optional visual elements for generation."
        ),
    },
    "master_emotional_bible": {
        "title": "Master Emotional Bible",
        "focus": (
            "Synthesize the emotional journey across emotion_clusters.md, narrative_patterns.md, "
            "audience_psychology.md, quote_patterns.md. "
            "Define the core arc: Pain → Understanding → Acceptance → Growth. "
            "Map emotions like peaceful sadness, hopeful melancholy, quiet resilience, acceptance. "
            "Contrast with what this niche is NOT (revenge, hype motivation, desperation love)."
        ),
    },
    "master_character_bible": {
        "title": "Master Character Bible",
        "focus": (
            "Synthesize character archetypes from advanced_visual_analysis.md and emotional subtext "
            "from comments/narratives. Define solitary male/female, dreamer, observer, traveler rules. "
            "Gaze rules (looking away, up, side profile). Expression rules (acceptance, resilience, "
            "peaceful sadness). Relationship presentation (usually alone). Anime aesthetic constraints."
        ),
    },
    "master_narrative_bible": {
        "title": "Master Narrative Bible",
        "focus": (
            "Synthesize narrative_patterns.md, quote_patterns.md, channel_playbook.md, audio transcripts themes. "
            "Quote structure, voice/tone, theme distribution (self-love, healing, growth vs love). "
            "Opening hooks, pacing for Shorts, how narration pairs with visuals."
        ),
    },
    "master_motion_bible": {
        "title": "Master Motion Bible",
        "focus": (
            "Infer motion and pacing patterns from music_profile.md, audio_analysis.md, narrative pacing, "
            "and visual composition. NOTE: No dedicated motion analyzer exists yet — mark motion-specific "
            "claims as [LOW] confidence unless strongly supported. Cover: cut rhythm, camera stillness vs drift, "
            "parallax, Ken Burns, fade timing, music-synced beats."
        ),
    },
    "audience_persona": {
        "title": "Audience Persona",
        "focus": (
            "Synthesize audience_psychology.md and comment_patterns.md into a vivid persona. "
            "Who they are, what pain they carry, why they save/share, what they seek (recovery not romance). "
            "Psychographic profile, vocabulary they use in comments, content they reject."
        ),
    },
    "content_dna": {
        "title": "Content DNA",
        "focus": (
            "The master synthesis — define this channel's emotional PRODUCT in one document. "
            "This is NOT a love channel; it is Recovery Content wrapped in anime aesthetics. "
            "Encode: Pain → Acceptance → Hope journey, visual+emotional+narrative formula, "
            "audience psychology, performance patterns, niche positioning vs competitors. "
            "This document is the single source of truth for what to build next."
        ),
    },
}


def build_bible_prompt(ctx: SynthesisContext, bible_id: str) -> str:
    spec = BIBLE_SPECS[bible_id]
    return (
        f"You are a senior creative strategist reverse-engineering a YouTube Shorts emotional product.\n\n"
        f"TASK: Write the **{spec['title']}** for channel `{ctx.channel_name}`.\n\n"
        f"FOCUS:\n{spec['focus']}\n\n"
        f"{STRUCTURE_RULES}\n\n"
        f"{_base_context(ctx)}"
    )


def build_content_dna_prompt(ctx: SynthesisContext, prior_bibles: dict[str, str]) -> str:
    """Second-pass content DNA using already-synthesized bibles."""
    bible_excerpts = []
    for name, content in prior_bibles.items():
        bible_excerpts.append(f"### {name}\n{content[:4000]}")
    bibles_text = "\n\n---\n\n".join(bible_excerpts)

    return (
        f"You are synthesizing the **Content DNA** — the master formula for `{ctx.channel_name}`.\n\n"
        f"Use the analyzer reports AND the draft bibles below.\n\n"
        f"{STRUCTURE_RULES}\n\n"
        f"ADDITIONAL SECTION (after Executive Summary):\n"
        f"## The Emotional Product\n"
        f"One paragraph defining what the audience is actually buying emotionally.\n\n"
        f"## The Formula\n"
        f"A concise template, e.g.: [Visual] + [Emotion Arc] + [Narration] + [Music] = [Outcome]\n\n"
        f"DRAFT BIBLES:\n{bibles_text}\n\n"
        f"RAW REPORTS:\n{ctx.report_bundle(max_chars_per_report=6000)}\n"
    )

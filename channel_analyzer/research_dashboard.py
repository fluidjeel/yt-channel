#!/usr/bin/env python3
"""
Research Dashboard Generator — 10-minute project overview.

Usage:
  python -m channel_analyzer.research_dashboard
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from channel_analyzer.benchmark.channels import load_benchmark_program
from channel_analyzer.benchmark.config import channel_config
from channel_analyzer.config import Config, PROJECT_ROOT
from channel_analyzer.cross_channel.collector import collect_all_profiles
from channel_analyzer.review_artifact import trim_to_word_limit
from channel_analyzer.utils import setup_logging, write_markdown

logger = logging.getLogger(__name__)


def _list_reports(reports_dir: Path) -> list[str]:
    if not reports_dir.exists():
        return []
    return sorted(p.name for p in reports_dir.glob("*.md"))


def _channel_status_lines() -> str:
    try:
        program = load_benchmark_program()
        profiles = collect_all_profiles(program)
        lines = []
        for p in profiles:
            lines.append(
                f"- **{p.name}** (`{p.slug}`, {p.group}): {p.status}, "
                f"{p.video_count} videos, bibles={'yes' if p.has_bibles else 'no'}"
            )
        return "\n".join(lines) or "_No benchmark channels configured._"
    except Exception as exc:
        return f"_Benchmark status unavailable: {exc}_"


def build_project_state_sections(config: Config) -> dict[str, str]:
    reports = _list_reports(config.reports_dir)
    channel_reports = []
    ch_root = config.reports_dir
    for d in sorted(ch_root.iterdir()):
        if d.is_dir() and (d / "content_dna.md").exists():
            channel_reports.append(d.name)

    capabilities = (
        "**SHIPPED analyzers (local ML, no API required for core steps):**\n"
        "- Channel discovery + performance ranking (steps 1-2)\n"
        "- Download + Whisper transcription (steps 3-4)\n"
        "- Heuristic visual analysis (step 5)\n"
        "- Emotion / narrative / music / quote analysis (steps 6-9)\n"
        "- Channel playbook report (step 10)\n"
        "- Bonus frames + style reference (step 11)\n\n"
        "**SHIPPED extensions:**\n"
        "- Advanced Visual Analyzer (CLIP + composition)\n"
        "- Comment Intelligence (audience psychology)\n"
        "- Bible Synthesizer (master bibles + content_dna)\n"
        "- Benchmark Program + Cross-Channel Synthesizer\n"
        "- Research Dashboard (this document)\n\n"
        "**NOT SHIPPED:** Knowledge graph, channel discovery at scale, motion analyzer v2, "
        "image/video generation, LLM provider plumbing (DeepSeek→Claude compression)."
    )

    completed = (
        "| Analyzer | Status |\n|----------|--------|\n"
        "| Core pipeline 1-11 | Complete on WhisprsYT |\n"
        "| Advanced visual | Complete (20 videos) |\n"
        "| Comment intelligence | Complete (top 20 videos) |\n"
        "| Bible synthesis | Complete (7 bibles) |\n"
        "| Benchmark program | Scaffold + import |\n"
        "| Cross-channel synth | Ready (needs multi-channel data) |\n"
        "| Motion analyzer v2 | Not built |\n"
        "| Style evidence engine | Not built |\n"
        "| Knowledge graph | Not built |"
    )

    major_findings = (
        "**WhisprsYT (single-channel, high confidence):**\n"
        "- Product is **Recovery Content** in anime aesthetic — not love content\n"
        "- Emotional arc: Pain → Understanding → Acceptance → Growth\n"
        "- Comments: 23% self-love, 19% heartbreak, 18% gratitude, 17% loneliness\n"
        "- Visuals: acceptance/resilience, dreamer/solitary, tiny-human/large-world, ~80% negative space\n"
        "- Audience treats videos as emotional reference material (save > share)\n\n"
        "**Cross-channel (low confidence until more full runs):**\n"
        "- Benchmark cohort defined (10 channels) — mostly discovery-only pending full pipeline"
    )

    confidence = (
        "| Finding | Confidence |\n|---------|------------|\n"
        "| Recovery vs love positioning | HIGH (multi-source) |\n"
        "| Pain→Acceptance→Hope arc | HIGH on Whisprs, LOW niche-wide |\n"
        "| Tiny human / large world | HIGH on Whisprs, MEDIUM niche |\n"
        "| Peaceful sadness taxonomy | MEDIUM (CLIP label, needs validation) |\n"
        "| Cross-channel niche DNA | LOW (1 full channel) |"
    )

    open_hyp = (
        "- Is tiny-human/large-world universal or Whisprs-specific?\n"
        "- Do high performers in competitor channels share acceptance expression?\n"
        "- What motion patterns correlate with saves (no motion analyzer yet)?\n"
        "- Are 'peaceful sadness' and 'hopeful melancholy' distinct audience segments?"
    )

    validated = (
        "- Channel is self-worth/healing disguised as love/poetry (quotes + comments)\n"
        "- Visual negative space + solitary archetype on top Whisprs performers\n"
        "- Comment self-love theme is #1 connection point"
    )

    rejected = (
        "- Pure love-channel hypothesis\n"
        "- Revenge/motivation arc as primary product\n"
        "- Desperation-love aesthetic"
    )

    next_work = (
        "1. **Full benchmark** on 3-5 direct competitors (`benchmark_program --full-slugs`)\n"
        "2. **Re-run cross_channel_synthesizer** → paste CHATGPT_REVIEW_CROSS_CHANNEL.md for critique\n"
        "3. **LLM provider plumbing** (DeepSeek compress → Claude synthesize) per TOKEN_ECONOMICS\n"
        "4. Style Evidence Engine (after cross-channel validation)\n"
        "5. Knowledge graph (after taxonomy stabilizes)"
    )

    return {
        "Current Capabilities": capabilities,
        "Completed Analyzers": completed,
        "Channels Analyzed": _channel_status_lines(),
        "Per-Channel Bibles": ", ".join(channel_reports) or "whisprs_yt (root reports only — run --import-reference)",
        "Root Reports Available": ", ".join(reports[:20]) + ("..." if len(reports) > 20 else ""),
        "Major Findings": major_findings,
        "Confidence Levels": confidence,
        "Open Hypotheses": open_hyp,
        "Validated Hypotheses": validated,
        "Rejected Hypotheses": rejected,
        "Next Recommended Work": next_work,
    }


def run_research_dashboard(config: Config | None = None) -> Path:
    config = config or Config.from_yaml()
    config.ensure_dirs()
    sections = build_project_state_sections(config)
    # Flatten and trim
    body = trim_to_word_limit(
        "\n\n".join(f"## {k}\n\n{v}" for k, v in sections.items()),
        2000,
    )
    path = config.reports_dir / "PROJECT_STATE.md"
    write_markdown(path, "Project State", {"Dashboard": body})
    return path


def main(argv: list[str] | None = None) -> int:
    setup_logging()
    parser = argparse.ArgumentParser(description="Research Dashboard Generator")
    parser.add_argument("--config", type=str)
    args = parser.parse_args(argv)
    config = Config.from_yaml(Path(args.config)) if args.config else Config.from_yaml()
    path = run_research_dashboard(config)
    print(f"Wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

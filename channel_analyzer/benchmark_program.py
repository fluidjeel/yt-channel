#!/usr/bin/env python3
"""
Benchmark Channel Program — run pipeline across niche cohort.

Usage:
  python -m channel_analyzer.benchmark_program --import-reference
  python -m channel_analyzer.benchmark_program --discover-all
  python -m channel_analyzer.benchmark_program --full thefallenpoet
  python -m channel_analyzer.benchmark_program --discover-all --full-slugs thefallenpoet,deep_verse
"""

from __future__ import annotations

import argparse
import logging

from channel_analyzer.benchmark.channels import load_benchmark_program
from channel_analyzer.benchmark.runner import (
    import_existing_channel,
    run_channel_discovery,
    run_channel_full_pipeline,
)
from channel_analyzer.config import Config, configure_ffmpeg_env
from channel_analyzer.utils import setup_logging

logger = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> int:
    setup_logging()
    configure_ffmpeg_env()

    parser = argparse.ArgumentParser(description="Benchmark Channel Program")
    parser.add_argument("--config", type=str, help="Path to config.yaml")
    parser.add_argument(
        "--benchmark-config",
        type=str,
        default=None,
        help="Path to benchmark_channels.yaml",
    )
    parser.add_argument(
        "--import-reference",
        action="store_true",
        help="Import existing root analysis into reference channel folder",
    )
    parser.add_argument(
        "--discover-all",
        action="store_true",
        help="Run steps 1-2 (discovery+performance) on all benchmark channels",
    )
    parser.add_argument(
        "--full",
        type=str,
        metavar="SLUG",
        help="Run full pipeline + extensions on one channel slug",
    )
    parser.add_argument(
        "--full-slugs",
        type=str,
        help="Comma-separated slugs for full pipeline",
    )
    args = parser.parse_args(argv)

    from pathlib import Path

    bench_path = Path(args.benchmark_config) if args.benchmark_config else None
    program = load_benchmark_program(bench_path)
    base_config = Config.from_yaml(Path(args.config)) if args.config else Config.from_yaml()

    if args.import_reference:
        ref = program.reference_channel
        import_existing_channel(ref)
        print(f"Imported reference channel: {ref}")
        return 0

    if args.discover_all:
        for ch in program.channels:
            if ch.use_existing:
                logger.info("Skipping discovery for imported channel: %s", ch.slug)
                continue
            logger.info("Discovering %s (%s)...", ch.slug, ch.group)
            try:
                run_channel_discovery(ch, program, base_config)
            except Exception as exc:
                logger.error("Discovery failed for %s: %s", ch.slug, exc)
        print("Discovery pass complete.")
        return 0

    if args.full:
        ch = program.by_slug().get(args.full)
        if not ch:
            parser.error(f"Unknown slug: {args.full}")
        run_channel_full_pipeline(ch, program, base_config)
        print(f"Full pipeline complete: {args.full}")
        return 0

    if args.full_slugs:
        slugs = [s.strip() for s in args.full_slugs.split(",") if s.strip()]
        by_slug = program.by_slug()
        for slug in slugs:
            ch = by_slug.get(slug)
            if not ch:
                logger.error("Unknown slug: %s", slug)
                continue
            logger.info("Full pipeline: %s", slug)
            try:
                run_channel_full_pipeline(ch, program, base_config)
            except Exception as exc:
                logger.error("Full pipeline failed for %s: %s", slug, exc)
        print("Full pipeline batch complete.")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

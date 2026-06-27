#!/usr/bin/env python3
"""Channel Intelligence Analyzer — CLI entry point."""

from __future__ import annotations

import argparse
import sys

from channel_analyzer.config import Config, configure_ffmpeg_env, get_ffmpeg_path
from channel_analyzer.pipeline import STEP_NAMES, Step, run_pipeline
from channel_analyzer.utils import setup_logging


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Channel Intelligence Analyzer — reverse-engineer YouTube channels",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py "https://www.youtube.com/@channelname"
  python main.py "https://www.youtube.com/@channelname" --step 1
  python main.py "https://www.youtube.com/@channelname" --from 4 --to 7
  python main.py "https://www.youtube.com/@channelname" --mvp-profile
  python main.py --check-deps
        """,
    )
    parser.add_argument("channel_url", nargs="?", help="YouTube channel URL")
    parser.add_argument("--config", type=str, help="Path to config.yaml")
    parser.add_argument("--step", type=int, choices=range(1, 12), help="Run a single step (1-11)")
    parser.add_argument("--from", dest="from_step", type=int, default=1, help="Start step (default: 1)")
    parser.add_argument("--to", dest="to_step", type=int, default=11, help="End step (default: 11)")
    parser.add_argument(
        "--mvp-profile",
        action="store_true",
        help="After pipeline: assemble MVP JSON + human channel intelligence report",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")
    parser.add_argument("--check-deps", action="store_true", help="Verify dependencies and exit")

    args = parser.parse_args()
    setup_logging()
    configure_ffmpeg_env()

    if args.check_deps:
        return check_dependencies()

    if not args.channel_url:
        parser.error("channel_url is required unless using --check-deps")

    config_path = None
    if args.config:
        from pathlib import Path

        config_path = Path(args.config)
    config = Config.from_yaml(config_path)

    if args.step:
        start = end = Step(args.step)
    else:
        start = Step(args.from_step)
        end = Step(args.to_step)

    pipeline_config = config
    slug: str | None = None
    if args.mvp_profile:
        from channel_analyzer.benchmark.config import channel_config
        from assembler.slug import resolve_channel_slug

        slug = resolve_channel_slug(args.channel_url)
        pipeline_config = channel_config(slug, config)

    try:
        results = run_pipeline(args.channel_url, pipeline_config, start, end)
        print("\n" + "=" * 60)
        print("ANALYSIS COMPLETE")
        print("=" * 60)
        for name, path in results.items():
            print(f"  {name}: {path}")

        if args.mvp_profile and slug:
            from assembler.assemble import write_mvp_profile
            from assembler.report_renderer import write_channel_report

            mvp_path = write_mvp_profile(slug, channel_url=args.channel_url)
            report_path = write_channel_report(slug)
            print("\n" + "=" * 60)
            print("MVP PROFILE COMPLETE")
            print("=" * 60)
            print(f"  slug: {slug}")
            print(f"  mvp_profile.json: {mvp_path}")
            print(f"  channel_intelligence_report.md: {report_path}")
        return 0
    except KeyboardInterrupt:
        print("\nInterrupted.")
        return 130
    except Exception as exc:
        print(f"\nError: {exc}", file=sys.stderr)
        if args.verbose:
            raise
        return 1


def check_dependencies() -> int:
    """Verify all required dependencies are available."""
    import importlib

    print("Checking dependencies...\n")
    ok = True

    packages = [
        "yt_dlp",
        "whisper",
        "librosa",
        "moviepy",
        "cv2",
        "pandas",
        "numpy",
        "matplotlib",
        "seaborn",
        "sklearn",
        "sentence_transformers",
        "yaml",
        "tqdm",
    ]
    for pkg in packages:
        try:
            importlib.import_module(pkg)
            print(f"  [OK] {pkg}")
        except ImportError:
            print(f"  [MISSING] {pkg}")
            ok = False

    try:
        ffmpeg = get_ffmpeg_path()
        print(f"  [OK] ffmpeg ({ffmpeg})")
    except RuntimeError as exc:
        print(f"  [MISSING] ffmpeg — {exc}")
        ok = False

    print()
    if ok:
        print("All dependencies available.")
        return 0
    print("Some dependencies missing. Run: pip install -r requirements.txt")
    return 1


if __name__ == "__main__":
    sys.exit(main())

"""CLI: assemble MVP profile JSON from existing pipeline artifacts."""

from __future__ import annotations

import argparse
import logging
import sys

from channel_analyzer.utils import setup_logging

from assembler.assemble import write_mvp_profile

LOG = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Assemble MVP profile JSON from pipeline reports (no LLM, no new analyzers).",
    )
    parser.add_argument("slug", help="Channel slug (e.g. whisprs_yt, soulxsigh)")
    parser.add_argument("--url", default=None, help="Original channel URL (optional metadata)")
    parser.add_argument("-o", "--output", default=None, help="Output JSON path")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)

    setup_logging(logging.DEBUG if args.verbose else logging.INFO)

    try:
        from pathlib import Path

        out = write_mvp_profile(
            args.slug,
            channel_url=args.url,
            output_path=Path(args.output) if args.output else None,
        )
        LOG.info("Wrote MVP profile: %s", out)
        print(out)
        return 0
    except FileNotFoundError as exc:
        LOG.error("%s", exc)
        return 1
    except Exception:
        if args.verbose:
            raise
        LOG.exception("Assembly failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())

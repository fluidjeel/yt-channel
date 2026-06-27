#!/usr/bin/env python3
"""Append structured creator feedback to data/feedback/creator_feedback.jsonl."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from channel_analyzer.config import PROJECT_ROOT
from channel_analyzer.utils import load_json

FEEDBACK_DIR = PROJECT_ROOT / "data" / "feedback"
DEFAULT_LOG = FEEDBACK_DIR / "creator_feedback.jsonl"
TEMPLATE_PATH = PROJECT_ROOT / "templates" / "creator_feedback.json"

REQUIRED_FIELDS = (
    "channel_slug",
    "accuracy",
    "usefulness",
    "decision_it_would_help_with",
)


def _prompt(label: str, *, required: bool = True) -> str:
    while True:
        value = input(f"{label}: ").strip()
        if value or not required:
            return value
        print("  (required)")


def _prompt_int(label: str, low: int = 1, high: int = 5) -> int:
    while True:
        raw = _prompt(label)
        try:
            num = int(raw)
            if low <= num <= high:
                return num
        except ValueError:
            pass
        print(f"  Enter an integer from {low} to {high}")


def collect_interactive() -> dict:
    print("Creator feedback (Ctrl+C to cancel)\n")
    payload = {
        "channel_slug": _prompt("Channel slug"),
        "channel_url": _prompt("Channel URL", required=False),
        "report_path": _prompt("Report path", required=False),
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "reviewer_role": _prompt("Reviewer role [creator]", required=False) or "creator",
        "accuracy": _prompt_int("Accuracy (1-5)"),
        "usefulness": _prompt_int("Usefulness (1-5)"),
        "surprises": _prompt("Surprises (optional)", required=False),
        "willingness_to_pay": _prompt(
            "Willingness to pay [no/maybe/yes_under_50/yes_50_200/yes_over_200]",
            required=False,
        ),
        "decision_it_would_help_with": _prompt("Decision it would help with"),
        "most_valuable_section": _prompt("Most valuable section (optional)", required=False),
        "least_valuable_section": _prompt("Least valuable section (optional)", required=False),
        "freeform_notes": _prompt("Freeform notes (optional)", required=False),
    }
    return {k: v for k, v in payload.items() if v != ""}


def validate_payload(data: dict) -> None:
    missing = [f for f in REQUIRED_FIELDS if not data.get(f)]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")
    for field in ("accuracy", "usefulness"):
        val = data[field]
        if not isinstance(val, int) or not 1 <= val <= 5:
            raise ValueError(f"{field} must be an integer 1-5")


def append_feedback(payload: dict, log_path: Path = DEFAULT_LOG) -> Path:
    validate_payload(payload)
    if "submitted_at" not in payload:
        payload["submitted_at"] = datetime.now(timezone.utc).isoformat()

    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return log_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Record creator MVP validation feedback")
    parser.add_argument("--file", type=str, help="JSON file with feedback payload")
    parser.add_argument("--interactive", action="store_true", help="Prompt for fields")
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=str(DEFAULT_LOG),
        help="JSONL output path (default: data/feedback/creator_feedback.jsonl)",
    )
    parser.add_argument("--show-template", action="store_true", help="Print JSON schema path")
    args = parser.parse_args(argv)

    if args.show_template:
        print(TEMPLATE_PATH)
        return 0

    if args.file:
        payload = load_json(Path(args.file))
    elif args.interactive:
        payload = collect_interactive()
    else:
        parser.error("Use --interactive or --file")

    try:
        out = append_feedback(payload, Path(args.output))
        print(f"Recorded feedback → {out}")
        return 0
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

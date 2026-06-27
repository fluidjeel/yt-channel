"""Generate CHATGPT_REVIEW_* artifacts for external critique."""

from __future__ import annotations

from pathlib import Path

from channel_analyzer.utils import write_markdown

MAX_WORDS_DEFAULT = 1500


def _word_count(text: str) -> int:
    return len(text.split())


def trim_to_word_limit(text: str, max_words: int) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[: max_words - 20]) + "\n\n_[Trimmed to word limit]_"


def write_review_artifact(
    reports_dir: Path,
    feature_name: str,
    sections: dict[str, str],
    max_words: int = MAX_WORDS_DEFAULT,
) -> Path:
    """
    Write reports/CHATGPT_REVIEW_<FEATURE>.md optimized for external review.
    No code, no stack traces.
    """
    body = "\n\n".join(f"## {k}\n\n{v.strip()}" for k, v in sections.items())
    body = trim_to_word_limit(body, max_words)
    path = reports_dir / f"CHATGPT_REVIEW_{feature_name.upper()}.md"
    write_markdown(path, f"Review: {feature_name.replace('_', ' ').title()}", {"Report": body})
    return path

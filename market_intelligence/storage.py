"""Persistence, resume checkpoints, and CSV helpers for Market Intelligence."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from market_intelligence.config import MarketConfig

logger = logging.getLogger(__name__)


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    logger.info("Wrote %d rows to %s", len(df), path)


def append_csv_rows(path: Path, rows: list[dict[str, Any]]) -> pd.DataFrame:
    """Append rows to CSV, deduplicating by channel_url."""
    new_df = pd.DataFrame(rows)
    if new_df.empty:
        return read_csv(path)
    existing = read_csv(path)
    if existing.empty:
        write_csv(new_df, path)
        return new_df
    combined = pd.concat([existing, new_df], ignore_index=True)
    if "channel_url" in combined.columns:
        combined = combined.drop_duplicates(subset=["channel_url"], keep="first")
    write_csv(combined, path)
    return combined


def checkpoint_path(config: MarketConfig, step: str) -> Path:
    return config.checkpoint_dir / f"{step}.json"


def load_checkpoint(config: MarketConfig, step: str) -> dict[str, Any] | None:
    path = checkpoint_path(config, step)
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_checkpoint(config: MarketConfig, step: str, data: dict[str, Any]) -> None:
    config.checkpoint_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        **data,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "step": step,
    }
    path = checkpoint_path(config, step)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, default=str)
    logger.debug("Checkpoint saved: %s", path)


def is_step_complete(config: MarketConfig, step: str) -> bool:
    ckpt = load_checkpoint(config, step)
    return ckpt is not None and ckpt.get("status") == "complete"


def mark_step_complete(config: MarketConfig, step: str, extra: dict[str, Any] | None = None) -> None:
    save_checkpoint(config, step, {"status": "complete", **(extra or {})})


def write_markdown(path: Path, title: str, sections: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"# {title}", ""]
    for heading, body in sections.items():
        lines.extend([f"## {heading}", "", body.strip(), ""])
    path.write_text("\n".join(lines), encoding="utf-8")
    logger.info("Wrote report to %s", path)


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    logger.info("Wrote JSON to %s", path)

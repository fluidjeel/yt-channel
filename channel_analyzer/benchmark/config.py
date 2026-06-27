"""Per-channel isolated paths for benchmark runs."""

from __future__ import annotations

from pathlib import Path

from channel_analyzer.config import PROJECT_ROOT, Config


def channel_config(slug: str, base: Config | None = None) -> Config:
    """Return Config scoped to one benchmark channel."""
    cfg = base or Config.from_yaml()
    cfg.data_dir = PROJECT_ROOT / "data" / "channels" / slug
    cfg.reports_dir = PROJECT_ROOT / "reports" / slug
    cfg.artifacts_dir = PROJECT_ROOT / "artifacts" / "channels" / slug
    return cfg


def apply_pipeline_overrides(cfg: Config, overrides: dict) -> Config:
    for key in (
        "top_n_download",
        "top_n_report",
        "max_videos_discover",
        "whisper_model",
    ):
        if key in overrides and overrides[key] is not None:
            setattr(cfg, key, overrides[key])
    return cfg

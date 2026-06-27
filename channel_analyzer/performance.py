"""STEP 2 — Performance Analysis: rank and identify top videos."""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

from channel_analyzer.config import Config
from channel_analyzer.utils import read_csv

logger = logging.getLogger(__name__)


def _normalize_series(series: pd.Series) -> pd.Series:
    if series.max() == series.min():
        return pd.Series(0.5, index=series.index)
    return (series - series.min()) / (series.max() - series.min())


def _engagement_proxy(df: pd.DataFrame) -> pd.Series:
    """Likes/views ratio when likes available; else log-views as proxy."""
    views = df["views"].replace(0, 1)
    if "likes" in df.columns and df["likes"].sum() > 0:
        return df["likes"] / views
    return np.log1p(df["views"]) / np.log1p(views.max())


def _recency_score(df: pd.DataFrame) -> pd.Series:
    """Higher score for recent uploads with strong velocity."""
    days = df.get("days_since_upload", pd.Series(30.0, index=df.index))
    days = days.replace(0, 1)
    velocity = df["views"] / days
    recency_factor = 1 / (1 + np.log1p(days))
    return velocity * recency_factor


def analyze_performance(config: Config, videos_csv: Path | None = None) -> Path:
    """
    Rank videos and write top_videos.csv with top 20 and top 50 flags.

    Returns path to top_videos.csv.
    """
    config.ensure_dirs()
    source = videos_csv or config.videos_csv
    df = read_csv(source)
    if df.empty:
        raise FileNotFoundError(f"No videos data at {source}. Run discovery first.")

    weights = config.ranking_weights
    df = df.copy()
    df["views_per_day"] = df["views"] / df.get("days_since_upload", 30).replace(0, 1)
    df["engagement_proxy"] = _engagement_proxy(df)
    df["recency_adjusted"] = _recency_score(df)

    df["score_views"] = _normalize_series(df["views"].astype(float))
    df["score_vpd"] = _normalize_series(df["views_per_day"].astype(float))
    df["score_engagement"] = _normalize_series(df["engagement_proxy"].astype(float))
    df["score_recency"] = _normalize_series(df["recency_adjusted"].astype(float))

    df["composite_score"] = (
        weights.get("total_views", 0.25) * df["score_views"]
        + weights.get("views_per_day", 0.35) * df["score_vpd"]
        + weights.get("engagement", 0.25) * df["score_engagement"]
        + weights.get("recency", 0.15) * df["score_recency"]
    )

    df = df.sort_values("composite_score", ascending=False).reset_index(drop=True)
    df["rank"] = df.index + 1
    df["top_20"] = df["rank"] <= 20
    df["top_50"] = df["rank"] <= 50

    output_path = config.top_videos_csv
    df.to_csv(output_path, index=False)
    logger.info(
        "Performance analysis complete. Top video: %s (score=%.3f)",
        df.iloc[0]["title"][:50],
        df.iloc[0]["composite_score"],
    )
    return output_path

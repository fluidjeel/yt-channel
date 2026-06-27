"""Configuration for Market Intelligence module."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from channel_analyzer.config import PROJECT_ROOT, DEFAULT_CONFIG_PATH


@dataclass
class MarketConfig:
    data_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "data")
    reports_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "reports")
    knowledge_graph_dir: Path = field(
        default_factory=lambda: PROJECT_ROOT / "knowledge_graph"
    )
    dashboard_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "dashboard")
    checkpoint_dir: Path = field(
        default_factory=lambda: PROJECT_ROOT / "data" / ".checkpoints"
    )

    min_candidate_channels: int = 100
    seed_video_sample: int = 20
    candidate_video_sample: int = 10
    top_similar_for_analysis: int = 10
    embedding_model: str = "all-MiniLM-L6-v2"
    search_results_per_query: int = 25
    max_search_queries: int = 15

    similarity_weights: dict[str, float] = field(
        default_factory=lambda: {
            "titles": 0.25,
            "descriptions": 0.20,
            "transcripts": 0.25,
            "emotional": 0.15,
            "visual": 0.15,
        }
    )
    category_thresholds: dict[str, float] = field(
        default_factory=lambda: {
            "direct_competitor_similarity": 0.72,
            "adjacent_competitor_similarity": 0.50,
            "emerging_max_subscribers": 100_000,
            "outlier_views_per_video": 500_000,
        }
    )
    opportunity_themes: list[str] = field(
        default_factory=lambda: [
            "healing",
            "self-worth",
            "loneliness",
            "purpose",
            "relationships",
            "spirituality",
            "growth",
            "hope",
        ]
    )

    @property
    def discovered_channels_csv(self) -> Path:
        return self.data_dir / "discovered_channels.csv"

    @property
    def channel_similarity_csv(self) -> Path:
        return self.data_dir / "channel_similarity.csv"

    @property
    def channel_categories_csv(self) -> Path:
        return self.data_dir / "channel_categories.csv"

    @property
    def common_patterns_md(self) -> Path:
        return self.reports_dir / "common_patterns.md"

    @property
    def niche_map_md(self) -> Path:
        return self.reports_dir / "niche_map.md"

    @property
    def opportunities_md(self) -> Path:
        return self.reports_dir / "opportunities.md"

    @property
    def knowledge_graph_path(self) -> Path:
        return self.knowledge_graph_dir / "knowledge_graph.graphml"

    @property
    def dashboard_summary_json(self) -> Path:
        return self.dashboard_dir / "summary.json"

    def ensure_dirs(self) -> None:
        for path in (
            self.data_dir,
            self.reports_dir,
            self.knowledge_graph_dir,
            self.dashboard_dir,
            self.checkpoint_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_yaml(cls, path: Path | None = None) -> "MarketConfig":
        config_path = path or DEFAULT_CONFIG_PATH
        data: dict[str, Any] = {}
        if config_path.exists():
            with open(config_path, encoding="utf-8") as f:
                raw = yaml.safe_load(f) or {}
            data = raw.get("market_intelligence", {})

        cfg = cls()
        path_keys = {
            "data_dir": "data_dir",
            "reports_dir": "reports_dir",
            "knowledge_graph_dir": "knowledge_graph_dir",
            "dashboard_dir": "dashboard_dir",
            "checkpoint_dir": "checkpoint_dir",
        }
        for attr, key in path_keys.items():
            if key in data:
                setattr(cfg, attr, PROJECT_ROOT / data[key])

        scalar_keys = (
            "min_candidate_channels",
            "seed_video_sample",
            "candidate_video_sample",
            "top_similar_for_analysis",
            "embedding_model",
            "search_results_per_query",
            "max_search_queries",
        )
        for key in scalar_keys:
            if key in data:
                setattr(cfg, key, data[key])

        if "similarity_weights" in data:
            cfg.similarity_weights = data["similarity_weights"]
        if "category_thresholds" in data:
            cfg.category_thresholds = data["category_thresholds"]
        if "opportunity_themes" in data:
            cfg.opportunity_themes = data["opportunity_themes"]
        return cfg

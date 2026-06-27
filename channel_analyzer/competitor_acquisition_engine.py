"""Competitor Acquisition Engine — discover and score benchmark channels."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import pandas as pd
import yaml

from channel_analyzer.competitor_acquisition.discovery import (
    discover_from_keywords,
    discover_from_seed_videos,
    load_cached_candidates,
    merge_candidates,
    save_cached_candidates,
)
from channel_analyzer.competitor_acquisition.reporter import (
    write_channel_candidates_md,
    write_discovery_review,
    write_top_20_md,
)
from channel_analyzer.competitor_acquisition.scorer import score_all_candidates, score_all_candidates_offline
from channel_analyzer.config import Config
from channel_analyzer.utils import save_json

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def _benchmark_seed_candidates() -> list[dict[str, str]]:
    """Include channels from benchmark_channels.yaml as seeds."""
    path = Config.from_yaml().reports_dir.parent / "benchmark_channels.yaml"
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    out: list[dict[str, str]] = []
    for group in (data.get("channels") or {}).values():
        for ch in group:
            url = ch.get("url", "")
            if url:
                out.append(
                    {
                        "channel_url": url,
                        "channel_name": ch.get("name", ""),
                        "discovery_source": "benchmark_yaml",
                    }
                )
    return out


def run_discovery(
    config: Config | None = None,
    use_cache: bool = True,
    max_score: int = 35,
    offline: bool = False,
) -> list:
    config = config or Config.from_yaml()
    config.ensure_dirs()
    cache_path = config.artifacts_dir / "competitor_discovery" / "candidates.json"
    cache_path.parent.mkdir(parents=True, exist_ok=True)

    if use_cache:
        cached = load_cached_candidates(cache_path)
        if cached:
            logger.info("Using cached %d candidates from %s", len(cached), cache_path)
            candidates = cached
        else:
            candidates = _discover_fresh(config, cache_path)
    else:
        candidates = _discover_fresh(config, cache_path)

    logger.info("Scoring up to %d candidates (offline=%s)...", len(candidates), offline)
    if offline:
        scored = score_all_candidates_offline(candidates, config=config, max_results=max_score)
    else:
        scored = score_all_candidates(candidates, config=config, max_score=max_score)
    logger.info("Scored %d candidates above threshold", len(scored))

    stats = {"raw": len(candidates), "scored": len(scored)}
    _write_outputs(config, scored, stats)
    return scored


def _discover_fresh(config: Config, cache_path: Path) -> list[dict[str, str]]:
    kw = discover_from_keywords()
    seed = discover_from_seed_videos()
    bench = _benchmark_seed_candidates()
    candidates = merge_candidates(kw, seed, bench)
    save_cached_candidates(cache_path, candidates)
    logger.info("Discovered %d unique candidates", len(candidates))
    return candidates


def prioritize_benchmark_channels(scored: list) -> list:
    """Pin benchmark_yaml seeds at top — human-curated cohort first."""
    bench = [c for c in scored if c.discovery_source == "benchmark_yaml"]
    rest = [c for c in scored if c.discovery_source != "benchmark_yaml"]
    bench = sorted(bench, key=lambda x: -x.similarity_score)
    rest = sorted(rest, key=lambda x: -x.similarity_score)
    merged = bench + rest
    seen: set[str] = set()
    out: list = []
    for c in merged:
        key = c.channel_url.rstrip("/").lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(c)
    return out


def _write_outputs(config: Config, scored: list, stats: dict) -> None:
    scored = prioritize_benchmark_channels(scored)
    reports = config.reports_dir
    data_dir = config.data_dir

    write_channel_candidates_md(reports / "channel_candidates.md", scored, stats)
    write_top_20_md(reports / "TOP_20_BENCHMARK_CHANNELS.md", scored)
    write_discovery_review(reports, scored, stats)

    rows = [c.to_row() for c in scored]
    df = pd.DataFrame(rows)
    csv_path = data_dir / "channel_candidates.csv"
    df.to_csv(csv_path, index=False)
    save_json(config.artifacts_dir / "competitor_discovery" / "scored.json", rows)
    logger.info("Wrote reports to %s", reports)


def main() -> None:
    parser = argparse.ArgumentParser(description="Competitor Acquisition Engine")
    parser.add_argument("--no-cache", action="store_true", help="Re-run discovery from scratch")
    parser.add_argument("--max-score", type=int, default=30, help="Max channels to score")
    parser.add_argument("--offline", action="store_true", help="Score from discovery metadata only (no yt-dlp)")
    args = parser.parse_args()
    run_discovery(use_cache=not args.no_cache, max_score=args.max_score, offline=args.offline)


if __name__ == "__main__":
    main()

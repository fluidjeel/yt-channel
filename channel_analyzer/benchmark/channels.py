"""Load and resolve benchmark channel definitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from channel_analyzer.config import PROJECT_ROOT

DEFAULT_BENCHMARK_PATH = PROJECT_ROOT / "benchmark_channels.yaml"


@dataclass
class BenchmarkChannel:
    slug: str
    name: str
    url: str
    group: str
    use_existing: bool = False


@dataclass
class BenchmarkProgram:
    reference_channel: str
    pipeline_overrides: dict[str, Any]
    channels: list[BenchmarkChannel] = field(default_factory=list)

    def by_slug(self) -> dict[str, BenchmarkChannel]:
        return {c.slug: c for c in self.channels}

    def slugs(self) -> list[str]:
        return [c.slug for c in self.channels]


def load_benchmark_program(path: Path | None = None) -> BenchmarkProgram:
    path = path or DEFAULT_BENCHMARK_PATH
    if not path.exists():
        raise FileNotFoundError(f"Benchmark config not found: {path}")

    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    channels: list[BenchmarkChannel] = []

    for group, entries in (data.get("channels") or {}).items():
        for entry in entries:
            channels.append(
                BenchmarkChannel(
                    slug=str(entry["slug"]),
                    name=str(entry.get("name", entry["slug"])),
                    url=str(entry["url"]),
                    group=str(group),
                    use_existing=bool(entry.get("use_existing", False)),
                )
            )

    return BenchmarkProgram(
        reference_channel=str(data.get("reference_channel", "whisprs_yt")),
        pipeline_overrides=dict(data.get("benchmark_pipeline") or {}),
        channels=channels,
    )

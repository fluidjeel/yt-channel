"""Configuration loader for Channel Intelligence Analyzer."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config.yaml"


@dataclass
class Config:
    """Config-driven paths aligned with architecture: data / reports / artifacts."""

    data_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "data")
    reports_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "reports")
    artifacts_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "artifacts")

    ranking_weights: dict[str, float] = field(
        default_factory=lambda: {
            "total_views": 0.25,
            "views_per_day": 0.35,
            "engagement": 0.25,
            "recency": 0.15,
        }
    )
    top_n_download: int = 50
    top_n_report: int = 20
    max_videos_discover: int | None = None
    representative_frames: int = 100
    whisper_model: str = "base"
    frame_interval_seconds: float = 1.0
    scene_change_threshold: float = 30.0
    emotion_dimensions: list[str] = field(
        default_factory=lambda: [
            "hope",
            "loneliness",
            "love",
            "healing",
            "growth",
            "spirituality",
            "self-worth",
            "acceptance",
        ]
    )
    yt_dlp_cookies_file: Path | None = None

    # --- Derived artifact paths (collector outputs) ---
    @property
    def downloads_dir(self) -> Path:
        return self.artifacts_dir / "downloads"

    @property
    def top_frames_dir(self) -> Path:
        return self.artifacts_dir / "top_frames"

    @property
    def style_reference_dir(self) -> Path:
        return self.artifacts_dir / "style_reference"

    @property
    def frames_cache_dir(self) -> Path:
        return self.artifacts_dir / "_frames_cache"

    @property
    def llm_cache_dir(self) -> Path:
        return self.artifacts_dir / "llm_cache"

    # --- Data artifacts (CSV) ---
    @property
    def videos_csv(self) -> Path:
        return self.data_dir / "videos.csv"

    @property
    def top_videos_csv(self) -> Path:
        return self.data_dir / "top_videos.csv"

    @property
    def quote_database_csv(self) -> Path:
        return self.data_dir / "quote_database.csv"

    @property
    def emotion_scores_csv(self) -> Path:
        return self.data_dir / "emotion_scores.csv"

    # --- Report artifacts (Markdown) ---
    @property
    def audio_analysis_md(self) -> Path:
        return self.reports_dir / "audio_analysis.md"

    @property
    def visual_analysis_md(self) -> Path:
        return self.reports_dir / "visual_analysis.md"

    @property
    def emotion_clusters_md(self) -> Path:
        return self.reports_dir / "emotion_clusters.md"

    @property
    def narrative_patterns_md(self) -> Path:
        return self.reports_dir / "narrative_patterns.md"

    @property
    def music_profile_md(self) -> Path:
        return self.reports_dir / "music_profile.md"

    @property
    def quote_patterns_md(self) -> Path:
        return self.reports_dir / "quote_patterns.md"

    @property
    def channel_playbook_md(self) -> Path:
        return self.reports_dir / "channel_playbook.md"

    @property
    def master_prompt_library_md(self) -> Path:
        return self.reports_dir / "master_prompt_library.md"

    def ensure_dirs(self) -> None:
        for path in (
            self.data_dir,
            self.reports_dir,
            self.artifacts_dir,
            self.downloads_dir,
            self.top_frames_dir,
            self.style_reference_dir,
            self.frames_cache_dir,
            self.llm_cache_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)

    def video_dir(self, video_id: str) -> Path:
        return self.downloads_dir / video_id

    @classmethod
    def from_yaml(cls, path: Path | None = None) -> "Config":
        config_path = path or DEFAULT_CONFIG_PATH
        data: dict[str, Any] = {}
        if config_path.exists():
            with open(config_path, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

        cfg = cls()
        for key in ("data_dir", "reports_dir", "artifacts_dir"):
            if key in data:
                setattr(cfg, key, PROJECT_ROOT / data[key])
        # Backward compatibility with legacy config keys
        if "output_dir" in data:
            cfg.data_dir = PROJECT_ROOT / data["output_dir"]
        if "downloads_dir" in data and "artifacts_dir" not in data:
            cfg.artifacts_dir = PROJECT_ROOT / data["downloads_dir"]
            if cfg.artifacts_dir.name == "downloads":
                cfg.artifacts_dir = cfg.artifacts_dir.parent
        if "ranking_weights" in data:
            cfg.ranking_weights = data["ranking_weights"]
        for key in (
            "top_n_download",
            "top_n_report",
            "max_videos_discover",
            "representative_frames",
            "whisper_model",
            "frame_interval_seconds",
            "scene_change_threshold",
            "emotion_dimensions",
            "yt_dlp_cookies_file",
        ):
            if key in data:
                val = data[key]
                if key == "yt_dlp_cookies_file" and val:
                    setattr(cfg, key, PROJECT_ROOT / val)
                else:
                    setattr(cfg, key, val)
        env_cookies = os.environ.get("YTDLP_COOKIES_FILE")
        if env_cookies and Path(env_cookies).exists():
            cfg.yt_dlp_cookies_file = Path(env_cookies)
        elif cfg.yt_dlp_cookies_file and not cfg.yt_dlp_cookies_file.exists():
            cfg.yt_dlp_cookies_file = None
        return cfg


def get_ffmpeg_path() -> str:
    """Resolve ffmpeg binary — system PATH or imageio-ffmpeg bundle."""
    import shutil

    system = shutil.which("ffmpeg")
    if system:
        return system
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        raise RuntimeError(
            "ffmpeg not found. Install ffmpeg system-wide or pip install imageio-ffmpeg."
        )


def configure_ffmpeg_env() -> str:
    """Ensure ffmpeg is on PATH for Whisper (Windows shim for ``ffmpeg.exe`` only)."""
    import shutil
    import sys

    ffmpeg = get_ffmpeg_path()
    ffmpeg_dir = Path(ffmpeg).parent
    resolved = ffmpeg
    if sys.platform == "win32":
        shim = ffmpeg_dir / "ffmpeg.exe"
        if not shim.exists() and Path(ffmpeg).name.lower() != "ffmpeg.exe":
            shutil.copy2(ffmpeg, shim)
        resolved = str(shim if shim.exists() else ffmpeg)
    path = os.environ.get("PATH", "")
    ffmpeg_dir_str = str(ffmpeg_dir)
    if ffmpeg_dir_str not in path.split(os.pathsep):
        os.environ["PATH"] = ffmpeg_dir_str + os.pathsep + path
    return resolved


def get_ffprobe_path() -> str:
    import shutil

    system = shutil.which("ffprobe")
    if system:
        return system
    ffmpeg = get_ffmpeg_path()
    probe = ffmpeg.replace("ffmpeg", "ffprobe")
    if os.path.isfile(probe):
        return probe
    return ffmpeg

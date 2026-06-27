"""Frame collection for advanced visual analysis."""

from __future__ import annotations

import logging
from pathlib import Path

import cv2

from channel_analyzer.config import Config

logger = logging.getLogger(__name__)


def collect_video_frames(
    video_path: Path,
    interval_sec: float = 1.0,
    max_frames: int = 12,
) -> list[tuple]:
    """Extract frames at interval from a video file. Returns (frame_bgr, timestamp)."""
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return []
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    step = max(int(fps * interval_sec), 1)
    frames: list[tuple] = []
    idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if idx % step == 0:
            frames.append((frame.copy(), idx / fps))
        idx += 1
    cap.release()
    if len(frames) > max_frames:
        stride = max(len(frames) // max_frames, 1)
        frames = frames[::stride][:max_frames]
    return frames


def iter_analysis_sources(
    config: Config,
    video_ids: list[str] | None = None,
) -> list[tuple[str, Path, str]]:
    """
    Yield (video_id, path, source_type) for videos and/or cached frames.

    source_type: 'video' | 'image'
    """
    sources: list[tuple[str, Path, str]] = []
    downloads = config.downloads_dir

    if video_ids:
        ids = video_ids
    else:
        ids = [
            d.name
            for d in downloads.iterdir()
            if d.is_dir() and (d / "video.mp4").exists()
        ]

    for vid in sorted(ids):
        video = downloads / vid / "video.mp4"
        if video.exists():
            sources.append((vid, video, "video"))
    return sources


def save_frame_cache(
    cache_dir: Path, video_id: str, frame_idx: int, frame_bgr
) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_dir / f"{video_id}_{frame_idx:04d}.jpg"
    cv2.imwrite(str(path), frame_bgr)
    return path

"""STEP 3 — Download Assets for top-performing videos."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import yt_dlp
from tqdm import tqdm

from channel_analyzer.config import Config
from channel_analyzer.utils import load_json, merge_ytdlp_opts, read_csv, save_json

logger = logging.getLogger(__name__)


def _download_single(video_id: str, url: str, out_dir: Path, config: Config | None = None) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    video_path = out_dir / "video.mp4"
    thumb_path = out_dir / "thumbnail.jpg"
    meta_path = out_dir / "metadata.json"

    if video_path.exists() and meta_path.exists():
        return load_json(meta_path)

    opts = merge_ytdlp_opts(
        {
            "outtmpl": str(out_dir / "video.%(ext)s"),
            "writethumbnail": True,
            "writeinfojson": False,
            "quiet": True,
            "no_warnings": True,
            "format": "best[ext=mp4]/best",
            "merge_output_format": "mp4",
        },
        config,
    )

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)

    # Normalize downloaded files
    for f in out_dir.iterdir():
        if f.suffix in (".mp4", ".webm", ".mkv") and f.name != "video.mp4":
            f.rename(video_path)
            break
    for f in out_dir.iterdir():
        if f.suffix in (".jpg", ".webp", ".png") and "thumb" not in f.name.lower():
            if not thumb_path.exists():
                f.rename(thumb_path)

    metadata = {
        "video_id": video_id,
        "title": info.get("title"),
        "url": url,
        "views": info.get("view_count"),
        "likes": info.get("like_count"),
        "upload_date": info.get("upload_date"),
        "duration": info.get("duration"),
        "description": info.get("description"),
        "tags": info.get("tags"),
        "channel": info.get("channel"),
    }
    save_json(meta_path, metadata)
    return metadata


def download_top_videos(config: Config, top_csv: Path | None = None) -> list[Path]:
    """
    Download video, thumbnail, and metadata for top N videos.

    Returns list of per-video download directories.
    """
    config.ensure_dirs()
    source = top_csv or config.top_videos_csv
    df = read_csv(source)
    if df.empty:
        raise FileNotFoundError(f"No top videos at {source}.")

    top = df[df["top_50"] == True].head(config.top_n_download)  # noqa: E712
    if top.empty:
        top = df.head(config.top_n_download)

    dirs: list[Path] = []
    for _, row in tqdm(top.iterrows(), total=len(top), desc="Downloading videos"):
        video_id = str(row["video_id"])
        url = row["url"]
        out_dir = config.video_dir(video_id)
        try:
            _download_single(video_id, url, out_dir, config)
            dirs.append(out_dir)
        except Exception as exc:
            logger.error("Download failed for %s: %s", video_id, exc)
    logger.info("Downloaded %d / %d videos", len(dirs), len(top))
    return dirs

"""STEP 3 — Download Assets for top-performing videos."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

import pandas as pd
import yt_dlp
from tqdm import tqdm

from channel_analyzer.config import Config
from channel_analyzer.utils import load_json, merge_ytdlp_opts, read_csv, save_json, YTDLP_DOWNLOAD_FORMAT

logger = logging.getLogger(__name__)


def _duration_ok(row, config: Config) -> bool:
    cap = config.max_video_duration_seconds
    if cap is None:
        return True
    dur = row.get("duration_seconds")
    if dur is None or (isinstance(dur, float) and dur != dur):
        return True
    try:
        return float(dur) <= float(cap)
    except (TypeError, ValueError):
        return True


def _size_ok(video_path: Path, config: Config) -> bool:
    cap_mb = config.max_download_mb
    if cap_mb is None or not video_path.exists():
        return True
    size_mb = video_path.stat().st_size / (1024 * 1024)
    return size_mb <= float(cap_mb)


def _download_single(video_id: str, url: str, out_dir: Path, config: Config | None = None) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    video_path = out_dir / "video.mp4"
    thumb_path = out_dir / "thumbnail.jpg"
    meta_path = out_dir / "metadata.json"

    if video_path.exists() and meta_path.exists():
        meta = load_json(meta_path)
        if config and not _size_ok(video_path, config):
            logger.warning(
                "Removing %s — %.1f MB exceeds max_download_mb=%s",
                video_id,
                video_path.stat().st_size / (1024 * 1024),
                config.max_download_mb,
            )
            shutil.rmtree(out_dir)
        else:
            return meta

    opts = merge_ytdlp_opts(
        {
            "outtmpl": str(out_dir / "video.%(ext)s"),
            "writethumbnail": True,
            "writeinfojson": False,
            "quiet": True,
            "no_warnings": True,
            "format": YTDLP_DOWNLOAD_FORMAT,
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

    if config and not _size_ok(video_path, config):
        size_mb = video_path.stat().st_size / (1024 * 1024)
        shutil.rmtree(out_dir)
        raise ValueError(
            f"Downloaded {video_id} is {size_mb:.1f} MB; max_download_mb={config.max_download_mb}"
        )

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

    Skips videos over max_video_duration_seconds; tries further ranked rows.
    Removes downloads over max_download_mb.

    Returns list of per-video download directories.
    """
    config.ensure_dirs()
    source = top_csv or config.top_videos_csv
    df = read_csv(source)
    if df.empty:
        raise FileNotFoundError(f"No top videos at {source}.")

    ranked = df[df["top_50"] == True].copy()  # noqa: E712
    if ranked.empty:
        ranked = df.copy()
    if "rank" in ranked.columns:
        ranked = ranked.sort_values("rank")
    elif "composite_score" in ranked.columns:
        ranked = ranked.sort_values("composite_score", ascending=False)

    target = config.top_n_download
    candidates = ranked
    if len(candidates) < target and "composite_score" in df.columns:
        extra = df.sort_values("composite_score", ascending=False)
        candidates = pd.concat([ranked, extra]).drop_duplicates(subset=["video_id"])

    dirs: list[Path] = []
    skipped_duration = 0
    for _, row in candidates.iterrows():
        if len(dirs) >= target:
            break
        if not _duration_ok(row, config):
            skipped_duration += 1
            logger.info(
                "Skip %s — duration %ss > cap %ss",
                row.get("video_id"),
                row.get("duration_seconds"),
                config.max_video_duration_seconds,
            )
            continue
        video_id = str(row["video_id"])
        url = row["url"]
        out_dir = config.video_dir(video_id)
        try:
            _download_single(video_id, url, out_dir, config)
            dirs.append(out_dir)
        except Exception as exc:
            logger.error("Download failed for %s: %s", video_id, exc)
    if skipped_duration:
        logger.info("Skipped %d candidates over duration cap", skipped_duration)
    logger.info("Downloaded %d / %d videos", len(dirs), target)
    return dirs

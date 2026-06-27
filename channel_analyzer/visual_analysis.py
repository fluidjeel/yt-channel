"""STEP 5 — Visual Analysis: frame extraction, color, scene classification."""

from __future__ import annotations

import logging
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from tqdm import tqdm

from channel_analyzer.config import Config
from channel_analyzer.utils import write_markdown

logger = logging.getLogger(__name__)

SCENE_LABELS = [
    "portrait",
    "landscape",
    "sky",
    "window",
    "ocean",
    "field",
    "forest",
    "rooftop",
]


def _dominant_colors(frame: np.ndarray, k: int = 5) -> list[tuple[int, int, int]]:
    pixels = frame.reshape(-1, 3).astype(np.float32)
    if len(pixels) < k:
        return []
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
    _, labels, centers = cv2.kmeans(
        pixels, k, None, criteria, 3, cv2.KMEANS_PP_CENTERS
    )
    counts = Counter(labels.flatten())
    sorted_centers = sorted(
        range(k), key=lambda i: counts.get(i, 0), reverse=True
    )
    return [tuple(int(c) for c in centers[i]) for i in sorted_centers]


def _frame_metrics(frame: np.ndarray) -> dict[str, float]:
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    brightness = float(np.mean(gray)) / 255.0
    contrast = float(np.std(gray)) / 128.0
    saturation = float(np.mean(hsv[:, :, 1])) / 255.0
    return {
        "brightness": round(brightness, 3),
        "contrast": round(min(contrast, 1.0), 3),
        "saturation": round(saturation, 3),
    }


def _classify_scene(frame: np.ndarray) -> list[str]:
    """Heuristic scene classification using color and edge features."""
    h, w = frame.shape[:2]
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    labels: list[str] = []

    aspect = w / max(h, 1)
    if aspect > 1.3:
        labels.append("landscape")
    elif aspect < 0.85:
        labels.append("portrait")

    # Sky: upper region bright blue/cyan
    top = hsv[: h // 3, :]
    blue_mask = cv2.inRange(top, (90, 30, 100), (130, 255, 255))
    if np.mean(blue_mask) > 40:
        labels.append("sky")

    # Ocean: lower blue-green horizontal band
    bottom = hsv[2 * h // 3 :, :]
    teal_mask = cv2.inRange(bottom, (80, 40, 40), (110, 255, 200))
    if np.mean(teal_mask) > 35:
        labels.append("ocean")

    # Forest: dominant green
    green_mask = cv2.inRange(hsv, (35, 40, 40), (85, 255, 200))
    if np.mean(green_mask) > 50:
        labels.append("forest")

    # Field: yellow-green mid saturation
    field_mask = cv2.inRange(hsv, (25, 30, 80), (45, 180, 255))
    if np.mean(field_mask) > 45 and "forest" not in labels:
        labels.append("field")

    # Window: rectangular bright regions with strong edges
    edges = cv2.Canny(gray, 50, 150)
    bright = gray > 200
    if np.mean(edges) > 15 and np.mean(bright) > 30:
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            approx = cv2.approxPolyDP(cnt, 0.02 * cv2.arcLength(cnt, True), True)
            if len(approx) == 4 and cv2.contourArea(cnt) > (w * h * 0.02):
                labels.append("window")
                break

    # Rooftop: horizon line + urban gray/brown lower third
    lower = hsv[2 * h // 3 :, :]
    urban = cv2.inRange(lower, (0, 0, 40), (30, 80, 180))
    if np.mean(urban) > 40 and "sky" in labels:
        labels.append("rooftop")

    # Face/portrait detection
    try:
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        faces = face_cascade.detectMultiScale(gray, 1.1, 4, minSize=(30, 30))
        if len(faces) > 0:
            labels.append("portrait")
    except Exception:
        pass

    return list(dict.fromkeys(labels)) or ["landscape"]


def _scene_change_score(prev: np.ndarray | None, curr: np.ndarray) -> float:
    if prev is None:
        return 0.0
    prev_small = cv2.resize(prev, (64, 64))
    curr_small = cv2.resize(curr, (64, 64))
    diff = cv2.absdiff(prev_small, curr_small)
    return float(np.mean(diff))


def _extract_frames(
    video_path: Path,
    interval: float,
    scene_threshold: float,
) -> list[tuple[np.ndarray, float, bool]]:
    """Return list of (frame, timestamp, is_scene_change)."""
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return []

    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    frame_interval = max(int(fps * interval), 1)
    frames: list[tuple[np.ndarray, float, bool]] = []
    prev_frame: np.ndarray | None = None
    idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        timestamp = idx / fps
        is_interval = idx % frame_interval == 0
        score = _scene_change_score(prev_frame, frame)
        is_scene = score > scene_threshold and prev_frame is not None

        if is_interval or is_scene:
            frames.append((frame.copy(), timestamp, is_scene))
        prev_frame = frame
        idx += 1

    cap.release()
    return frames


def _analyze_video_visuals(
    video_path: Path,
    interval: float,
    scene_threshold: float,
) -> dict[str, Any]:
    frames_data = _extract_frames(video_path, interval, scene_threshold)
    if not frames_data:
        return {}

    all_colors: list[tuple[int, int, int]] = []
    metrics_list: list[dict[str, float]] = []
    scene_counts: Counter[str] = Counter()
    char_freq = 0

    for frame, _ts, _sc in frames_data:
        colors = _dominant_colors(frame, k=3)
        all_colors.extend(colors)
        metrics_list.append(_frame_metrics(frame))
        for label in _classify_scene(frame):
            scene_counts[label] += 1
        try:
            face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            )
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            if len(face_cascade.detectMultiScale(gray, 1.1, 4)) > 0:
                char_freq += 1
        except Exception:
            pass

    color_counter = Counter(all_colors)
    top_palette = color_counter.most_common(8)
    avg_metrics = {
        k: round(float(np.mean([m[k] for m in metrics_list])), 3)
        for k in metrics_list[0]
    }

    return {
        "frame_count": len(frames_data),
        "dominant_colors": [c for c, _ in top_palette],
        "palette_hex": [
            f"#{r:02x}{g:02x}{b:02x}" for b, g, r in [c for c, _ in top_palette]
        ],
        "avg_brightness": avg_metrics["brightness"],
        "avg_contrast": avg_metrics["contrast"],
        "avg_saturation": avg_metrics["saturation"],
        "scene_frequency": dict(scene_counts),
        "character_frame_ratio": round(char_freq / len(frames_data), 3),
        "environment_frequency": {
            k: scene_counts.get(k, 0) for k in SCENE_LABELS if k != "portrait"
        },
        "sample_frames": [f for f, _, _ in frames_data[:: max(1, len(frames_data) // 5)]],
    }


def analyze_visuals(config: Config, video_dirs: list[Path] | None = None) -> Path:
    """Run visual analysis and write visual_analysis.md."""
    config.ensure_dirs()
    if video_dirs is None:
        video_dirs = [
            d for d in config.downloads_dir.iterdir() if d.is_dir() and (d / "video.mp4").exists()
        ]

    all_results: list[dict[str, Any]] = []
    frame_bank: list[tuple[np.ndarray, str, float]] = []

    for vdir in tqdm(video_dirs, desc="Visual analysis"):
        video_path = vdir / "video.mp4"
        if not video_path.exists():
            continue
        try:
            result = _analyze_video_visuals(
                video_path,
                config.frame_interval_seconds,
                config.scene_change_threshold,
            )
            if not result:
                continue
            result["video_id"] = vdir.name
            all_results.append(result)
            for i, frame in enumerate(result.pop("sample_frames", [])):
                frame_bank.append((frame, vdir.name, float(i)))
        except Exception as exc:
            logger.error("Visual analysis failed for %s: %s", vdir.name, exc)

    if not all_results:
        body = "No visual analyses completed."
    else:
        agg_scenes: Counter[str] = Counter()
        all_hex: Counter[str] = Counter()
        for r in all_results:
            for scene, cnt in r.get("scene_frequency", {}).items():
                agg_scenes[scene] += cnt
            for h in r.get("palette_hex", []):
                all_hex[h] += 1

        avg_b = np.mean([r["avg_brightness"] for r in all_results])
        avg_c = np.mean([r["avg_contrast"] for r in all_results])
        avg_s = np.mean([r["avg_saturation"] for r in all_results])
        char_ratio = np.mean([r["character_frame_ratio"] for r in all_results])

        per_video = "\n".join(
            f"### {r['video_id']}\n"
            f"- Frames analyzed: {r['frame_count']}\n"
            f"- Palette: {', '.join(r.get('palette_hex', [])[:5])}\n"
            f"- Brightness/Contrast/Saturation: {r['avg_brightness']}/{r['avg_contrast']}/{r['avg_saturation']}\n"
            f"- Character presence: {r['character_frame_ratio']*100:.0f}%\n"
            f"- Scenes: {r.get('scene_frequency', {})}\n"
            for r in all_results
        )

        body = (
            f"**Videos analyzed:** {len(all_results)}\n\n"
            f"### Channel Visual Signature\n"
            f"- Average brightness: **{avg_b:.2f}**\n"
            f"- Average contrast: **{avg_c:.2f}**\n"
            f"- Average saturation: **{avg_s:.2f}**\n"
            f"- Character frame ratio: **{char_ratio*100:.1f}%**\n\n"
            f"### Dominant Color Palette\n"
            + "\n".join(f"- `{h}` ({c} frames)" for h, c in all_hex.most_common(10))
            + "\n\n### Environment Frequency\n"
            + "\n".join(f"- **{k}**: {v}" for k, v in agg_scenes.most_common())
            + f"\n\n## Per-Video Breakdown\n\n{per_video}"
        )

    output = config.visual_analysis_md
    write_markdown(output, "Visual Analysis Report", {"Summary": body})
    logger.info("Wrote visual analysis to %s", output)

    # Stash frame bank for bonus step
    stash = config.artifacts_dir / "_frame_bank.npz"
    if frame_bank:
        np.savez_compressed(
            stash,
            count=len(frame_bank),
            video_ids=[fb[1] for fb in frame_bank],
        )
        frames_dir = config.frames_cache_dir
        frames_dir.mkdir(exist_ok=True)
        for i, (frame, vid, _) in enumerate(frame_bank[:200]):
            cv2.imwrite(str(frames_dir / f"{i:04d}_{vid}.jpg"), frame)

    return output

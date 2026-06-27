"""BONUS — Top frames, style reference assets, master prompt library."""

from __future__ import annotations

import json
import logging
import shutil
from collections import Counter
from pathlib import Path

import cv2
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.cluster import KMeans

from channel_analyzer.config import Config
from channel_analyzer.utils import read_csv, write_markdown

logger = logging.getLogger(__name__)


def _collect_all_frames(config: Config) -> list[tuple[np.ndarray, str, float]]:
    """Collect frames from cached analysis and fresh extraction."""
    frames: list[tuple[np.ndarray, str, float]] = []
    cache = config.frames_cache_dir
    if cache.exists():
        for f in sorted(cache.iterdir()):
            if f.suffix.lower() in (".jpg", ".png"):
                img = cv2.imread(str(f))
                if img is not None:
                    parts = f.stem.split("_", 1)
                    vid = parts[1] if len(parts) > 1 else "unknown"
                    frames.append((img, vid, 0.5))

    if len(frames) < config.representative_frames:
        for vdir in config.downloads_dir.iterdir():
            if not vdir.is_dir():
                continue
            video = vdir / "video.mp4"
            if not video.exists():
                continue
            cap = cv2.VideoCapture(str(video))
            fps = cap.get(cv2.CAP_PROP_FPS) or 30
            total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
            step = max(total // 10, 1)
            for i in range(0, total, step):
                cap.set(cv2.CAP_PROP_POS_FRAMES, i)
                ret, frame = cap.read()
                if ret:
                    frames.append((frame, vdir.name, i / fps))
            cap.release()
    return frames


def _frame_feature_vector(frame: np.ndarray) -> np.ndarray:
    small = cv2.resize(frame, (32, 32))
    hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
    hist_h = cv2.calcHist([hsv], [0], None, [16], [0, 180]).flatten()
    hist_s = cv2.calcHist([hsv], [1], None, [8], [0, 256]).flatten()
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    return np.concatenate([hist_h, hist_s, [np.mean(gray), np.std(gray)]])


def export_top_frames(config: Config) -> Path:
    """Select and export the most visually representative frames."""
    config.top_frames_dir.mkdir(parents=True, exist_ok=True)
    for old in config.top_frames_dir.glob("*.jpg"):
        old.unlink()

    frames = _collect_all_frames(config)
    if not frames:
        logger.warning("No frames available for top_frames export")
        return config.top_frames_dir

    features = np.array([_frame_feature_vector(f) for f, _, _ in frames])
    n = min(config.representative_frames, len(frames))

    if len(frames) > n:
        kmeans = KMeans(n_clusters=n, random_state=42, n_init=10)
        kmeans.fit(features)
        # Pick frame closest to each cluster center
        selected_idx: list[int] = []
        for i in range(n):
            mask = kmeans.labels_ == i
            cluster_indices = np.where(mask)[0]
            if len(cluster_indices) == 0:
                continue
            dists = np.linalg.norm(features[cluster_indices] - kmeans.cluster_centers_[i], axis=1)
            selected_idx.append(int(cluster_indices[np.argmin(dists)]))
        selected_idx = list(dict.fromkeys(selected_idx))[:n]
    else:
        selected_idx = list(range(len(frames)))

    for rank, idx in enumerate(selected_idx):
        frame, vid, ts = frames[idx]
        out = config.top_frames_dir / f"{rank+1:03d}_{vid}_t{ts:.1f}s.jpg"
        cv2.imwrite(str(out), frame)

    logger.info("Exported %d representative frames to %s", len(selected_idx), config.top_frames_dir)
    return config.top_frames_dir


def export_style_reference(config: Config) -> Path:
    """Generate color palettes, mood boards, character and environment references."""
    ref = config.style_reference_dir
    for sub in ("color_palettes", "mood_boards", "character_archetypes", "environments"):
        (ref / sub).mkdir(parents=True, exist_ok=True)

    frames = _collect_all_frames(config)
    if not frames:
        return ref

    # Color palettes
    all_colors: list[tuple[int, int, int]] = []
    for frame, _, _ in frames[:100]:
        pixels = cv2.resize(frame, (64, 64)).reshape(-1, 3).astype(np.float32)
        _, _, centers = cv2.kmeans(
            pixels, 3, None,
            (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0),
            3, cv2.KMEANS_PP_CENTERS,
        )
        for c in centers:
            b, g, r = int(c[0]), int(c[1]), int(c[2])
            all_colors.append((r, g, b))

    color_counts = Counter(all_colors)
    top_colors = [c for c, _ in color_counts.most_common(12)]

    palette_path = ref / "color_palettes" / "dominant_palette.json"
    palette_path.write_text(
        json.dumps(
            {"colors_rgb": top_colors, "colors_hex": [f"#{r:02x}{g:02x}{b:02x}" for r, g, b in top_colors]},
            indent=2,
        ),
        encoding="utf-8",
    )

    fig, ax = plt.subplots(figsize=(12, 2))
    for i, (r, g, b) in enumerate(top_colors):
        ax.add_patch(plt.Rectangle((i, 0), 1, 1, color=(r / 255, g / 255, b / 255)))
    ax.set_xlim(0, len(top_colors))
    ax.set_ylim(0, 1)
    ax.axis("off")
    fig.savefig(ref / "color_palettes" / "palette_strip.png", bbox_inches="tight", dpi=150)
    plt.close()

    # Mood board — grid of representative frames
    mood_frames = frames[:: max(1, len(frames) // 16)][:16]
    if mood_frames:
        cols = 4
        rows = (len(mood_frames) + cols - 1) // cols
        fig, axes = plt.subplots(rows, cols, figsize=(12, 3 * rows))
        axes_flat = np.atleast_1d(axes).flatten()
        for i, (frame, vid, ts) in enumerate(mood_frames):
            axes_flat[i].imshow(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            axes_flat[i].set_title(f"{vid[:8]}…", fontsize=8)
            axes_flat[i].axis("off")
        for j in range(len(mood_frames), len(axes_flat)):
            axes_flat[j].axis("off")
        fig.suptitle("Channel Mood Board", fontsize=14)
        fig.savefig(ref / "mood_boards" / "mood_board.png", bbox_inches="tight", dpi=120)
        plt.close()

    # Character archetypes — frames with faces
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    char_count = 0
    for frame, vid, ts in frames:
        if char_count >= 10:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4, minSize=(40, 40))
        if len(faces) > 0:
            cv2.imwrite(
                str(ref / "character_archetypes" / f"character_{char_count+1}_{vid}.jpg"),
                frame,
            )
            char_count += 1

    # Environments — classify and save examples
    from channel_analyzer.visual_analysis import _classify_scene

    env_counts: dict[str, int] = Counter()
    for frame, vid, ts in frames:
        for label in _classify_scene(frame):
            if label != "portrait" and env_counts[label] < 3:
                cv2.imwrite(
                    str(ref / "environments" / f"{label}_{env_counts[label]+1}.jpg"),
                    frame,
                )
                env_counts[label] += 1

    logger.info("Style reference assets written to %s", ref)
    return ref


def generate_master_prompts(config: Config) -> Path:
    """Create master_prompt_library.md with reproduction prompts."""
    output = config.master_prompt_library_md

    visual_md = config.visual_analysis_md
    audio_md = config.audio_analysis_md
    music_md = config.music_profile_md
    narrative_md = config.narrative_patterns_md
    emotion_md = config.emotion_clusters_md

    palette_file = config.style_reference_dir / "color_palettes" / "dominant_palette.json"
    palette_hex = []
    if palette_file.exists():
        palette_hex = json.loads(palette_file.read_text())["colors_hex"]

    top_df = read_csv(config.top_videos_csv)
    channel_name = ""
    if not top_df.empty and "channel" in top_df.columns:
        channel_name = str(top_df.iloc[0].get("channel", ""))

    sections = {
        "Visual Style Prompt": (
            f"Create a YouTube Short in the visual style of {channel_name or 'this channel'}.\n\n"
            f"**Color palette:** {', '.join(palette_hex[:6]) or 'warm muted tones'}\n"
            f"**Composition:** Vertical 9:16, cinematic depth of field\n"
            f"**Lighting:** Match channel brightness/contrast from analysis\n"
            f"**Environments:** Use dominant settings from visual analysis\n\n"
            f"```\n{_read_snippet(visual_md, 800)}\n```"
        ),
        "Narration Style Prompt": (
            "Write a voiceover script matching this channel's speech patterns.\n\n"
            "- Match the average words-per-minute and sentence length\n"
            "- Use the dominant hook style identified in analysis\n"
            "- Include emotional keywords at channel-average density\n"
            "- End with a quotable resolution line\n\n"
            f"```\n{_read_snippet(audio_md, 800)}\n```"
        ),
        "Emotional Tone Prompt": (
            "Set the emotional tone for this content piece.\n\n"
            "Target the channel's dominant emotion cluster while exploring "
            "underused emotional territories for freshness.\n\n"
            f"```\n{_read_snippet(emotion_md, 600)}\n```"
        ),
        "Story Structure Prompt": (
            "Structure the narrative using this channel's proven template:\n\n"
            "1. **Hook** (first 3 seconds) — pattern interrupt or personal stake\n"
            "2. **Reflection** — vulnerable personal narrative\n"
            "3. **Insight** — the transformative realization\n"
            "4. **Resolution** — emotional payoff and implicit CTA\n\n"
            f"```\n{_read_snippet(narrative_md, 600)}\n```"
        ),
        "Audio / Music Prompt": (
            "Select or generate background audio matching this signature:\n\n"
            f"```\n{_read_snippet(music_md, 600)}\n```"
        ),
        "Full Production Prompt": (
            f"Produce a complete YouTube Short replicating the style of {channel_name or 'the analyzed channel'}.\n\n"
            "**Visual:** Apply the dominant color palette, environment, and framing from the visual style bible.\n"
            "**Script:** Follow the Hook → Reflection → Insight → Resolution structure.\n"
            "**Voice:** Calm, intimate delivery at the channel's WPM. Strategic pauses.\n"
            "**Music:** Ambient bed matching tempo and key signature.\n"
            "**Duration:** Stay within the observed viral duration sweet spot.\n"
            "**Emotion:** Lead with the dominant cluster emotion, close with hope/acceptance."
        ),
    }

    write_markdown(output, "Master Prompt Library", sections)
    logger.info("Wrote master prompt library to %s", output)
    return output


def _read_snippet(path: Path, max_len: int) -> str:
    if not path.exists():
        return "(analysis not available)"
    return path.read_text(encoding="utf-8")[:max_len]


def run_bonus_features(config: Config) -> dict[str, Path]:
    """Run all bonus feature exports."""
    return {
        "top_frames": export_top_frames(config),
        "style_reference": export_style_reference(config),
        "master_prompts": generate_master_prompts(config),
    }

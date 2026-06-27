"""STEP 8 — Audio Signature Analysis: tempo, key, loudness, silence."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import librosa
import numpy as np
from tqdm import tqdm

from channel_analyzer.config import Config, get_ffmpeg_path
from channel_analyzer.utils import write_markdown

logger = logging.getLogger(__name__)

KEY_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def _estimate_key(chroma: np.ndarray) -> str:
    chroma_mean = np.mean(chroma, axis=1)
    return KEY_NAMES[int(np.argmax(chroma_mean))]


def _silence_stats(y: np.ndarray, sr: int, threshold_db: float = -40) -> dict[str, float]:
    intervals = librosa.effects.split(y, top_db=abs(threshold_db))
    if len(intervals) == 0:
        return {"silence_ratio": 1.0, "pause_count": 0, "avg_pause_duration": 0.0}

    total_samples = len(y)
    voiced_samples = sum(end - start for start, end in intervals)
    silence_samples = total_samples - voiced_samples

    pauses = []
    prev_end = 0
    for start, end in intervals:
        gap = start - prev_end
        if gap > sr * 0.15:
            pauses.append(gap / sr)
        prev_end = end

    return {
        "silence_ratio": round(silence_samples / max(total_samples, 1), 3),
        "pause_count": len(pauses),
        "avg_pause_duration": round(float(np.mean(pauses)) if pauses else 0.0, 2),
    }


def _analyze_audio_file(audio_path: Path) -> dict[str, Any]:
    y, sr = librosa.load(str(audio_path), sr=22050, mono=True)
    duration = librosa.get_duration(y=y, sr=sr)

    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    tempo_val = float(tempo) if np.isscalar(tempo) else float(tempo[0])

    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
    key = _estimate_key(chroma)

    rms = librosa.feature.rms(y=y)[0]
    loudness_db = float(librosa.amplitude_to_db(np.mean(rms), ref=np.max))

    silence = _silence_stats(y, sr)

    return {
        "duration_seconds": round(duration, 1),
        "tempo_bpm": round(tempo_val, 1),
        "estimated_key": key,
        "loudness_db": round(loudness_db, 1),
        **silence,
    }


def analyze_music(config: Config) -> Path:
    """Analyze background music and audio signature for each video."""
    config.ensure_dirs()
    results: list[dict[str, Any]] = []

    video_dirs = [
        d for d in config.downloads_dir.iterdir() if d.is_dir() and (d / "audio.mp3").exists()
    ]

    for vdir in tqdm(video_dirs, desc="Music analysis"):
        audio_path = vdir / "audio.mp3"
        try:
            analysis = _analyze_audio_file(audio_path)
            analysis["video_id"] = vdir.name
            results.append(analysis)
        except Exception as exc:
            logger.error("Music analysis failed for %s: %s", vdir.name, exc)

    if not results:
        body = "No audio files available for music analysis."
    else:
        avg_tempo = np.mean([r["tempo_bpm"] for r in results])
        keys = [r["estimated_key"] for r in results]
        dominant_key = max(set(keys), key=keys.count)
        avg_loud = np.mean([r["loudness_db"] for r in results])
        avg_silence = np.mean([r["silence_ratio"] for r in results])
        avg_pauses = np.mean([r["pause_count"] for r in results])

        per_video = "\n".join(
            f"### {r['video_id']}\n"
            f"- Tempo: {r['tempo_bpm']} BPM | Key: {r['estimated_key']}\n"
            f"- Loudness: {r['loudness_db']} dB\n"
            f"- Silence: {r['silence_ratio']*100:.0f}% | Pauses: {r['pause_count']} "
            f"(avg {r['avg_pause_duration']}s)\n"
            for r in results
        )

        tempo_class = (
            "slow/ambient" if avg_tempo < 90 else "mid-tempo" if avg_tempo < 120 else "upbeat"
        )

        body = (
            f"**Videos analyzed:** {len(results)}\n\n"
            f"### Channel Audio Signature\n"
            f"- Average tempo: **{avg_tempo:.0f} BPM** ({tempo_class})\n"
            f"- Dominant key: **{dominant_key}**\n"
            f"- Average loudness: **{avg_loud:.1f} dB**\n"
            f"- Silence ratio: **{avg_silence*100:.0f}%**\n"
            f"- Average pause count: **{avg_pauses:.1f}** per video\n\n"
            f"### Production Notes\n"
            f"- Use **{tempo_class}** background music around **{avg_tempo:.0f} BPM**\n"
            f"- Key of **{dominant_key}** appears most frequently\n"
            f"- Leave **{avg_silence*100:.0f}%** breathing room — pauses are intentional\n\n"
            f"## Per-Video Breakdown\n\n{per_video}"
        )

    output = config.music_profile_md
    write_markdown(output, "Music & Audio Signature Profile", {"Summary": body})
    logger.info("Wrote music profile to %s", output)
    return output

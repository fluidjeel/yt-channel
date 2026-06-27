"""STEP 4 — Audio Analysis: extract audio, transcribe, analyze speech patterns."""

from __future__ import annotations

import logging
import re
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

from tqdm import tqdm

from channel_analyzer.config import Config, configure_ffmpeg_env, get_ffmpeg_path
from channel_analyzer.utils import (
    extract_ngrams,
    tokenize_sentences,
    word_count,
    write_markdown,
)

logger = logging.getLogger(__name__)

HOOK_PATTERNS = [
    r"^(what if|imagine|have you ever|did you know|here'?s the thing)",
    r"^(stop|wait|listen|look)",
    r"^(i used to|when i|one day|the day)",
    r"^(nobody|no one|everyone|we all)",
    r"^(this is|here is|let me)",
]

EMOTION_KEYWORDS = {
    "hope": ["hope", "dream", "future", "believe", "possible", "light", "tomorrow"],
    "loneliness": ["alone", "lonely", "isolated", "empty", "silence", "nobody"],
    "love": ["love", "heart", "care", "together", "cherish", "devotion"],
    "healing": ["heal", "recover", "mend", "peace", "calm", "restore"],
    "growth": ["grow", "learn", "become", "evolve", "progress", "journey"],
    "spirituality": ["soul", "spirit", "faith", "divine", "universe", "prayer"],
    "self-worth": ["worth", "enough", "value", "deserve", "worthy", "confidence"],
    "acceptance": ["accept", "okay", "fine", "let go", "release", "forgive"],
}


def _extract_audio(video_path: Path, audio_path: Path) -> None:
    if audio_path.exists():
        return
    ffmpeg = get_ffmpeg_path()
    cmd = [
        ffmpeg,
        "-y",
        "-i",
        str(video_path),
        "-vn",
        "-acodec",
        "libmp3lame",
        "-q:a",
        "4",
        str(audio_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def _transcribe(audio_path: Path, model_name: str) -> str:
    transcript_path = audio_path.parent / "transcript.txt"
    if transcript_path.exists():
        return transcript_path.read_text(encoding="utf-8")

    configure_ffmpeg_env()
    import whisper

    model = whisper.load_model(model_name)
    result = model.transcribe(str(audio_path), fp16=False)
    text = result.get("text", "").strip()
    transcript_path.write_text(text, encoding="utf-8")
    return text


def _detect_hook_style(first_sentences: list[str]) -> str:
    if not first_sentences:
        return "unknown"
    opening = " ".join(first_sentences[:2]).lower()
    styles = []
    if re.search(r"\?", opening):
        styles.append("question-hook")
    if re.search(r"^(i |my |me )", opening):
        styles.append("personal-story")
    if re.search(r"^(you |your )", opening):
        styles.append("direct-address")
    for pattern in HOOK_PATTERNS:
        if re.search(pattern, opening, re.I):
            styles.append("pattern-hook")
            break
    if re.search(r"\d+", opening):
        styles.append("numeric-hook")
    return ", ".join(styles) if styles else "statement-hook"


def _emotional_keywords(text: str) -> dict[str, int]:
    words = re.findall(r"\b\w+\b", text.lower())
    counts: dict[str, int] = {}
    for emotion, keywords in EMOTION_KEYWORDS.items():
        counts[emotion] = sum(1 for w in words if w in keywords)
    return counts


def _analyze_transcript(text: str, duration_seconds: float) -> dict[str, Any]:
    sentences = tokenize_sentences(text)
    words = word_count(text)
    wpm = (words / max(duration_seconds, 1)) * 60 if duration_seconds else 0
    sent_lengths = [word_count(s) for s in sentences]
    avg_sent_len = sum(sent_lengths) / len(sent_lengths) if sent_lengths else 0

    hook_sents = sentences[:2]
    hook_style = _detect_hook_style(hook_sents)
    bigrams = extract_ngrams(text, 2, min_freq=2)
    trigrams = extract_ngrams(text, 3, min_freq=2)
    emotions = _emotional_keywords(text)

    # Repeated narrative openers
    openers = Counter(s.split()[0].lower() for s in sentences if s.split())
    structures = []
    if any(re.match(r"^(when|if|after)", s.lower()) for s in sentences):
        structures.append("conditional-temporal")
    if any(re.match(r"^(but|however|yet)", s.lower()) for s in sentences[1:]):
        structures.append("contrast-pivot")
    if any(re.match(r"^(so|therefore|and that)", s.lower()) for s in sentences):
        structures.append("resolution-close")

    return {
        "words_per_minute": round(wpm, 1),
        "sentence_count": len(sentences),
        "avg_sentence_length": round(avg_sent_len, 1),
        "hook_style": hook_style,
        "emotional_keywords": emotions,
        "recurring_phrases": [g for g, _ in (bigrams + trigrams)[:15]],
        "narrative_structures": structures,
        "hook_text": " ".join(hook_sents),
    }


def analyze_audio(config: Config, video_dirs: list[Path] | None = None) -> Path:
    """Run audio extraction, transcription, and analysis for all downloaded videos."""
    config.ensure_dirs()
    if video_dirs is None:
        video_dirs = [
            d for d in config.downloads_dir.iterdir() if d.is_dir() and (d / "video.mp4").exists()
        ]

    all_analyses: list[dict[str, Any]] = []
    for vdir in tqdm(video_dirs, desc="Audio analysis"):
        video_path = vdir / "video.mp4"
        audio_path = vdir / "audio.mp3"
        meta_path = vdir / "metadata.json"

        if not video_path.exists():
            continue
        try:
            _extract_audio(video_path, audio_path)
            text = _transcribe(audio_path, config.whisper_model)
            duration = 60.0
            if meta_path.exists():
                import json

                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                duration = float(meta.get("duration") or 60)
            analysis = _analyze_transcript(text, duration)
            analysis["video_id"] = vdir.name
            analysis["transcript_preview"] = text[:300]
            all_analyses.append(analysis)
        except Exception as exc:
            logger.error("Audio analysis failed for %s: %s", vdir.name, exc)

    # Aggregate report
    if not all_analyses:
        body = "No audio analyses completed. Ensure videos are downloaded."
    else:
        avg_wpm = sum(a["words_per_minute"] for a in all_analyses) / len(all_analyses)
        avg_sent = sum(a["avg_sentence_length"] for a in all_analyses) / len(all_analyses)
        hook_styles = Counter(a["hook_style"] for a in all_analyses)
        all_phrases = Counter()
        for a in all_analyses:
            for p in a["recurring_phrases"]:
                all_phrases[p] += 1
        agg_emotions: dict[str, float] = {}
        for dim in EMOTION_KEYWORDS:
            vals = [a["emotional_keywords"].get(dim, 0) for a in all_analyses]
            agg_emotions[dim] = round(sum(vals) / len(vals), 2)

        per_video = "\n".join(
            f"### {a['video_id']}\n"
            f"- WPM: {a['words_per_minute']} | Avg sentence: {a['avg_sentence_length']}\n"
            f"- Hook style: {a['hook_style']}\n"
            f"- Hook: _{a['hook_text'][:120]}_\n"
            f"- Structures: {', '.join(a['narrative_structures']) or 'none'}\n"
            for a in all_analyses
        )

        body = (
            f"**Videos analyzed:** {len(all_analyses)}\n\n"
            f"### Channel Averages\n"
            f"- Average words per minute: **{avg_wpm:.1f}**\n"
            f"- Average sentence length: **{avg_sent:.1f}** words\n\n"
            f"### Hook Style Distribution\n"
            + "\n".join(f"- {k}: {v}" for k, v in hook_styles.most_common())
            + "\n\n### Emotional Keyword Density (avg per video)\n"
            + "\n".join(f"- **{k}**: {v}" for k, v in sorted(agg_emotions.items(), key=lambda x: -x[1]))
            + "\n\n### Top Recurring Phrases\n"
            + "\n".join(f"- \"{p}\" ({c}x)" for p, c in all_phrases.most_common(20))
            + f"\n\n## Per-Video Breakdown\n\n{per_video}"
        )

    output = config.audio_analysis_md
    write_markdown(output, "Audio Analysis Report", {"Summary": body})
    logger.info("Wrote audio analysis to %s", output)
    return output

"""STEP 6 — Emotional Analysis: cluster videos by emotional profile."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

from channel_analyzer.audio_analysis import EMOTION_KEYWORDS
from channel_analyzer.config import Config
from channel_analyzer.utils import read_csv, write_markdown

logger = logging.getLogger(__name__)

EMOTION_SEEDS = {
    "hope": "hopeful optimistic bright future believing dreams possibility",
    "loneliness": "lonely isolated empty silence solitude disconnected alone",
    "love": "love heart caring devotion warmth connection together",
    "healing": "healing recovery peace calm restoration soothing mend",
    "growth": "growth learning evolving progress journey becoming better",
    "spirituality": "spiritual soul faith divine universe sacred prayer",
    "self-worth": "self worth value deserving enough confidence identity",
    "acceptance": "acceptance letting go forgiveness okay release surrender",
}


def _emotion_vector(text: str, model: SentenceTransformer) -> np.ndarray:
    """Score text against each emotion dimension via embedding similarity."""
    if not text.strip():
        return np.zeros(len(EMOTION_SEEDS))

    text_emb = model.encode([text], normalize_embeddings=True)[0]
    seed_embs = model.encode(list(EMOTION_SEEDS.values()), normalize_embeddings=True)
    scores = seed_embs @ text_emb
    # Blend with keyword hits
    words = set(re.findall(r"\b\w+\b", text.lower()))
    for i, (dim, keywords) in enumerate(EMOTION_KEYWORDS.items()):
        kw_score = sum(1 for k in keywords if k in words) / max(len(keywords), 1)
        scores[i] = 0.7 * scores[i] + 0.3 * kw_score
    return scores


def _load_transcripts(downloads_dir: Path) -> dict[str, str]:
    transcripts: dict[str, str] = {}
    for vdir in downloads_dir.iterdir():
        if not vdir.is_dir():
            continue
        tpath = vdir / "transcript.txt"
        if tpath.exists():
            transcripts[vdir.name] = tpath.read_text(encoding="utf-8")
    return transcripts


def _load_visual_summaries(frames_cache_dir: Path) -> dict[str, str]:
    """Build short visual descriptions from cached frame metadata."""
    summaries: dict[str, str] = {}
    cache = frames_cache_dir
    if cache.exists():
        for f in cache.iterdir():
            if f.suffix == ".jpg":
                parts = f.stem.split("_", 1)
                if len(parts) == 2:
                    vid = parts[1]
                    summaries.setdefault(vid, "visual frames captured")
    return summaries


def analyze_emotions(config: Config) -> Path:
    """Cluster videos by emotional profile from transcripts and visuals."""
    config.ensure_dirs()
    top_csv = config.top_videos_csv
    df = read_csv(top_csv)
    transcripts = _load_transcripts(config.downloads_dir)
    visual_hints = _load_visual_summaries(config.frames_cache_dir)

    if not transcripts:
        raise FileNotFoundError("No transcripts found. Run audio analysis first.")

    logger.info("Loading sentence transformer model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    video_ids: list[str] = []
    vectors: list[np.ndarray] = []
    combined_texts: list[str] = []

    for vid, text in tqdm(transcripts.items(), desc="Emotion scoring"):
        visual = visual_hints.get(vid, "")
        combined = f"{text}\n\nVisual context: {visual}"
        vec = _emotion_vector(combined, model)
        video_ids.append(vid)
        vectors.append(vec)
        combined_texts.append(combined)

    matrix = np.vstack(vectors)
    dim_names = list(EMOTION_SEEDS.keys())
    n_clusters = min(5, max(2, len(video_ids) // 3))
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(matrix)

    cluster_data: list[dict[str, Any]] = []
    for i, vid in enumerate(video_ids):
        row = {"video_id": vid, "cluster": int(labels[i])}
        for j, dim in enumerate(dim_names):
            row[dim] = round(float(matrix[i, j]), 3)
        title = ""
        if not df.empty and "video_id" in df.columns:
            match = df[df["video_id"].astype(str) == vid]
            if not match.empty:
                title = str(match.iloc[0].get("title", ""))
        row["title"] = title
        cluster_data.append(row)

    cluster_df = pd.DataFrame(cluster_data)
    cluster_df.to_csv(config.emotion_scores_csv, index=False)

    sections: dict[str, str] = {}
    for c in range(n_clusters):
        members = cluster_df[cluster_df["cluster"] == c]
        centroid = members[dim_names].mean()
        dominant = centroid.idxmax()
        secondary = centroid.sort_values(ascending=False).index[1]

        member_lines = "\n".join(
            f"- **{r['title'][:60]}** ({r['video_id']}) — "
            f"top: {dominant} ({r[dominant]:.2f})"
            for _, r in members.iterrows()
        )
        profile = "\n".join(
            f"- **{d}**: {centroid[d]:.3f}" for d in dim_names
        )
        sections[f"Cluster {c + 1}: {dominant.title()} / {secondary.title()}"] = (
            f"**{len(members)} videos** in this cluster.\n\n"
            f"### Emotional Profile\n{profile}\n\n"
            f"### Members\n{member_lines}"
        )

    # Cross-channel emotional signature
    channel_avg = cluster_df[dim_names].mean().sort_values(ascending=False)
    signature = "\n".join(
        f"- **{d}**: {v:.3f}" for d, v in channel_avg.items()
    )
    sections["Channel Emotional Signature"] = signature

    output = config.emotion_clusters_md
    write_markdown(output, "Emotional Cluster Analysis", sections)
    logger.info("Wrote emotion clusters to %s", output)
    return output

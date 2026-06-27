"""STEP 9 — Quote Pattern Analysis: extract, cluster, and theme quotes."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

import pandas as pd
from sklearn.cluster import AgglomerativeClustering
from sentence_transformers import SentenceTransformer

from channel_analyzer.config import Config
from channel_analyzer.utils import tokenize_sentences, write_markdown

logger = logging.getLogger(__name__)

QUOTE_PATTERNS = [
    re.compile(r'"([^"]{10,200})"'),
    re.compile(r"'([^']{10,200})'"),
    re.compile(r"«([^»]{10,200})»"),
]

THEME_SEEDS = {
    "wisdom": "wisdom truth lesson learned knowledge understanding",
    "self-love": "love yourself worth enough deserve care compassion",
    "healing": "heal pain hurt recover mend broken peace",
    "motivation": "start keep going never give up push forward achieve",
    "relationships": "love together trust connection partner friend family",
    "spirituality": "soul universe faith divine purpose meaning",
    "growth": "grow change evolve become better transform journey",
    "acceptance": "accept let go okay fine release forgive move on",
}


def _extract_quotes(text: str, video_id: str, title: str) -> list[dict[str, str]]:
    quotes: list[dict[str, str]] = []
    for pattern in QUOTE_PATTERNS:
        for match in pattern.finditer(text):
            q = match.group(1).strip()
            if len(q.split()) >= 3:
                quotes.append({"quote": q, "video_id": video_id, "title": title, "source": "explicit"})

    # Memorable standalone sentences (short, punchy)
    for sent in tokenize_sentences(text):
        words = sent.split()
        if 5 <= len(words) <= 25 and not sent.endswith("?"):
            if any(
                w in sent.lower()
                for w in ("you", "your", "love", "life", "heart", "never", "always", "remember")
            ):
                quotes.append(
                    {"quote": sent, "video_id": video_id, "title": title, "source": "narrative"}
                )
    return quotes


def _assign_theme(quote: str, model: SentenceTransformer) -> str:
    q_emb = model.encode([quote], normalize_embeddings=True)[0]
    seed_texts = list(THEME_SEEDS.values())
    seed_names = list(THEME_SEEDS.keys())
    seed_embs = model.encode(seed_texts, normalize_embeddings=True)
    scores = seed_embs @ q_emb
    return seed_names[int(scores.argmax())]


def analyze_quotes(config: Config) -> tuple[Path, Path]:
    """Extract quotes, cluster by theme, write CSV and markdown."""
    config.ensure_dirs()
    all_quotes: list[dict[str, str]] = []

    top_csv = config.top_videos_csv
    titles: dict[str, str] = {}
    if top_csv.exists():
        df = pd.read_csv(top_csv)
        for _, row in df.iterrows():
            titles[str(row["video_id"])] = str(row.get("title", ""))

    for vdir in sorted(config.downloads_dir.iterdir()):
        if not vdir.is_dir():
            continue
        tpath = vdir / "transcript.txt"
        if not tpath.exists():
            continue
        text = tpath.read_text(encoding="utf-8")
        vid = vdir.name
        all_quotes.extend(_extract_quotes(text, vid, titles.get(vid, "")))

    if not all_quotes:
        csv_path = config.quote_database_csv
        pd.DataFrame(columns=["quote", "video_id", "title", "source", "theme", "cluster"]).to_csv(
            csv_path, index=False
        )
        md_path = config.quote_patterns_md
        write_markdown(md_path, "Quote Pattern Analysis", {"Summary": "No quotes extracted."})
        return csv_path, md_path

    # Deduplicate
    seen: set[str] = set()
    unique: list[dict[str, str]] = []
    for q in all_quotes:
        key = q["quote"].lower()[:80]
        if key not in seen:
            seen.add(key)
            unique.append(q)

    logger.info("Clustering %d unique quotes...", len(unique))
    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = model.encode([q["quote"] for q in unique], normalize_embeddings=True)

    n_clusters = min(8, max(2, len(unique) // 5))
    if len(unique) >= n_clusters:
        clustering = AgglomerativeClustering(n_clusters=n_clusters)
        cluster_labels = clustering.fit_predict(embeddings)
    else:
        cluster_labels = list(range(len(unique)))

    for i, q in enumerate(unique):
        q["theme"] = _assign_theme(q["quote"], model)
        q["cluster"] = int(cluster_labels[i])

    quote_df = pd.DataFrame(unique)
    csv_path = config.quote_database_csv
    quote_df.to_csv(csv_path, index=False)

    theme_groups = quote_df.groupby("theme")
    theme_sections: dict[str, str] = {}
    for theme, group in theme_groups:
        lines = "\n".join(
            f"- \"{r['quote'][:120]}\" — _{r['title'][:40]}_"
            for _, r in group.head(10).iterrows()
        )
        theme_sections[theme.replace("-", " ").title()] = (
            f"**{len(group)} quotes**\n\n{lines}"
        )

    cluster_sections: dict[str, str] = {}
    for c in sorted(quote_df["cluster"].unique()):
        members = quote_df[quote_df["cluster"] == c]
        themes = members["theme"].value_counts()
        dominant_theme = themes.index[0] if len(themes) else "mixed"
        samples = "\n".join(
            f"- \"{r['quote'][:100]}\"" for _, r in members.head(5).iterrows()
        )
        cluster_sections[f"Cluster {c + 1} ({dominant_theme})"] = samples

    md_path = config.quote_patterns_md
    sections = {
        "Overview": (
            f"**Total quotes extracted:** {len(unique)}\n"
            f"**Themes identified:** {quote_df['theme'].nunique()}\n"
            f"**Clusters:** {n_clusters}"
        ),
        **theme_sections,
        "Cluster Patterns": "\n\n".join(
            f"### {k}\n{v}" for k, v in cluster_sections.items()
        ),
    }
    write_markdown(md_path, "Quote Pattern Analysis", sections)
    logger.info("Wrote quote database to %s", csv_path)
    return csv_path, md_path

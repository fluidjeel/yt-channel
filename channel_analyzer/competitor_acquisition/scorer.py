"""Score candidate channels against WhisprsYT reference profile."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any

import numpy as np
from sentence_transformers import SentenceTransformer

from channel_analyzer.competitor_acquisition.keywords import (
    NON_RECOVERY_SIGNALS,
    RECOVERY_SIGNALS,
    STYLE_SIGNALS,
)
from channel_analyzer.config import Config
from channel_analyzer.utils import read_csv
from channel_analyzer.competitor_acquisition.fast_profile import FastChannelProfile, fetch_fast_profile

logger = logging.getLogger(__name__)

EMOTION_SEEDS = {
    "heartbreak": "heartbreak pain loss betrayal longing",
    "loneliness": "lonely alone isolated empty",
    "healing": "healing recovery growth mend",
    "self_love": "self love self worth deserve enough",
    "acceptance": "acceptance letting go peace surrender",
    "resilience": "resilience strength quiet hope endure",
    "hope": "hopeful future light tomorrow",
}


@dataclass
class ScoredCandidate:
    channel_name: str
    channel_url: str
    subscribers: int
    avg_views: float
    video_sample_count: int
    similarity_score: float
    style_similarity: float
    content_similarity: float
    emotional_similarity: float
    audience_similarity: float
    comment_similarity: float
    confidence: float
    why_similar: str
    why_different: str
    discovery_source: str
    niche_signals: list[str] = field(default_factory=list)

    def to_row(self) -> dict[str, Any]:
        return {
            "channel": self.channel_name,
            "channel_url": self.channel_url,
            "subscribers": self.subscribers,
            "avg_views": round(self.avg_views, 0),
            "similarity_score": round(self.similarity_score, 3),
            "style_similarity": round(self.style_similarity, 3),
            "content_similarity": round(self.content_similarity, 3),
            "emotional_similarity": round(self.emotional_similarity, 3),
            "audience_similarity": round(self.audience_similarity, 3),
            "comment_similarity": round(self.comment_similarity, 3),
            "confidence": round(self.confidence, 3),
            "why_similar": self.why_similar,
            "why_different": self.why_different,
            "discovery_source": self.discovery_source,
        }


@lru_cache(maxsize=1)
def _load_model() -> SentenceTransformer:
    return SentenceTransformer("all-MiniLM-L6-v2")


def build_reference_profile(config: Config | None = None) -> tuple[str, np.ndarray, dict[str, float]]:
    """Build text corpus + emotion vector from WhisprsYT analysis."""
    config = config or Config.from_yaml()
    parts: list[str] = []

    for name in ("content_dna.md", "audience_psychology.md", "master_emotional_bible.md"):
        path = config.reports_dir / name
        if path.exists():
            parts.append(path.read_text(encoding="utf-8")[:4000])

    top_df = read_csv(config.top_videos_csv)
    if not top_df.empty and "title" in top_df.columns:
        titles = top_df.head(25)["title"].astype(str).tolist()
        parts.append(" ".join(titles))

    quotes = read_csv(config.quote_database_csv)
    if not quotes.empty and "quote" in quotes.columns:
        parts.append(" ".join(quotes["quote"].head(30).astype(str).tolist()))

    corpus = " ".join(parts)
    model = _load_model()
    ref_emb = model.encode([corpus], normalize_embeddings=True)[0]

    emotion_vec: dict[str, float] = {}
    if corpus.strip():
        for label, seed_emb in _emotion_seed_embeddings().items():
            emotion_vec[label] = float(ref_emb @ seed_emb)

    return corpus, ref_emb, emotion_vec


@lru_cache(maxsize=1)
def _emotion_seed_embeddings() -> dict[str, np.ndarray]:
    model = _load_model()
    return {
        label: model.encode([seed_text], normalize_embeddings=True)[0]
        for label, seed_text in EMOTION_SEEDS.items()
    }


def _keyword_score(text: str, keywords: list[str]) -> float:
    lower = text.lower()
    hits = sum(1 for k in keywords if k in lower)
    return min(1.0, hits / max(len(keywords) * 0.15, 1))


def _fetch_channel_text(channel_url: str, sample: int = 8) -> tuple[str, str, list[str], FastChannelProfile]:
    """Lightweight channel text — titles + description only."""
    meta = fetch_fast_profile(channel_url, title_limit=sample)
    if not meta:
        raise RuntimeError(f"fast profile failed: {channel_url}")
    titles_text = " ".join(meta.top_titles)
    return titles_text, meta.description, meta.top_titles, meta


def score_candidate(
    candidate: dict[str, str],
    ref_emb: np.ndarray,
    ref_emotions: dict[str, float],
    ref_corpus: str,
    seed_embs: dict[str, np.ndarray] | None = None,
) -> ScoredCandidate | None:
    url = candidate.get("channel_url", "")
    if not url:
        return None

    # Skip seed itself in ranking (still could appear)
    try:
        titles_text, desc_text, titles, meta = _fetch_channel_text(url)
    except Exception as exc:
        logger.debug("Metadata failed for %s: %s", url, exc)
        return None

    combined = f"{meta.description} {titles_text} {desc_text}"
    if len(combined.strip()) < 20:
        return None

    # Filter obvious non-niche
    lower = combined.lower()
    if any(sig in lower for sig in NON_RECOVERY_SIGNALS):
        non_rec = sum(1 for s in NON_RECOVERY_SIGNALS if s in lower)
        if non_rec >= 2 and _keyword_score(lower, RECOVERY_SIGNALS) < 0.1:
            return None

    model = _load_model()
    cand_emb = model.encode([combined], normalize_embeddings=True)[0]

    content_sim = float(cand_emb @ ref_emb)
    style_sim = (
        _keyword_score(lower, STYLE_SIGNALS) * 0.5
        + _keyword_score(lower, ["poetry", "quote", "shorts"]) * 0.5
    )

    # Emotional similarity vs reference emotion profile
    seed_embs = seed_embs or _emotion_seed_embeddings()
    cand_emotions: dict[str, float] = {}
    for label, seed_emb in seed_embs.items():
        cand_emotions[label] = float(cand_emb @ seed_emb)
    if ref_emotions:
        ref_vec = np.array(list(ref_emotions.values()))
        cand_vec = np.array([cand_emotions[k] for k in ref_emotions.keys()])
        emotional_sim = float(
            np.dot(ref_vec, cand_vec) / (np.linalg.norm(ref_vec) * np.linalg.norm(cand_vec) + 1e-9)
        )
    else:
        emotional_sim = _keyword_score(lower, RECOVERY_SIGNALS)

    # Audience proxy: overlap of recovery keywords with reference comment themes
    audience_sim = _keyword_score(lower, RECOVERY_SIGNALS + ["needed this", "thank you", "relatable"])

    # Comment similarity unavailable without fetching — estimate from title tone
    comment_sim = audience_sim * 0.7

    weights = {
        "content": 0.30,
        "style": 0.20,
        "emotional": 0.25,
        "audience": 0.15,
        "comment": 0.10,
    }
    overall = (
        weights["content"] * max(0, content_sim)
        + weights["style"] * style_sim
        + weights["emotional"] * max(0, emotional_sim)
        + weights["audience"] * audience_sim
        + weights["comment"] * comment_sim
    )

    signals = [k for k in RECOVERY_SIGNALS if k in lower][:4]
    style_hits = [k for k in STYLE_SIGNALS if k in lower][:3]

    why_similar_parts = []
    if style_hits:
        why_similar_parts.append(f"Style signals: {', '.join(style_hits)}")
    if signals:
        why_similar_parts.append(f"Recovery themes: {', '.join(signals)}")
    if content_sim > 0.35:
        why_similar_parts.append(f"Content embedding similarity {content_sim:.2f}")
    why_similar = "; ".join(why_similar_parts) or "Moderate textual overlap with reference"

    why_diff_parts = []
    if "stoic" in lower and "anime" not in lower:
        why_diff_parts.append("Stoicism/philosophy tilt vs anime aesthetic")
    if "motivation" in lower and "healing" not in lower:
        why_diff_parts.append("Motivation-heavy vs recovery-heavy")
    if meta.subscriber_count > 500_000:
        why_diff_parts.append("Much larger channel — audience scale differs")
    if not why_diff_parts:
        why_diff_parts.append("Needs full pipeline to confirm visual/comment overlap")
    why_different = "; ".join(why_diff_parts)

    avg_views = meta.avg_views
    confidence = min(0.9, 0.3 + 0.3 * min(len(titles), 8) / 8 + 0.2 * (1 if content_sim > 0.3 else 0))

    return ScoredCandidate(
        channel_name=meta.channel_name or candidate.get("channel_name", url),
        channel_url=url,
        subscribers=meta.subscriber_count,
        avg_views=avg_views,
        video_sample_count=len(titles),
        similarity_score=overall,
        style_similarity=style_sim,
        content_similarity=max(0, content_sim),
        emotional_similarity=max(0, emotional_sim),
        audience_similarity=audience_sim,
        comment_similarity=comment_sim,
        confidence=confidence,
        why_similar=why_similar,
        why_different=why_different,
        discovery_source=candidate.get("discovery_source", ""),
        niche_signals=signals + style_hits,
    )


def score_candidate_offline(
    candidate: dict[str, str],
    ref_emb: np.ndarray,
    ref_emotions: dict[str, float],
    seed_embs: dict[str, np.ndarray],
) -> ScoredCandidate:
    """Score using discovery metadata only — no yt-dlp (rate-limit safe)."""
    url = candidate.get("channel_url", "")
    name = candidate.get("channel_name", "")
    source = candidate.get("discovery_source", "")
    handle = url.split("/@")[-1].lower() if "/@" in url else ""

    if url.rstrip("/").lower().endswith("@whisprsyt"):
        return None

    combined = f"{name} {handle}".strip()
    lower = combined.lower()
    source_lower = source.lower()

    model = _load_model()
    cand_emb = model.encode([combined], normalize_embeddings=True)[0]
    content_sim = float(cand_emb @ ref_emb)

    style_sim = _keyword_score(lower, STYLE_SIGNALS + ["poetry", "quote", "shorts", "anime", "aesthetic", "poet", "verse", "soul", "whisper"])
    emotional_sim = _keyword_score(lower, RECOVERY_SIGNALS)
    if ref_emotions:
        cand_emotions = {label: float(cand_emb @ seed_emb) for label, seed_emb in seed_embs.items()}
        ref_vec = np.array(list(ref_emotions.values()))
        cand_vec = np.array([cand_emotions[k] for k in ref_emotions.keys()])
        emotional_sim = max(
            emotional_sim,
            float(np.dot(ref_vec, cand_vec) / (np.linalg.norm(ref_vec) * np.linalg.norm(cand_vec) + 1e-9)),
        )

    audience_sim = _keyword_score(lower, RECOVERY_SIGNALS + ["relatable", "comfort"])
    comment_sim = audience_sim * 0.6

    # Boost @-handle channels and benchmark seeds; penalize generic healing-only names
    if "/@" in url:
        style_sim = min(1.0, style_sim + 0.2)
    if source == "benchmark_yaml":
        overall_boost = 0.35
        confidence = 0.60
    else:
        overall_boost = 0.0
        confidence = 0.35

    # Require niche format signal for non-benchmark channels
    niche_format = any(
        tok in lower for tok in ("poet", "verse", "soul", "whisper", "anime", "quote", "aesthetic", "lofi", "faceless", "lines", "mind")
    )
    if source != "benchmark_yaml" and not niche_format:
        style_sim *= 0.5
        emotional_sim *= 0.7

    # Downrank obvious wrong-format channels
    if any(tok in lower for tok in ("ted", "matthew hussey", "psych2go", "dove", "jay shetty", "entertainment")):
        overall_boost -= 0.2

    weights = {"content": 0.30, "style": 0.20, "emotional": 0.25, "audience": 0.15, "comment": 0.10}
    overall = (
        weights["content"] * max(0, content_sim)
        + weights["style"] * style_sim
        + weights["emotional"] * max(0, emotional_sim)
        + weights["audience"] * audience_sim
        + weights["comment"] * comment_sim
        + overall_boost
    )

    signals = [k for k in RECOVERY_SIGNALS if k in lower][:4]
    style_hits = [k for k in STYLE_SIGNALS if k in lower][:3]
    why_similar_parts = []
    if style_hits or "anime" in lower or "poet" in lower:
        why_similar_parts.append(f"Name signals: {name} (source: {source})")
    if signals:
        why_similar_parts.append(f"Recovery keywords: {', '.join(signals)}")
    if content_sim > 0.3:
        why_similar_parts.append(f"Embedding similarity {content_sim:.2f}")
    why_similar = "; ".join(why_similar_parts) or f"Discovered via {source}"

    why_diff = []
    if "whisprs" in lower:
        why_diff.append("Reference channel — exclude from benchmark cohort")
    if "stoic" in lower or "stoicism" in source_lower:
        why_diff.append("Stoicism-adjacent discovery query")
    if "lofi" in lower or "geisha" in lower:
        why_diff.append("Lofi/aesthetic channel — may lack recovery comment density")
    if "motivation" in lower and "healing" not in lower:
        why_diff.append("Motivation tilt vs recovery tilt")
    if not why_diff:
        why_diff.append("Metadata not fetched (rate limit) — validate with full pipeline")
    why_different = "; ".join(why_diff)

    return ScoredCandidate(
        channel_name=name or handle or url,
        channel_url=url,
        subscribers=0,
        avg_views=0.0,
        video_sample_count=0,
        similarity_score=overall,
        style_similarity=style_sim,
        content_similarity=max(0, content_sim),
        emotional_similarity=max(0, emotional_sim),
        audience_similarity=audience_sim,
        comment_similarity=comment_sim,
        confidence=confidence,
        why_similar=why_similar,
        why_different=why_different,
        discovery_source=source,
        niche_signals=signals + style_hits,
    )


def score_all_candidates_offline(
    candidates: list[dict[str, str]],
    config: Config | None = None,
    max_results: int = 40,
) -> list[ScoredCandidate]:
    ref_corpus, ref_emb, ref_emotions = build_reference_profile(config)
    seed_embs = _emotion_seed_embeddings()
    scored = [
        s for s in (
            score_candidate_offline(c, ref_emb, ref_emotions, seed_embs)
            for c in candidates
        )
        if s is not None
    ]
    scored = [s for s in scored if s.similarity_score >= 0.32]
    return sorted(scored, key=lambda x: -x.similarity_score)[:max_results]


def _quick_prefilter_score(candidate: dict[str, str]) -> float:
    """Rank discovery rows before expensive metadata fetch."""
    text = f"{candidate.get('channel_name', '')} {candidate.get('discovery_source', '')}".lower()
    return _keyword_score(text, RECOVERY_SIGNALS + STYLE_SIGNALS)


def score_all_candidates(
    candidates: list[dict[str, str]],
    config: Config | None = None,
    max_score: int = 40,
) -> list[ScoredCandidate]:
    ref_corpus, ref_emb, ref_emotions = build_reference_profile(config)
    seed_embs = _emotion_seed_embeddings()

    # Pre-rank by cheap heuristics, then deep-score top N only
    ranked = sorted(candidates, key=lambda c: -_quick_prefilter_score(c))
    deep_pool = ranked[: min(len(ranked), max_score + 15)]

    scored: list[ScoredCandidate] = []
    for i, cand in enumerate(deep_pool):
        if i % 5 == 0:
            logger.info("Scoring channel %d/%d...", i + 1, len(deep_pool))
        result = score_candidate(cand, ref_emb, ref_emotions, ref_corpus, seed_embs)
        if result and result.similarity_score >= 0.25:
            scored.append(result)
        if len(scored) >= max_score and i >= max_score:
            break

    return sorted(scored, key=lambda x: -x.similarity_score)

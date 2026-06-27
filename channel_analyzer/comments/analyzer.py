"""Analyze comments: spam filter, clustering, psychology signals."""

from __future__ import annotations

import logging
import re
from collections import Counter, defaultdict
from typing import Any

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.cluster import AgglomerativeClustering

from channel_analyzer.comments.models import (
    EMOTIONAL_STATES,
    LIFE_SITUATIONS,
    COMMENT_THEMES,
    AnalyzedComment,
    CommentCluster,
    RawComment,
)

logger = logging.getLogger(__name__)

SPAM_PATTERNS = [
    r"check\s+(out\s+)?my\s+channel",
    r"sub\s*scribe",
    r"follow\s+me",
    r"http[s]?://",
    r"www\.\w+",
    r"^\s*first\s*$",
    r"^\s*\d+\s*/\s*\d+\s*$",
    r"crypto|bitcoin|forex|nft",
    r"whatsapp|telegram\s+me",
]

SAVE_SIGNAL_PHRASES = [
    "needed this",
    "needed to hear",
    "needed to see",
    "saving this",
    "saved this",
    "bookmark",
    "screenshot",
    "came back",
    "rewatch",
    "listen again",
    "keeping this",
    "for later",
    "this hit",
    "this spoke to me",
]

SHARE_SIGNAL_PHRASES = [
    "sent this to",
    "shared this",
    "shared with",
    "tagged",
    "showed my",
    "sent to my friend",
    "everyone needs",
    "sharing with",
    "forwarded",
    "told my",
]

EMOTION_SEEDS = {
    "hope": "hopeful optimistic future believing dreams possibility",
    "loneliness": "lonely isolated empty silence disconnected alone",
    "heartbreak": "heartbreak broken heart pain betrayal hurt crying",
    "healing": "healing recovery peace calm restoration soothing mend",
    "validation": "felt seen understood validated recognized finally someone said",
    "motivation": "motivation push forward keep going never give up",
    "acceptance": "acceptance letting go okay release surrender forgive",
    "gratitude": "thank you grateful appreciate blessed thankful",
    "anger": "angry furious toxic hate unfair rage",
    "nostalgia": "miss remember past memories used to wish could go back",
    "self-worth": "worth enough deserve value confidence identity",
    "longing": "miss longing yearn wish want need crave",
}

LIFE_SEED_TEXTS = {
    "breakup": "breakup ex relationship ended split divorce",
    "toxic_relationship": "toxic abusive narcissist manipulation red flags",
    "unrequited_love": "unrequited one sided love not reciprocated",
    "self_esteem": "self esteem confidence insecure not enough",
    "family_conflict": "family parents mother father trauma childhood",
    "loneliness": "alone lonely no friends isolated nobody",
    "healing_journey": "healing journey recovery growth moving forward",
    "career_stress": "job work career burnout stress money",
    "friendship": "friend friends betrayal loyalty trust",
    "personal_growth": "grow change evolve become better transform",
    "spiritual_search": "soul universe faith god purpose meaning",
    "identity": "who am i identity self discovery finding myself",
}

THEME_SEEDS = {
    "relatability": "so relatable this is me exactly felt that",
    "self_love": "love yourself self love worth deserve care",
    "letting_go": "let go release move on detach surrender",
    "moving_on": "moving on past behind new chapter forward",
    "validation": "needed to hear finally someone understands felt seen",
    "motivation": "motivated inspired push forward keep going",
    "heartbreak": "heartbreak broken crying tears pain hurt",
    "wisdom": "wise truth lesson learned words wisdom",
    "gratitude": "thank you grateful appreciate blessed",
    "sharing_with_others": "sent shared tagged showed friend family",
    "saving_for_later": "save bookmark screenshot rewatch came back",
    "creator_praise": "love your content amazing voice whisprs channel",
}


def is_spam(text: str, min_length: int = 8) -> bool:
    cleaned = text.strip()
    if len(cleaned) < min_length:
        return True
    if not re.search(r"[a-zA-Z]", cleaned):
        return True
    lower = cleaned.lower()
    for pat in SPAM_PATTERNS:
        if re.search(pat, lower, re.IGNORECASE):
            return True
    # Repeated character spam
    if re.search(r"(.)\1{6,}", cleaned):
        return True
    return False


def detect_save_signal(text: str) -> bool:
    lower = text.lower()
    return any(p in lower for p in SAVE_SIGNAL_PHRASES)


def detect_share_signal(text: str) -> bool:
    lower = text.lower()
    return any(p in lower for p in SHARE_SIGNAL_PHRASES)


def _softmax_rows(scores: np.ndarray) -> np.ndarray:
    exp = np.exp(scores - scores.max(axis=1, keepdims=True))
    return exp / exp.sum(axis=1, keepdims=True)


def _precompute_seed_embeddings(
    model: SentenceTransformer, seeds: dict[str, str]
) -> tuple[list[str], np.ndarray]:
    labels = list(seeds.keys())
    embs = model.encode(list(seeds.values()), normalize_embeddings=True, show_progress_bar=False)
    return labels, np.array(embs)


def _batch_best_labels(
    text_embs: np.ndarray, labels: list[str], seed_embs: np.ndarray
) -> tuple[list[str], list[float]]:
    scores = text_embs @ seed_embs.T
    probs = _softmax_rows(scores)
    idx = scores.argmax(axis=1)
    return [labels[i] for i in idx], [float(probs[r, idx[r]]) for r in range(len(idx))]


def _batch_pain_scores(text_embs: np.ndarray, pain_embs: np.ndarray) -> list[float]:
    scores = text_embs @ pain_embs.T
    return [
        float(max(0.0, min(1.0, (row[0] - row[1] + 1) / 2)))
        for row in scores
    ]


def _cluster_comments(
    embs: np.ndarray,
    n_clusters: int,
) -> np.ndarray:
    if len(embs) < 2:
        return np.array([0])
    k = min(n_clusters, max(2, len(embs) // 8))
    clustering = AgglomerativeClustering(n_clusters=k, metric="cosine", linkage="average")
    return clustering.fit_predict(embs)


def _cluster_confidence(labels: np.ndarray, embs: np.ndarray) -> dict[int, float]:
    conf: dict[int, float] = {}
    for cid in set(labels):
        mask = labels == cid
        cluster_embs = embs[mask]
        if len(cluster_embs) < 2:
            conf[cid] = 0.5
            continue
        centroid = cluster_embs.mean(axis=0)
        centroid /= np.linalg.norm(centroid) + 1e-9
        sims = cluster_embs @ centroid
        conf[cid] = float(np.clip(sims.mean(), 0, 1))
    return conf


def _top_phrases(texts: list[str], min_freq: int = 2) -> list[str]:
    grams: Counter[str] = Counter()
    for text in texts:
        words = re.findall(r"\b[a-z]{3,}\b", text.lower())
        for n in (2, 3):
            for i in range(len(words) - n + 1):
                grams[" ".join(words[i : i + n])] += 1
    return [g for g, c in grams.most_common(8) if c >= min_freq]


def analyze_comments(
    raw_comments: list[RawComment],
    video_meta: dict[str, dict[str, Any]],
    embedding_model: str = "all-MiniLM-L6-v2",
    n_clusters: int = 12,
    min_comment_length: int = 8,
) -> tuple[list[AnalyzedComment], list[CommentCluster], dict[str, Any]]:
    """
    Filter spam, cluster, label emotions/themes, compute psychology signals.

    video_meta: video_id -> {title, rank, views_per_day, channel}
    """
    model = SentenceTransformer(embedding_model)

    spam_rows: list[AnalyzedComment] = []
    spam_count = 0

    for c in raw_comments:
        meta = video_meta.get(c.video_id, {})
        channel = c.channel or str(meta.get("channel", ""))
        base_kwargs = dict(
            comment_id=c.comment_id,
            video_id=c.video_id,
            channel=channel,
            video_title=str(meta.get("title", "")),
            video_rank=int(meta.get("rank", 0)),
            video_views_per_day=float(meta.get("views_per_day", 0)),
            text=c.text,
            like_count=c.like_count,
            author=c.author,
        )
        if is_spam(c.text, min_length=min_comment_length):
            spam_count += 1
            spam_rows.append(
                AnalyzedComment(
                    **base_kwargs,
                    is_spam=True,
                    cluster_id=-1,
                    theme="spam",
                    emotional_state="",
                    life_situation="",
                    save_signal=False,
                    share_signal=False,
                    pain_point_score=0.0,
                    confidence=0.9,
                )
            )

    non_spam_raw = [c for c in raw_comments if not is_spam(c.text, min_length=min_comment_length)]
    texts = [c.text for c in non_spam_raw]

    if texts:
        text_embs = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    else:
        text_embs = np.zeros((0, 384))

    theme_labels, theme_seed_embs = _precompute_seed_embeddings(model, THEME_SEEDS)
    emotion_labels, emotion_seed_embs = _precompute_seed_embeddings(model, EMOTION_SEEDS)
    life_labels, life_seed_embs = _precompute_seed_embeddings(model, LIFE_SEED_TEXTS)
    pain_seed_embs = model.encode(
        [
            "deep pain hurt suffering struggle broken lost hopeless",
            "neutral casual comment praise simple reaction",
        ],
        normalize_embeddings=True,
        show_progress_bar=False,
    )

    labels = _cluster_comments(text_embs, n_clusters) if len(texts) else np.array([])
    cluster_conf = _cluster_confidence(labels, text_embs) if len(texts) else {}

    themes, theme_confs = _batch_best_labels(text_embs, theme_labels, theme_seed_embs) if len(texts) else ([], [])
    emotions, emotion_confs = _batch_best_labels(text_embs, emotion_labels, emotion_seed_embs) if len(texts) else ([], [])
    lives, life_confs = _batch_best_labels(text_embs, life_labels, life_seed_embs) if len(texts) else ([], [])
    pain_scores = _batch_pain_scores(text_embs, pain_seed_embs) if len(texts) else []

    analyzed: list[AnalyzedComment] = list(spam_rows)

    for i, raw in enumerate(non_spam_raw):
        meta = video_meta.get(raw.video_id, {})
        conf = float(
            np.mean(
                [
                    theme_confs[i],
                    emotion_confs[i],
                    life_confs[i],
                    cluster_conf.get(int(labels[i]), 0.5),
                ]
            )
        )

        analyzed.append(
            AnalyzedComment(
                comment_id=raw.comment_id,
                video_id=raw.video_id,
                channel=raw.channel or str(meta.get("channel", "")),
                video_title=str(meta.get("title", "")),
                video_rank=int(meta.get("rank", 0)),
                video_views_per_day=float(meta.get("views_per_day", 0)),
                text=raw.text,
                like_count=raw.like_count,
                author=raw.author,
                is_spam=False,
                cluster_id=int(labels[i]),
                theme=themes[i],
                emotional_state=emotions[i],
                life_situation=lives[i],
                save_signal=detect_save_signal(raw.text),
                share_signal=detect_share_signal(raw.text),
                pain_point_score=pain_scores[i],
                confidence=conf,
            )
        )

    # Build cluster aggregates
    by_cluster: dict[int, list[AnalyzedComment]] = defaultdict(list)
    for ac in analyzed:
        if not ac.is_spam:
            by_cluster[ac.cluster_id].append(ac)

    channel = ""
    if analyzed:
        channel = next((a.channel for a in analyzed if a.channel), "")

    clusters: list[CommentCluster] = []
    for cid, members in sorted(by_cluster.items()):
        themes = Counter(m.theme for m in members)
        emotions = Counter(m.emotional_state for m in members)
        lives = Counter(m.life_situation for m in members)
        videos = {m.video_id for m in members}
        save_pct = 100 * sum(1 for m in members if m.save_signal) / len(members)
        share_pct = 100 * sum(1 for m in members if m.share_signal) / len(members)
        avg_vpd = float(np.mean([m.video_views_per_day for m in members]))
        sorted_members = sorted(members, key=lambda m: (-m.like_count, -m.confidence))
        examples = [m.text[:200] for m in sorted_members[:3]]
        evidence_ids = [m.comment_id for m in sorted_members[:10]]

        clusters.append(
            CommentCluster(
                cluster_id=cid,
                channel=channel,
                theme=themes.most_common(1)[0][0],
                emotional_state=emotions.most_common(1)[0][0],
                life_situation=lives.most_common(1)[0][0],
                comment_count=len(members),
                video_count=len(videos),
                avg_likes=float(np.mean([m.like_count for m in members])),
                save_signal_pct=save_pct,
                share_signal_pct=share_pct,
                confidence=cluster_conf.get(cid, 0.5),
                example_comments=examples,
                evidence_comment_ids=evidence_ids,
                avg_video_views_per_day=avg_vpd,
                top_phrases=_top_phrases([m.text for m in members]),
            )
        )

    # Performance correlation: cluster prevalence on high vs low performers
    perf_stats = _performance_correlation(analyzed, clusters, video_meta)

    # Repeated phrases across videos
    phrase_stats = _cross_video_phrases(analyzed)

    stats = {
        "total_raw": len(raw_comments),
        "spam_count": spam_count,
        "analyzed_count": len(non_spam_raw),
        "cluster_count": len(clusters),
        "save_signal_count": sum(1 for a in analyzed if a.save_signal and not a.is_spam),
        "share_signal_count": sum(1 for a in analyzed if a.share_signal and not a.is_spam),
        "performance_correlation": perf_stats,
        "repeated_phrases": phrase_stats,
    }
    return analyzed, clusters, stats


def _performance_correlation(
    analyzed: list[AnalyzedComment],
    clusters: list[CommentCluster],
    video_meta: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    if len(video_meta) < 4:
        return {}

    vpd_values = [float(m.get("views_per_day", 0)) for m in video_meta.values()]
    median_vpd = float(np.median(vpd_values))
    high_vids = {vid for vid, m in video_meta.items() if float(m.get("views_per_day", 0)) >= median_vpd}

    high_comments = [a for a in analyzed if not a.is_spam and a.video_id in high_vids]
    low_comments = [a for a in analyzed if not a.is_spam and a.video_id not in high_vids]

    def _dist(comments: list[AnalyzedComment], attr: str) -> dict[str, int]:
        return dict(Counter(getattr(c, attr) for c in comments).most_common(8))

    high_cluster_ids = Counter(a.cluster_id for a in high_comments)
    total_high = max(len(high_comments), 1)

    cluster_perf = []
    for cl in clusters:
        high_count = high_cluster_ids.get(cl.cluster_id, 0)
        cluster_perf.append(
            {
                "cluster_id": cl.cluster_id,
                "theme": cl.theme,
                "high_performer_pct": round(100 * high_count / total_high, 1),
                "avg_video_views_per_day": cl.avg_video_views_per_day,
                "confidence": cl.confidence,
            }
        )
    cluster_perf.sort(key=lambda x: -x["high_performer_pct"])

    return {
        "median_views_per_day": median_vpd,
        "high_performer_video_count": len(high_vids),
        "high_performer_themes": _dist(high_comments, "theme"),
        "high_performer_emotions": _dist(high_comments, "emotional_state"),
        "low_performer_themes": _dist(low_comments, "theme"),
        "top_clusters_on_high_performers": cluster_perf[:6],
    }


def _cross_video_phrases(analyzed: list[AnalyzedComment], min_videos: int = 2) -> list[dict[str, Any]]:
    """Find phrases repeated across multiple videos."""
    phrase_videos: dict[str, set[str]] = defaultdict(set)
    phrase_count: Counter[str] = Counter()

    for ac in analyzed:
        if ac.is_spam:
            continue
        words = re.findall(r"\b[a-z]{3,}\b", ac.text.lower())
        seen_in_comment: set[str] = set()
        for n in (2, 3, 4):
            for i in range(len(words) - n + 1):
                gram = " ".join(words[i : i + n])
                if gram in seen_in_comment:
                    continue
                seen_in_comment.add(gram)
                phrase_videos[gram].add(ac.video_id)
                phrase_count[gram] += 1

    results = []
    for phrase, vids in phrase_videos.items():
        if len(vids) >= min_videos and phrase_count[phrase] >= 2:
            results.append(
                {
                    "phrase": phrase,
                    "video_count": len(vids),
                    "comment_count": phrase_count[phrase],
                }
            )
    results.sort(key=lambda x: (-x["video_count"], -x["comment_count"]))
    return results[:30]

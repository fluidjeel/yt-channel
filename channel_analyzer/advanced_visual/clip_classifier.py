"""CLIP zero-shot classification for visual semantics."""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

# Prompt templates — anime-aware phrasing for this niche
ARCHETYPE_PROMPTS = {
    "solitary_male": "anime illustration of a solitary young man alone in nature",
    "solitary_female": "anime illustration of a solitary young woman alone in nature",
    "couple": "anime illustration of a romantic couple together",
    "traveler": "anime character traveler walking on a road or path",
    "dreamer": "anime dreamer character gazing at the sky or horizon",
    "observer": "anime character quietly observing the world from a distance",
    "no_character": "landscape scenery with no people anime background art",
}

GAZE_PROMPTS = {
    "looking_away": "anime character looking away from the camera into the distance",
    "looking_down": "anime character looking down with downcast eyes",
    "looking_up": "anime character looking up at the sky",
    "side_profile": "anime character side profile portrait",
    "back_profile": "anime character seen from behind back view",
    "direct_gaze": "anime character looking directly at viewer intense eyes",
    "no_face": "scenery without visible face or no human",
}

EXPRESSION_PROMPTS = {
    "hopeful": "hopeful melancholy expression soft light in eyes anime",
    "reflective": "reflective thoughtful calm expression anime character",
    "longing": "longing wistful yearning expression soft sadness anime",
    "peaceful_sadness": "peaceful sadness serene sorrow composed expression anime",
    "resilience": "quiet resilience strong but gentle expression anime",
    "acceptance": "acceptance letting go peaceful expression anime",
    "wonder": "wonder awe amazed expression looking at vast world anime",
}

SYMBOLISM_PROMPTS = {
    "moon": "moon in night sky anime scenery",
    "rain": "rain falling rainy atmosphere anime",
    "ocean": "ocean sea waves anime scenery",
    "clouds": "dramatic clouds sky anime",
    "sunset": "sunset golden hour anime scenery",
    "stars": "starry night stars sky anime",
    "road": "road path journey anime scenery",
    "window": "window light indoor looking outside anime",
    "birds": "birds flying sky anime",
}

RELATIONSHIP_PROMPTS = {
    "alone": "single person alone solitary anime scene",
    "couple": "couple close together anime romantic",
    "separated_couple": "two people far apart separated distance anime",
    "walking_together": "two people walking together side by side anime",
    "looking_at_each_other": "two people looking at each other anime",
    "ambiguous": "unclear human relationship in anime scene",
}

ANIME_STYLE_PROMPTS = {
    "anime": "anime art style illustration japanese animation aesthetic",
    "realistic": "realistic photograph live action",
}


@lru_cache(maxsize=1)
def _load_clip(model_name: str = "clip-ViT-B-32"):
    from sentence_transformers import SentenceTransformer

    logger.info("Loading CLIP model: %s", model_name)
    return SentenceTransformer(model_name)


def _softmax(scores: np.ndarray) -> np.ndarray:
    exp = np.exp(scores - scores.max())
    return exp / exp.sum()


def _classify(
    image: Image.Image,
    prompts: dict[str, str],
    model_name: str,
    top_k: int = 1,
    threshold: float = 0.0,
) -> list[tuple[str, float]]:
    model = _load_clip(model_name)
    img_emb = model.encode([image], convert_to_tensor=False, normalize_embeddings=True)[0]
    labels = list(prompts.keys())
    texts = list(prompts.values())
    text_embs = model.encode(texts, convert_to_tensor=False, normalize_embeddings=True)
    scores = text_embs @ img_emb
    probs = _softmax(np.array(scores, dtype=np.float64))
    ranked = sorted(zip(labels, probs), key=lambda x: -x[1])
    if top_k == 1:
        return [ranked[0]]
    return [(l, float(p)) for l, p in ranked[:top_k] if p >= threshold]


def classify_archetype(image: Image.Image, model_name: str) -> tuple[str, float]:
    label, conf = _classify(image, ARCHETYPE_PROMPTS, model_name)[0]
    return label, float(conf)


def classify_gaze(image: Image.Image, model_name: str, has_face: bool = True) -> tuple[str, float]:
    """CLIP gaze — not gated on OpenCV face detection (anime faces are often missed)."""
    label, conf = _classify(image, GAZE_PROMPTS, model_name)[0]
    if not has_face and label == "direct_gaze":
        # Prefer distance/away labels when no photorealistic face detected
        ranked = _classify(image, GAZE_PROMPTS, model_name, top_k=len(GAZE_PROMPTS))
        for lbl, c in ranked:
            if lbl != "direct_gaze":
                return lbl, float(c)
    return label, float(conf)


def classify_expression(image: Image.Image, model_name: str) -> tuple[str, float]:
    label, conf = _classify(image, EXPRESSION_PROMPTS, model_name)[0]
    return label, float(conf)


def classify_symbolism(
    image: Image.Image, model_name: str, threshold: float = 0.12
) -> list[str]:
    hits = _classify(image, SYMBOLISM_PROMPTS, model_name, top_k=len(SYMBOLISM_PROMPTS))
    return [label for label, conf in hits if conf >= threshold]


def classify_relationship(image: Image.Image, model_name: str) -> tuple[str, float]:
    label, conf = _classify(image, RELATIONSHIP_PROMPTS, model_name)[0]
    return label, float(conf)


def anime_style_score(image: Image.Image, model_name: str) -> float:
    model = _load_clip(model_name)
    img_emb = model.encode([image], normalize_embeddings=True)[0]
    anime_emb = model.encode(
        [ANIME_STYLE_PROMPTS["anime"]], normalize_embeddings=True
    )[0]
    real_emb = model.encode(
        [ANIME_STYLE_PROMPTS["realistic"]], normalize_embeddings=True
    )[0]
    anime_s = float(anime_emb @ img_emb)
    real_s = float(real_emb @ img_emb)
    # Normalize to 0-1-ish
    return max(0.0, min(1.0, (anime_s - real_s + 1) / 2))

#!/usr/bin/env python3
"""
Advanced Visual Analyzer — character, gaze, emotion, composition, symbolism.

Architecture: collector -> analyzer -> synthesizer -> report
Does NOT modify the existing step-5 visual_analysis.py pipeline.

Usage:
  python -m channel_analyzer.advanced_visual_analyzer
  python -m channel_analyzer.advanced_visual_analyzer --video-id FFUYW3587s0
  python -m channel_analyzer.advanced_visual_analyzer --llm-synthesis
"""

from __future__ import annotations

import argparse
import logging
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import pandas as pd
from PIL import Image
from tqdm import tqdm

from channel_analyzer.advanced_visual.clip_classifier import (
    anime_style_score,
    classify_archetype,
    classify_expression,
    classify_gaze,
    classify_relationship,
    classify_symbolism,
)
from channel_analyzer.advanced_visual.collector import (
    collect_video_frames,
    iter_analysis_sources,
    save_frame_cache,
)
from channel_analyzer.advanced_visual.composition import (
    analyze_composition,
    detect_faces,
    infer_relationship_heuristic,
)
from channel_analyzer.advanced_visual.llm_synth import synthesize_insights
from channel_analyzer.advanced_visual.models import FrameAnalysis, VideoVisualProfile
from channel_analyzer.config import Config
from channel_analyzer.utils import read_csv, setup_logging, write_markdown

logger = logging.getLogger(__name__)


def _analyze_frame(
    frame_bgr: np.ndarray,
    video_id: str,
    frame_path: str,
    timestamp: float,
    clip_model: str,
) -> FrameAnalysis:
    rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    pil = Image.fromarray(rgb)
    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    faces = detect_faces(gray)
    face_count = len(faces)

    comp, comp_conf, neg_pct, scale_pct = analyze_composition(frame_bgr, faces)
    rel_h, rel_h_conf = infer_relationship_heuristic(faces, frame_bgr.shape)

    archetype, arch_conf = classify_archetype(pil, clip_model)
    gaze, gaze_conf = classify_gaze(pil, clip_model, has_face=face_count > 0)
    expression, expr_conf = classify_expression(pil, clip_model)
    symbolism = classify_symbolism(pil, clip_model)
    rel_clip, rel_clip_conf = classify_relationship(pil, clip_model)
    anime_score = anime_style_score(pil, clip_model)

    # Blend relationship signals
    if rel_h_conf > rel_clip_conf:
        relationship, rel_conf = rel_h, rel_h_conf
    else:
        relationship, rel_conf = rel_clip, rel_clip_conf

    return FrameAnalysis(
        video_id=video_id,
        frame_path=frame_path,
        timestamp_sec=timestamp,
        character_archetype=archetype,
        character_confidence=arch_conf,
        gaze=gaze,
        gaze_confidence=gaze_conf,
        expression=expression,
        expression_confidence=expr_conf,
        composition=comp,
        composition_confidence=comp_conf,
        negative_space_pct=neg_pct,
        subject_scale_pct=scale_pct,
        symbolism=symbolism,
        relationship=relationship,
        relationship_confidence=rel_conf,
        anime_style_score=anime_score,
        face_count=face_count,
    )


def _aggregate_video(
    frames: list[FrameAnalysis],
    meta: dict[str, Any],
) -> VideoVisualProfile:
    if not frames:
        return VideoVisualProfile(video_id=meta.get("video_id", ""))

    def _dominant(attr: str) -> str:
        vals = [getattr(f, attr) for f in frames]
        return Counter(vals).most_common(1)[0][0]

    sym_counter: Counter[str] = Counter()
    for f in frames:
        sym_counter.update(f.symbolism)

    arch_scores: dict[str, float] = defaultdict(float)
    expr_scores: dict[str, float] = defaultdict(float)
    for f in frames:
        arch_scores[f.character_archetype] += f.character_confidence
        expr_scores[f.expression] += f.expression_confidence

    return VideoVisualProfile(
        video_id=meta.get("video_id", frames[0].video_id),
        title=meta.get("title", ""),
        views=int(meta.get("views", 0)),
        views_per_day=float(meta.get("views_per_day", 0)),
        rank=int(meta.get("rank", 0)),
        frames_analyzed=len(frames),
        dominant_archetype=_dominant("character_archetype"),
        dominant_gaze=_dominant("gaze"),
        dominant_expression=_dominant("expression"),
        dominant_composition=_dominant("composition"),
        dominant_relationship=_dominant("relationship"),
        avg_negative_space_pct=float(np.mean([f.negative_space_pct for f in frames])),
        avg_subject_scale_pct=float(np.mean([f.subject_scale_pct for f in frames])),
        avg_anime_style_score=float(np.mean([f.anime_style_score for f in frames])),
        symbolism_frequency=dict(sym_counter),
        archetype_scores=dict(arch_scores),
        expression_scores=dict(expr_scores),
    )


def _performance_correlations(
    profiles: list[VideoVisualProfile],
) -> dict[str, Any]:
    """Correlate visual patterns with views_per_day across analyzed videos."""
    if len(profiles) < 3:
        return {}

    df = pd.DataFrame([p.to_row() for p in profiles])
    df["views_per_day"] = [p.views_per_day for p in profiles]
    df["views"] = [p.views for p in profiles]

    median_vpd = df["views_per_day"].median()
    high = df[df["views_per_day"] >= median_vpd]
    low = df[df["views_per_day"] < median_vpd]

    def _rate(column: str, subset) -> Counter:
        return Counter(subset[column].tolist())

    insights: dict[str, Any] = {
        "high_performer_count": len(high),
        "low_performer_count": len(low),
        "median_views_per_day": float(median_vpd),
        "high_performer_archetypes": dict(_rate("dominant_archetype", high)),
        "low_performer_archetypes": dict(_rate("dominant_archetype", low)),
        "high_performer_expressions": dict(_rate("dominant_expression", high)),
        "high_performer_compositions": dict(_rate("dominant_composition", high)),
        "high_performer_gaze": dict(_rate("dominant_gaze", high)),
        "avg_anime_score_high": float(high["avg_anime_style_score"].mean())
        if len(high) else 0,
        "avg_anime_score_low": float(low["avg_anime_style_score"].mean())
        if len(low) else 0,
        "avg_negative_space_high": float(high["avg_negative_space_pct"].mean())
        if len(high) else 0,
        "avg_negative_space_low": float(low["avg_negative_space_pct"].mean())
        if len(low) else 0,
    }
    return insights


def _build_key_insights(
    profiles: list[VideoVisualProfile],
    frame_df: pd.DataFrame,
) -> str:
    """Produce human-readable performance-linked visual insights."""
    if len(profiles) < 4 or frame_df.empty:
        return "_Need at least 4 analyzed videos for performance-linked insights._"

    vpd = [p.views_per_day for p in profiles]
    median_vpd = float(np.median(vpd))
    high = [p for p in profiles if p.views_per_day >= median_vpd]
    n_high = len(high)
    if n_high == 0:
        return "_No high-performer split available._"

    high_ids = {p.video_id for p in high}
    high_frames = frame_df[frame_df["video_id"].isin(high_ids)]

    lines: list[str] = []

    def _rate_in_high(attr: str, value: str, on: str = "videos") -> float:
        if on == "videos":
            return 100 * sum(1 for p in high if getattr(p, attr) == value) / n_high
        mask = high_frames[attr] == value
        return 100 * mask.sum() / max(len(high_frames), 1)

    # Single-dimension insights (>= 50% threshold)
    for attr, label in [
        ("dominant_archetype", "character archetype"),
        ("dominant_gaze", "gaze"),
        ("dominant_expression", "emotional expression"),
        ("dominant_composition", "composition"),
        ("dominant_relationship", "relationship"),
    ]:
        counts: Counter[str] = Counter(getattr(p, attr) for p in high)
        top_val, top_n = counts.most_common(1)[0]
        pct = 100 * top_n / n_high
        if pct >= 50:
            readable = top_val.replace("_", " ")
            lines.append(
                f"- **{pct:.0f}%** of high-performing videos use a dominant "
                f"**{readable}** {label}."
            )

    # Anime + negative space
    anime_high = np.mean([p.avg_anime_style_score for p in high])
    neg_high = np.mean([p.avg_negative_space_pct for p in high])
    if anime_high >= 0.55:
        lines.append(
            f"- High performers average **{anime_high:.0%} anime-style score** "
            f"(CLIP anime vs realistic)."
        )
    if neg_high >= 45:
        lines.append(
            f"- High performers average **{neg_high:.0f}% negative space**, "
            "suggesting tiny-human / large-world or airy compositions."
        )

    # Symbolism in high-performer frames
    sym_counter: Counter[str] = Counter()
    for syms in high_frames["symbolism"].dropna():
        for s in str(syms).split("|"):
            if s:
                sym_counter[s] += 1
    if sym_counter:
        top_sym, sym_n = sym_counter.most_common(1)[0]
        sym_pct = 100 * sym_n / max(len(high_frames), 1)
        if sym_pct >= 25:
            lines.append(
                f"- **{sym_pct:.0f}%** of high-performer frames contain **{top_sym}** symbolism."
            )

    # Composite signature (the insight format the user asked for)
    signature_count = sum(
        1
        for p in high
        if p.dominant_archetype in ("solitary_female", "solitary_male")
        and p.dominant_gaze in ("looking_away", "side_profile", "back_profile")
        and p.dominant_expression in (
            "hopeful",
            "peaceful_sadness",
            "resilience",
            "longing",
            "reflective",
        )
        and p.avg_negative_space_pct >= 40
    )
    sig_pct = 100 * signature_count / n_high
    if sig_pct >= 40:
        lines.insert(
            0,
            f"- **{sig_pct:.0f}%** of high-performing videos contain a **solitary character** "
            "with **averted gaze** (away, side, or back profile), **hopeful-melancholy expression** "
            "(hopeful, longing, peaceful sadness, resilience, or reflective), and "
            f"**high negative space** (avg ≥ 40%)."
        )

    # Sunset + solitary combo
    sunset_frames = high_frames[
        high_frames["symbolism"].str.contains("sunset", na=False)
    ]
    if len(sunset_frames) >= 5:
        sunset_pct = 100 * len(sunset_frames) / max(len(high_frames), 1)
        solitary_sunset = sum(
            1
            for p in high
            if p.dominant_archetype.startswith("solitary")
            and "sunset" in p.symbolism_frequency
        )
        ss_pct = 100 * solitary_sunset / n_high
        if ss_pct >= 30:
            lines.append(
                f"- **{ss_pct:.0f}%** of high performers pair **solitary characters** "
                f"with **sunset** symbolism ({sunset_pct:.0f}% of their frames show sunset)."
            )

    if not lines:
        return "_No dominant patterns above threshold in high performers yet._"
    return "\n".join(lines)


def _load_advanced_visual_settings(config: Config) -> dict[str, Any]:
    """Read advanced_visual block from config.yaml with defaults."""
    import yaml

    defaults = {
        "frame_interval_seconds": 1.5,
        "max_frames_per_video": 10,
        "clip_model": "clip-ViT-B-32",
        "symbolism_threshold": 0.12,
        "llm_synthesis": False,
        "llm_provider": "anthropic",
    }
    config_path = getattr(config, "_config_path", None)
    if config_path is None:
        from channel_analyzer.config import DEFAULT_CONFIG_PATH

        config_path = DEFAULT_CONFIG_PATH
    if Path(config_path).exists():
        with open(config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        av = data.get("advanced_visual", {})
        defaults.update({k: v for k, v in av.items() if v is not None})
    return defaults


def _build_report_sections(
    profiles: list[VideoVisualProfile],
    frame_df: pd.DataFrame,
    correlations: dict[str, Any],
    llm_text: str | None,
) -> dict[str, str]:
    n_videos = len(profiles)
    n_frames = len(frame_df)

    # Channel-wide aggregates
    arch_agg = Counter(frame_df["character_archetype"].tolist())
    gaze_agg = Counter(frame_df["gaze"].tolist())
    expr_agg = Counter(frame_df["expression"].tolist())
    comp_agg = Counter(frame_df["composition"].tolist())
    rel_agg = Counter(frame_df["relationship"].tolist())
    sym_agg: Counter[str] = Counter()
    for syms in frame_df["symbolism"].dropna():
        for s in str(syms).split("|"):
            if s:
                sym_agg[s] += 1

    avg_anime = frame_df["anime_style_score"].mean()
    avg_neg = frame_df["negative_space_pct"].mean()

    overview = (
        f"**Videos analyzed:** {n_videos}\n"
        f"**Frames analyzed:** {n_frames}\n"
        f"**Average anime style score:** {avg_anime:.2f}\n"
        f"**Average negative space:** {avg_neg:.1f}%\n\n"
        "This layer answers *what people are feeling visually* — not just pixel statistics."
    )

    archetypes = "\n".join(
        f"- **{k}**: {v} frames ({100*v/n_frames:.0f}%)"
        for k, v in arch_agg.most_common()
    )

    gaze = "\n".join(
        f"- **{k}**: {v} frames ({100*v/n_frames:.0f}%)"
        for k, v in gaze_agg.most_common()
    )

    expressions = "\n".join(
        f"- **{k}**: {v} frames ({100*v/n_frames:.0f}%)"
        for k, v in expr_agg.most_common()
    )

    compositions = "\n".join(
        f"- **{k}**: {v} frames ({100*v/n_frames:.0f}%)"
        for k, v in comp_agg.most_common()
    )

    symbolism = "\n".join(
        f"- **{k}**: {v} frames ({100*v/n_frames:.0f}%)"
        for k, v in sym_agg.most_common(12)
    )

    relationships = "\n".join(
        f"- **{k}**: {v} frames ({100*v/n_frames:.0f}%)"
        for k, v in rel_agg.most_common()
    )

    perf = "_Insufficient videos for correlation._"
    if correlations:
        hp = correlations.get("high_performer_count", 0)
        lp = correlations.get("low_performer_count", 0)
        perf = (
            f"Split at median views/day ({correlations.get('median_views_per_day', 0):,.0f}).\n\n"
            f"**High performers ({hp} videos):**\n"
            f"- Archetypes: {correlations.get('high_performer_archetypes', {})}\n"
            f"- Expressions: {correlations.get('high_performer_expressions', {})}\n"
            f"- Compositions: {correlations.get('high_performer_compositions', {})}\n"
            f"- Gaze: {correlations.get('high_performer_gaze', {})}\n"
            f"- Avg anime score: {correlations.get('avg_anime_score_high', 0):.2f}\n"
            f"- Avg negative space: {correlations.get('avg_negative_space_high', 0):.1f}%\n\n"
            f"**Lower performers ({lp} videos):**\n"
            f"- Avg anime score: {correlations.get('avg_anime_score_low', 0):.2f}\n"
            f"- Avg negative space: {correlations.get('avg_negative_space_low', 0):.1f}%"
        )

    per_video = "\n".join(
        f"### {p.video_id} (rank {p.rank}, {p.views_per_day:,.0f} views/day)\n"
        f"- Archetype: **{p.dominant_archetype}** | Gaze: **{p.dominant_gaze}** | "
        f"Expression: **{p.dominant_expression}**\n"
        f"- Composition: **{p.dominant_composition}** | Relationship: **{p.dominant_relationship}**\n"
        f"- Anime score: {p.avg_anime_style_score:.2f} | Negative space: {p.avg_negative_space_pct:.1f}%\n"
        f"- Top symbols: {', '.join(k for k, _ in sorted(p.symbolism_frequency.items(), key=lambda x: -x[1])[:4]) or 'none'}\n"
        for p in sorted(profiles, key=lambda x: x.rank or 999)
    )

    llm_section = llm_text or "_LLM synthesis skipped (no API keys or --llm-synthesis not set)._"

    key_insights = _build_key_insights(profiles, frame_df)

    return {
        "Overview": overview,
        "Key Insights": key_insights,
        "Character Archetypes": archetypes,
        "Gaze Analysis": gaze,
        "Emotional Expression": expressions,
        "Composition Analysis": compositions,
        "Symbolism": symbolism,
        "Relationship Analysis": relationships,
        "Performance Correlations": perf,
        "Per-Video Profiles": per_video,
        "LLM Synthesis": llm_section,
    }


def run_advanced_visual_analysis(
    config: Config | None = None,
    video_ids: list[str] | None = None,
    frame_interval: float | None = None,
    max_frames_per_video: int | None = None,
    clip_model: str | None = None,
    use_llm_synthesis: bool | None = None,
    llm_provider: str | None = None,
) -> dict[str, Path]:
    """
    Run full advanced visual analysis pipeline.

    Returns paths to output artifacts.
    """
    config = config or Config.from_yaml()
    config.ensure_dirs()
    av_settings = _load_advanced_visual_settings(config)

    frame_interval = frame_interval or av_settings["frame_interval_seconds"]
    max_frames_per_video = max_frames_per_video or av_settings["max_frames_per_video"]
    clip_model = clip_model or av_settings["clip_model"]
    use_llm_synthesis = (
        use_llm_synthesis
        if use_llm_synthesis is not None
        else bool(av_settings.get("llm_synthesis", False))
    )
    llm_provider = llm_provider or av_settings.get("llm_provider", "anthropic")

    cache_dir = config.artifacts_dir / "advanced_visual_cache"
    frame_cache_dir = cache_dir / "frames"
    llm_cache_dir = config.llm_cache_dir / "advanced_visual"

    top_df = read_csv(config.top_videos_csv)
    meta_by_id: dict[str, dict[str, Any]] = {}
    if not top_df.empty and "video_id" in top_df.columns:
        for _, row in top_df.iterrows():
            meta_by_id[str(row["video_id"])] = row.to_dict()

    sources = iter_analysis_sources(config, video_ids)
    if not sources:
        raise FileNotFoundError(
            f"No videos in {config.downloads_dir}. Run pipeline step 3 first."
        )

    all_frames: list[FrameAnalysis] = []
    sample_images: list[Image.Image] = []

    for video_id, path, source_type in tqdm(sources, desc="Advanced visual"):
        meta = meta_by_id.get(video_id, {"video_id": video_id})
        if source_type == "video":
            raw_frames = collect_video_frames(
                path, interval_sec=frame_interval, max_frames=max_frames_per_video
            )
        else:
            raw_frames = []

        for i, (frame, ts) in enumerate(raw_frames):
            fpath = save_frame_cache(frame_cache_dir, video_id, i, frame)
            analysis = _analyze_frame(
                frame, video_id, str(fpath), ts, clip_model
            )
            all_frames.append(analysis)
            if len(sample_images) < 12:
                sample_images.append(
                    Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                )

    frame_df = pd.DataFrame([f.to_row() for f in all_frames])
    frames_csv = config.data_dir / "advanced_visual_frames.csv"
    frame_df.to_csv(frames_csv, index=False)
    logger.info("Wrote %d frame rows to %s", len(frame_df), frames_csv)

    # Aggregate per video
    by_video: dict[str, list[FrameAnalysis]] = defaultdict(list)
    for f in all_frames:
        by_video[f.video_id].append(f)

    profiles: list[VideoVisualProfile] = []
    for vid, frames in by_video.items():
        meta = meta_by_id.get(vid, {"video_id": vid})
        profiles.append(_aggregate_video(frames, meta))

    profiles_df = pd.DataFrame([p.to_row() for p in profiles])
    videos_csv = config.data_dir / "advanced_visual_videos.csv"
    profiles_df.to_csv(videos_csv, index=False)

    correlations = _performance_correlations(profiles)

    llm_text = None
    if use_llm_synthesis:
        agg_stats = {
            "frame_counts": {
                "archetype": dict(Counter(frame_df["character_archetype"])),
                "gaze": dict(Counter(frame_df["gaze"])),
                "expression": dict(Counter(frame_df["expression"])),
                "composition": dict(Counter(frame_df["composition"])),
            },
            "correlations": correlations,
            "avg_anime_style": float(frame_df["anime_style_score"].mean()),
            "avg_negative_space": float(frame_df["negative_space_pct"].mean()),
        }
        llm_text = synthesize_insights(
            llm_cache_dir, agg_stats, sample_images, provider=llm_provider
        )

    report_path = config.reports_dir / "advanced_visual_analysis.md"
    sections = _build_report_sections(profiles, frame_df, correlations, llm_text)
    write_markdown(report_path, "Advanced Visual Analysis", sections)

    return {
        "advanced_visual_frames.csv": frames_csv,
        "advanced_visual_videos.csv": videos_csv,
        "advanced_visual_analysis.md": report_path,
    }


def main(argv: list[str] | None = None) -> int:
    setup_logging()
    parser = argparse.ArgumentParser(description="Advanced Visual Analyzer")
    parser.add_argument("--config", type=str, help="Path to config.yaml")
    parser.add_argument("--video-id", action="append", dest="video_ids")
    parser.add_argument("--frame-interval", type=float, default=1.5)
    parser.add_argument("--max-frames", type=int, default=10)
    parser.add_argument("--clip-model", default="clip-ViT-B-32")
    parser.add_argument(
        "--llm-synthesis",
        action="store_true",
        help="Run optional LLM synthesis on preprocessed thumbnails (cached)",
    )
    parser.add_argument(
        "--llm-provider",
        choices=["anthropic", "openai"],
        default="anthropic",
    )
    args = parser.parse_args(argv)

    config_path = Path(args.config) if args.config else None
    config = Config.from_yaml(config_path)

    try:
        results = run_advanced_visual_analysis(
            config=config,
            video_ids=args.video_ids,
            frame_interval=args.frame_interval,
            max_frames_per_video=args.max_frames,
            clip_model=args.clip_model,
            use_llm_synthesis=args.llm_synthesis or None,
            llm_provider=args.llm_provider,
        )
        print("\nAdvanced visual analysis complete:")
        for name, path in results.items():
            print(f"  {name}: {path}")
        return 0
    except Exception as exc:
        logger.error("Advanced visual analysis failed: %s", exc)
        raise


if __name__ == "__main__":
    raise SystemExit(main())

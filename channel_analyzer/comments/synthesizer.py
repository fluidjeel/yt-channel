"""Synthesize audience psychology reports from comment analysis."""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Any

from channel_analyzer.comments.models import AnalyzedComment, CommentCluster
from channel_analyzer.utils import write_markdown

logger = logging.getLogger(__name__)


def _fmt_counter(counter: dict[str, int], total: int) -> str:
    if not counter or total == 0:
        return "_None detected._"
    lines = []
    for k, v in counter.items():
        pct = 100 * v / total
        lines.append(f"- **{k.replace('_', ' ')}**: {v} ({pct:.0f}%)")
    return "\n".join(lines)


def _cluster_section(clusters: list[CommentCluster]) -> str:
    if not clusters:
        return "_No clusters._"
    lines = []
    for cl in sorted(clusters, key=lambda c: -c.comment_count)[:12]:
        lines.append(
            f"### Cluster {cl.cluster_id}: {cl.theme.replace('_', ' ')} "
            f"(confidence {cl.confidence:.2f})\n"
            f"- **Comments:** {cl.comment_count} across {cl.video_count} videos\n"
            f"- **Emotion:** {cl.emotional_state.replace('_', ' ')} | "
            f"**Life situation:** {cl.life_situation.replace('_', ' ')}\n"
            f"- **Save signals:** {cl.save_signal_pct:.0f}% | "
            f"**Share signals:** {cl.share_signal_pct:.0f}%\n"
            f"- **Avg video views/day:** {cl.avg_video_views_per_day:,.0f}\n"
            f"- **Top phrases:** {', '.join(cl.top_phrases[:4]) or 'none'}\n"
            f"- **Evidence:**\n"
            + "\n".join(f'  - "{ex}"' for ex in cl.example_comments[:2])
        )
    return "\n\n".join(lines)


def build_audience_psychology_sections(
    analyzed: list[AnalyzedComment],
    clusters: list[CommentCluster],
    stats: dict[str, Any],
    channel: str = "",
) -> dict[str, str]:
    non_spam = [a for a in analyzed if not a.is_spam]
    n = len(non_spam)
    total = len(analyzed)

    theme_dist = {}
    emotion_dist = {}
    life_dist = {}
    for a in non_spam:
        theme_dist[a.theme] = theme_dist.get(a.theme, 0) + 1
        emotion_dist[a.emotional_state] = emotion_dist.get(a.emotional_state, 0) + 1
        life_dist[a.life_situation] = life_dist.get(a.life_situation, 0) + 1

    save_comments = [a for a in non_spam if a.save_signal]
    share_comments = [a for a in non_spam if a.share_signal]
    high_pain = sorted(non_spam, key=lambda a: -a.pain_point_score)[:8]

    overview = (
        f"**Channel:** {channel or 'unknown'}\n"
        f"**Comments collected:** {stats.get('total_raw', total)}\n"
        f"**After spam filter:** {stats.get('analyzed_count', n)} "
        f"({stats.get('spam_count', 0)} spam removed)\n"
        f"**Clusters:** {stats.get('cluster_count', len(clusters))}\n"
        f"**Save-intent signals:** {stats.get('save_signal_count', len(save_comments))}\n"
        f"**Share-intent signals:** {stats.get('share_signal_count', len(share_comments))}\n\n"
        "This report answers *why people emotionally connect* — not just what they watched."
    )

    why_save = (
        f"**{len(save_comments)}** comments ({100*len(save_comments)/max(n,1):.1f}%) "
        "show save/bookmark intent.\n\n"
        + (
            "\n".join(
                f'- "{c.text[:180]}" _(video rank {c.video_rank}, {c.theme})_'
                for c in sorted(save_comments, key=lambda x: -x.like_count)[:8]
            )
            if save_comments
            else "_No explicit save phrases detected; validation/relatability themes may still drive saves._"
        )
    )

    why_share = (
        f"**{len(share_comments)}** comments ({100*len(share_comments)/max(n,1):.1f}%) "
        "show share intent.\n\n"
        + (
            "\n".join(
                f'- "{c.text[:180]}" _(video rank {c.video_rank})_'
                for c in sorted(share_comments, key=lambda x: -x.like_count)[:8]
            )
            if share_comments
            else "_Few explicit share phrases; wisdom/heartbreak clusters may still drive sharing._"
        )
    )

    pain_points = "\n".join(
        f"- **{a.life_situation.replace('_', ' ')}** / "
        f"**{a.emotional_state.replace('_', ' ')}** "
        f"(pain score {a.pain_point_score:.2f}): \"{a.text[:150]}...\""
        for a in high_pain
    )

    repeated = stats.get("repeated_phrases", [])
    phrases_section = (
        "\n".join(
            f"- **\"{p['phrase']}\"** — {p['comment_count']} comments across "
            f"{p['video_count']} videos"
            for p in repeated[:15]
        )
        if repeated
        else "_No cross-video repeated phrases above threshold._"
    )

    perf = stats.get("performance_correlation", {})
    perf_section = "_Insufficient data for performance correlation._"
    if perf:
        perf_section = (
            f"Split at median views/day ({perf.get('median_views_per_day', 0):,.0f}).\n\n"
            f"**High-performer comment themes:**\n"
            f"{_fmt_counter(perf.get('high_performer_themes', {}), n)}\n\n"
            f"**High-performer emotions:**\n"
            f"{_fmt_counter(perf.get('high_performer_emotions', {}), n)}\n\n"
            f"**Clusters over-indexed on high performers:**\n"
            + "\n".join(
                f"- Cluster {c['cluster_id']} ({c['theme']}): "
                f"{c['high_performer_pct']:.0f}% of high-performer comments "
                f"(confidence {c['confidence']:.2f})"
                for c in perf.get("top_clusters_on_high_performers", [])[:6]
            )
        )

    key_insights = _build_key_insights(non_spam, clusters, stats)

    return {
        "Overview": overview,
        "Key Insights": key_insights,
        "Why Viewers Save": why_save,
        "Why Viewers Share": why_share,
        "Emotional Triggers": _fmt_counter(emotion_dist, n),
        "Life Situations": _fmt_counter(life_dist, n),
        "Recurring Pain Points": pain_points or "_None above threshold._",
        "Repeated Phrases": phrases_section,
        "Comment Clusters": _cluster_section(clusters),
        "Performance Correlation": perf_section,
    }


def build_comment_patterns_sections(
    analyzed: list[AnalyzedComment],
    clusters: list[CommentCluster],
    stats: dict[str, Any],
) -> dict[str, str]:
    non_spam = [a for a in analyzed if not a.is_spam]
    n = len(non_spam)

    theme_dist: dict[str, int] = {}
    for a in non_spam:
        theme_dist[a.theme] = theme_dist.get(a.theme, 0) + 1

    by_video: dict[str, list[AnalyzedComment]] = {}
    for a in non_spam:
        by_video.setdefault(a.video_id, []).append(a)

    per_video = []
    for vid, comments in sorted(
        by_video.items(),
        key=lambda x: -(x[1][0].video_views_per_day if x[1] else 0),
    )[:10]:
        themes = {}
        for c in comments:
            themes[c.theme] = themes.get(c.theme, 0) + 1
        top_theme = max(themes, key=themes.get) if themes else "unknown"
        per_video.append(
            f"### {vid} (rank {comments[0].video_rank}, "
            f"{comments[0].video_views_per_day:,.0f} views/day)\n"
            f"- Dominant theme: **{top_theme.replace('_', ' ')}** "
            f"({themes.get(top_theme, 0)}/{len(comments)} comments)\n"
            f"- Top comment: \"{max(comments, key=lambda c: c.like_count).text[:120]}...\""
        )

    return {
        "Theme Distribution": _fmt_counter(theme_dist, n),
        "Top Videos by Comment Theme": "\n\n".join(per_video) or "_No data._",
        "Cluster Evidence": _cluster_section(clusters),
        "Cross-Video Phrases": "\n".join(
            f"- \"{p['phrase']}\" ({p['video_count']} videos, {p['comment_count']} comments)"
            for p in stats.get("repeated_phrases", [])[:20]
        )
        or "_None._",
    }


def _build_key_insights(
    non_spam: list[AnalyzedComment],
    clusters: list[CommentCluster],
    stats: dict[str, Any],
) -> str:
    if not non_spam:
        return "_No comments to analyze._"

    n = len(non_spam)
    lines: list[str] = []

    theme_counts: dict[str, int] = {}
    for a in non_spam:
        theme_counts[a.theme] = theme_counts.get(a.theme, 0) + 1
    top_theme, top_n = max(theme_counts.items(), key=lambda x: x[1])
    if 100 * top_n / n >= 15:
        lines.append(
            f"- **{100*top_n/n:.0f}%** of comments express **{top_theme.replace('_', ' ')}** — "
            "the primary audience connection point."
        )

    emotion_counts: dict[str, int] = {}
    for a in non_spam:
        emotion_counts[a.emotional_state] = emotion_counts.get(a.emotional_state, 0) + 1
    top_emo, emo_n = max(emotion_counts.items(), key=lambda x: x[1])
    if 100 * emo_n / n >= 12:
        lines.append(
            f"- Dominant emotional state: **{top_emo.replace('_', ' ')}** "
            f"({100*emo_n/n:.0f}% of comments)."
        )

    save_pct = 100 * stats.get("save_signal_count", 0) / n
    share_pct = 100 * stats.get("share_signal_count", 0) / n
    if save_pct >= 1:
        lines.append(
            f"- **{save_pct:.1f}%** of comments show explicit save/bookmark language — "
            "content functions as emotional reference material."
        )
    if share_pct >= 0.5:
        lines.append(
            f"- **{share_pct:.1f}%** show share intent — viewers use this as "
            "social emotional currency."
        )

    perf = stats.get("performance_correlation", {})
    top_clusters = perf.get("top_clusters_on_high_performers", [])
    if top_clusters:
        tc = top_clusters[0]
        lines.append(
            f"- High performers over-index on cluster **{tc['cluster_id']}** "
            f"({tc['theme'].replace('_', ' ')}, {tc['high_performer_pct']:.0f}% of "
            f"high-performer comments, confidence {tc['confidence']:.2f})."
        )

    repeated = stats.get("repeated_phrases", [])
    if repeated:
        p = repeated[0]
        lines.append(
            f"- Most repeated cross-video phrase: **\"{p['phrase']}\"** "
            f"({p['video_count']} videos) — potential audience vocabulary."
        )

    if not lines:
        return "_Patterns emerging; collect more comments for stronger signals._"
    return "\n".join(lines)


def synthesize_with_llm(
    cache_dir: Path,
    sections_text: str,
    stats: dict[str, Any],
    provider: str = "anthropic",
) -> str | None:
    """Optional Claude/GPT synthesis of audience psychology."""
    from channel_analyzer.advanced_visual.llm_synth import load_api_keys

    keys = load_api_keys()
    if provider == "anthropic" and not keys["anthropic"]:
        provider = "openai"
    if provider == "openai" and not keys["openai"]:
        if keys["anthropic"]:
            provider = "anthropic"
        else:
            return None

    payload = json.dumps(stats, default=str)[:5000]
    cache_key = hashlib.sha256((payload + sections_text[:2000]).encode()).hexdigest()[:16]
    cache_path = cache_dir / f"audience_psychology_{cache_key}.md"
    if cache_path.exists():
        return cache_path.read_text(encoding="utf-8")

    prompt = (
        "You are analyzing YouTube Shorts comment psychology for a poetry/self-worth channel.\n"
        "Given aggregate stats and patterns below, synthesize:\n"
        "1. The hidden niche hypothesis (self-worth/healing vs love)\n"
        "2. Why viewers save and share\n"
        "3. Core pain points and emotional triggers\n"
        "4. What the audience is really seeking\n"
        "5. Content recommendations based on comment evidence\n\n"
        "Cite percentages from the data. Do not invent statistics.\n\n"
        f"STATS:\n{payload}\n\n"
        f"PATTERNS:\n{sections_text[:6000]}"
    )

    try:
        import httpx

        if provider == "anthropic":
            resp = httpx.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": keys["anthropic"],
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 2500,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=120,
            )
            resp.raise_for_status()
            text = resp.json()["content"][0]["text"]
        else:
            resp = httpx.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {keys['openai']}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-4o-mini",
                    "max_tokens": 2500,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=120,
            )
            resp.raise_for_status()
            text = resp.json()["choices"][0]["message"]["content"]

        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(text, encoding="utf-8")
        return text
    except Exception as exc:
        logger.warning("LLM synthesis failed: %s", exc)
        return None


def write_reports(
    reports_dir: Path,
    analyzed: list[AnalyzedComment],
    clusters: list[CommentCluster],
    stats: dict[str, Any],
    channel: str = "",
    llm_text: str | None = None,
) -> dict[str, Path]:
    psych_sections = build_audience_psychology_sections(analyzed, clusters, stats, channel)
    if llm_text:
        psych_sections["LLM Synthesis"] = llm_text

    patterns_sections = build_comment_patterns_sections(analyzed, clusters, stats)

    psych_path = reports_dir / "audience_psychology.md"
    patterns_path = reports_dir / "comment_patterns.md"
    write_markdown(psych_path, "Audience Psychology", psych_sections)
    write_markdown(patterns_path, "Comment Patterns", patterns_sections)

    return {
        "audience_psychology.md": psych_path,
        "comment_patterns.md": patterns_path,
    }

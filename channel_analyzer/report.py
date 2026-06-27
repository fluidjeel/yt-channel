"""STEP 10 — Final Reverse Engineering Report: channel playbook."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from channel_analyzer.config import Config
from channel_analyzer.utils import read_csv, write_markdown

logger = logging.getLogger(__name__)


def _read_md_section(path: Path, max_chars: int = 2000) -> str:
    if not path.exists():
        return "_Not yet generated._"
    text = path.read_text(encoding="utf-8")
    return text[:max_chars] + ("..." if len(text) > max_chars else "")


def _visual_style_bible(config: Config) -> str:
    path = config.visual_analysis_md
    if not path.exists():
        return "Run visual analysis to populate."
    text = path.read_text(encoding="utf-8")
    return (
        "Derived from frame-by-frame analysis across top videos.\n\n"
        + text.split("## Summary", 1)[-1][:2500]
    )


def _emotional_style_bible(config: Config) -> str:
    path = config.emotion_clusters_md
    scores = config.emotion_scores_csv
    parts = []
    if path.exists():
        parts.append(path.read_text(encoding="utf-8")[:2000])
    if scores.exists():
        df = pd.read_csv(scores)
        dim_cols = [c for c in df.columns if c not in ("video_id", "cluster", "title")]
        if dim_cols:
            avg = df[dim_cols].mean().sort_values(ascending=False)
            parts.append(
                "\n\n**Dominant emotions (channel average):**\n"
                + "\n".join(f"- {d}: {v:.3f}" for d, v in avg.head(5).items())
            )
    return "\n".join(parts) or "Run emotion analysis to populate."


def _script_style_bible(config: Config) -> str:
    audio = config.audio_analysis_md
    narrative = config.narrative_patterns_md
    quotes = config.quote_patterns_md
    sections = []
    for label, p in [
        ("Speech Patterns", audio),
        ("Narrative Structure", narrative),
        ("Signature Quotes", quotes),
    ]:
        if p.exists():
            sections.append(f"### {label}\n{p.read_text(encoding='utf-8')[:1200]}")
    return "\n\n".join(sections) or "Run audio and narrative analysis to populate."


def _audio_style_bible(config: Config) -> str:
    path = config.music_profile_md
    return path.read_text(encoding="utf-8")[:2500] if path.exists() else "Run music analysis to populate."


def _content_calendar(config: Config) -> str:
    df = read_csv(config.top_videos_csv)
    if df.empty:
        return "Insufficient data."
    top = df.head(10)
    emotion_df = read_csv(config.emotion_scores_csv)

    # Best performing themes
    themes = []
    if not emotion_df.empty and "video_id" in emotion_df.columns:
        dim_cols = [c for c in emotion_df.columns if c not in ("video_id", "cluster", "title")]
        for _, row in top.iterrows():
            match = emotion_df[emotion_df["video_id"].astype(str) == str(row["video_id"])]
            if not match.empty and dim_cols:
                top_dim = match[dim_cols].iloc[0].idxmax()
                themes.append(top_dim)

    from collections import Counter

    theme_counts = Counter(themes)
    dominant = theme_counts.most_common(3)

    lines = [
        "### Recommended Posting Strategy",
        "- **Frequency:** 4-7 Shorts per week (based on top performer velocity)",
        "- **Optimal length:** Match median duration of top 20 videos",
        "",
        "### Weekly Theme Rotation",
    ]
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    for i, day in enumerate(days):
        theme = dominant[i % len(dominant)][0] if dominant else "hope"
        lines.append(f"- **{day}:** {theme.title()}-themed content")

    if not top.empty and "upload_date" in top.columns:
        dates = pd.to_datetime(top["upload_date"], errors="coerce").dropna()
        if len(dates) > 2:
            gaps = dates.sort_values().diff().dt.days.dropna()
            if len(gaps) > 0:
                lines.append(f"\n- **Observed upload cadence:** ~{gaps.median():.0f} days between hits")

    return "\n".join(lines)


def _content_gaps(config: Config) -> str:
    emotion_df = read_csv(config.emotion_scores_csv)
    if emotion_df.empty:
        return "Run emotion analysis to identify gaps."

    dim_cols = [c for c in emotion_df.columns if c not in ("video_id", "cluster", "title")]
    avg = emotion_df[dim_cols].mean()
    low = avg.sort_values().head(3)
    high = avg.sort_values(ascending=False).head(3)

    return (
        "### Underexplored Emotional Territories\n"
        + "\n".join(f"- **{d}** (avg score {v:.3f}) — opportunity for differentiated content" for d, v in low.items())
        + "\n\n### Overused Themes (saturation risk)\n"
        + "\n".join(f"- **{d}** (avg score {v:.3f}) — consider fresh angles" for d, v in high.items())
        + "\n\n### Structural Gaps\n"
        "- Test videos with longer reflection segments if current winners skew hook-heavy\n"
        "- Experiment with question-hooks if statement-hooks dominate\n"
        "- Try environment diversity (ocean, forest) if urban/indoor scenes saturate"
    )


def _viral_patterns(config: Config) -> str:
    df = read_csv(config.top_videos_csv)
    if df.empty:
        return "No performance data."

    top20 = df[df["top_20"] == True]  # noqa: E712
    if top20.empty:
        top20 = df.head(20)

    patterns = [
        f"- **View velocity:** Top videos average **{top20['views_per_day'].mean():,.0f}** views/day",
        f"- **Engagement:** Avg engagement proxy **{top20['engagement_proxy'].mean():.4f}**",
    ]

    if "duration_seconds" in top20.columns:
        patterns.append(
            f"- **Duration sweet spot:** {top20['duration_seconds'].median():.0f}s median "
            f"(range {top20['duration_seconds'].min():.0f}-{top20['duration_seconds'].max():.0f}s)"
        )

    quote_df = read_csv(config.quote_database_csv)
    if not quote_df.empty:
        top_themes = quote_df["theme"].value_counts().head(3)
        patterns.append(
            "- **Viral quote themes:** "
            + ", ".join(f"{t} ({c})" for t, c in top_themes.items())
        )

    return "### Identified Viral Patterns\n\n" + "\n".join(patterns)


def _replication_framework(config: Config) -> str:
    return """### The 8-Step Replication Framework

1. **Pick an emotional pillar** — Choose from the channel's top 2 performing emotion clusters
2. **Select environment** — Match dominant visual settings (sky, portrait, etc.)
3. **Write the hook** — First 1-2 sentences using the channel's dominant hook style
4. **Build reflection** — Personal, vulnerable narrative (~30-40% of script)
5. **Deliver insight** — The transformative realization (~25-30%)
6. **Close with resolution** — Actionable emotional payoff (~15-20%)
7. **Audio bed** — Match channel tempo and key signature
8. **Visual grade** — Apply dominant color palette, brightness, and saturation levels

### Quality Checklist
- [ ] Hook lands in first 3 seconds
- [ ] Emotional keyword density matches channel average
- [ ] Visual palette aligns with top performers
- [ ] Background music tempo within ±10 BPM of channel average
- [ ] Includes one quotable line suitable for title/thumbnail
- [ ] Duration within observed sweet spot
"""


def generate_playbook(config: Config) -> Path:
    """Synthesize all analyses into channel_playbook.md."""
    config.ensure_dirs()

    sections = {
        "1. Visual Style Bible": _visual_style_bible(config),
        "2. Emotional Style Bible": _emotional_style_bible(config),
        "3. Script Style Bible": _script_style_bible(config),
        "4. Audio Style Bible": _audio_style_bible(config),
        "5. Content Calendar Recommendations": _content_calendar(config),
        "6. Content Gaps": _content_gaps(config),
        "7. Viral Patterns": _viral_patterns(config),
        "8. Replication Framework": _replication_framework(config),
    }

    output = config.channel_playbook_md
    write_markdown(
        output,
        "Channel Playbook — Complete Reverse Engineering Report",
        sections,
    )
    logger.info("Wrote channel playbook to %s", output)
    return output

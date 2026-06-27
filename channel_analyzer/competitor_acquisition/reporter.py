"""Write competitor discovery reports."""

from __future__ import annotations

from pathlib import Path

from channel_analyzer.competitor_acquisition.scorer import ScoredCandidate
from channel_analyzer.review_artifact import write_review_artifact


def _fmt_subs(n: int) -> str:
    if n <= 0:
        return "—"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def _fmt_views(n: float) -> str:
    if n <= 0:
        return "—"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return f"{n:.0f}"


def write_channel_candidates_md(
    path: Path,
    scored: list[ScoredCandidate],
    discovery_stats: dict[str, int],
) -> None:
    lines = [
        "# Channel Candidates — Emotional Recovery Niche",
        "",
        "Discovery sources: YouTube search, related/recommended expansion from @WhisprsYT, "
        "and benchmark seed list.",
        "",
        f"**Candidates discovered:** {discovery_stats.get('raw', 0)} | "
        f"**Scored (≥0.25 similarity):** {len(scored)}",
        "",
        "| Channel | Subscribers | Avg Views | Similarity Score | Why Similar | Why Different |",
        "| --- | ---: | ---: | ---: | --- | --- |",
    ]
    for c in scored:
        link = f"[{c.channel_name}]({c.channel_url})"
        lines.append(
            f"| {link} | {_fmt_subs(c.subscribers)} | {_fmt_views(c.avg_views)} | "
            f"{c.similarity_score:.2f} | {c.why_similar} | {c.why_different} |"
        )
    lines.extend(
        [
            "",
            "## Score breakdown (top 10)",
            "",
            "| Channel | Style | Content | Emotional | Audience | Comment | Confidence |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for c in scored[:10]:
        lines.append(
            f"| {c.channel_name} | {c.style_similarity:.2f} | {c.content_similarity:.2f} | "
            f"{c.emotional_similarity:.2f} | {c.audience_similarity:.2f} | "
            f"{c.comment_similarity:.2f} | {c.confidence:.2f} |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def write_top_20_md(path: Path, scored: list[ScoredCandidate]) -> None:
    top = scored[:20]
    lines = [
        "# Top 20 Benchmark Channels",
        "",
        "Ranked by composite similarity to @WhisprsYT reference profile "
        "(content DNA, audience psychology, emotional bible, top titles).",
        "",
        "Weights: content 30%, style 20%, emotional 25%, audience 15%, comment proxy 10%.",
        "",
    ]
    for i, c in enumerate(top, 1):
        lines.extend(
            [
                f"## {i}. [{c.channel_name}]({c.channel_url})",
                "",
                f"- **Similarity:** {c.similarity_score:.2f} (confidence {c.confidence:.2f})",
                f"- **Subscribers:** {_fmt_subs(c.subscribers)} | **Avg views:** {_fmt_views(c.avg_views)}",
                f"- **Discovery:** {c.discovery_source or 'search'}",
                f"- **Why similar:** {c.why_similar}",
                f"- **Why different:** {c.why_different}",
                "",
            ]
        )
    lines.extend(
        [
            "## Recommended benchmark set (5 channels)",
            "",
            "Run full pipeline on these before any new analyzer work:",
            "",
        ]
    )
    for i, c in enumerate(top[:5], 1):
        lines.append(f"{i}. [{c.channel_name}]({c.channel_url}) — score {c.similarity_score:.2f}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def write_discovery_review(
    reports_dir: Path,
    scored: list[ScoredCandidate],
    discovery_stats: dict[str, int],
) -> Path:
    top = scored[:20]
    best = top[:5]
    surprising = [c for c in top if c.style_similarity < 0.4 and c.emotional_similarity > 0.5][:3]
    non_obvious = [c for c in top if "stoic" in c.why_different.lower() or "philosophy" in c.why_different.lower()][:3]
    if not non_obvious:
        non_obvious = [c for c in top[5:12] if c.subscribers < 100_000][:3]

    best_text = "\n".join(
        f"- **{c.channel_name}** ({c.similarity_score:.2f}): {c.why_similar}"
        for c in best
    )
    surprising_text = (
        "\n".join(
            f"- **{c.channel_name}** — high emotional match ({c.emotional_similarity:.2f}) "
            f"with different surface style: {c.why_different}"
            for c in surprising
        )
        or "No strong style/emotional divergence in top ranks yet — expand search if needed."
    )
    non_obvious_text = (
        "\n".join(
            f"- **{c.channel_name}** — adjacent niche candidate: {c.why_different}"
            for c in non_obvious
        )
        or "Adjacent niches (stoicism, philosophy) may appear after deeper comment/visual analysis."
    )

    bias_text = (
        "Discovery is biased toward channels that already rank for Whisprs-adjacent search terms "
        "(poetry quotes, healing shorts, anime aesthetic). Related-video expansion seeds from "
        "@WhisprsYT, which favors the same recommendation graph. Comment similarity is estimated "
        "from title/description tone only — not yet validated. Channels with weak metadata or "
        "non-English content may be under-ranked."
    )

    rec_set = "\n".join(
        f"{i}. [{c.channel_name}]({c.channel_url}) — score {c.similarity_score:.2f}"
        for i, c in enumerate(best[:5], 1)
    )

    validated_signal = (
        "Cross-analyzer convergence on WhisprsYT: comments emphasize heartbreak, loneliness, "
        "healing, self-love; visuals emphasize acceptance, resilience, hope; narrative arc "
        "Pain → Acceptance → Growth. Discovery scores emotional similarity against this profile — "
        "but cannot yet distinguish Whisprs-specific signal from niche-wide signal."
    )

    sections = {
        "Executive Summary": (
            f"Competitor Acquisition Engine discovered {discovery_stats.get('raw', 0)} raw candidates, "
            f"scored {len(scored)} above threshold. Top match: **{top[0].channel_name}** "
            f"({top[0].similarity_score:.2f}). Next step: run full analyzer pipeline on top 5 "
            "and compare content_dna / audience_persona / emotional_bible across channels."
        ),
        "Validated Signal Context": validated_signal,
        "Best Candidates": best_text or "No candidates scored — check network/API access.",
        "Surprising Candidates": surprising_text,
        "Non-Obvious / Adjacent Niche": non_obvious_text,
        "Selection Bias Risks": (
            bias_text
            + " YouTube rate-limited metadata enrichment during this run; subscriber/view "
            "columns may show — until re-run with `python -m channel_analyzer.competitor_acquisition_engine` "
            "(without --offline) after cooldown."
        ),
        "Recommended Benchmark Set": rec_set,
        "Open Questions for Human Review": (
            "- Are top matches true competitors or same recommendation cluster?\n"
            "- Is the validated signal Whisprs-specific or niche-wide?\n"
            "- Missing adjacent niches: stoicism healing, philosophy quotes, pure lofi aesthetic?\n"
            "- Should benchmark include one larger outlier (500K+ subs) for scale comparison?"
        ),
    }
    return write_review_artifact(reports_dir, "DISCOVERY", sections)

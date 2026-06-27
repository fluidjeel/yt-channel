"""Cross-channel pattern synthesis — niche vs channel-specific."""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from channel_analyzer.cross_channel.collector import ChannelProfile, PATTERN_SIGNALS, collect_all_profiles
from channel_analyzer.utils import write_markdown

logger = logging.getLogger(__name__)


@dataclass
class CrossChannelPattern:
    pattern_id: str
    label: str
    channels_observed: list[str]
    frequency: float  # 0-1 across cohort
    confidence: float
    performance_note: str
    classification: str  # niche | unique | emerging | insufficient_data

    def to_row(self) -> dict[str, Any]:
        return {
            "pattern_id": self.pattern_id,
            "label": self.label,
            "channels_observed": "|".join(self.channels_observed),
            "frequency": round(self.frequency, 3),
            "confidence": round(self.confidence, 3),
            "performance_note": self.performance_note,
            "classification": self.classification,
        }


PATTERN_LABELS = {
    "acceptance_emotion": "Acceptance as dominant expression",
    "resilience_emotion": "Quiet resilience",
    "peaceful_sadness": "Peaceful sadness",
    "tiny_human_large_world": "Tiny human / large world composition",
    "solitary_character": "Solitary / dreamer character",
    "looking_away_gaze": "Averted gaze",
    "self_love_theme": "Self-love / self-worth theme",
    "healing_journey": "Healing journey",
    "heartbreak": "Heartbreak",
    "recovery_not_love": "Recovery framing (not love)",
    "pain_acceptance_hope_arc": "Pain → Acceptance → Hope arc",
    "anime_aesthetic": "Anime aesthetic",
    "gratitude": "Gratitude",
    "loneliness": "Loneliness",
}


def _confidence_for_pattern(
    observed: int,
    total: int,
    full_analysis_count: int,
) -> float:
    freq = observed / max(total, 1)
    depth_bonus = min(full_analysis_count / max(total, 1), 1.0) * 0.3
    return min(0.95, round(freq * 0.6 + depth_bonus + (0.1 if observed >= 2 else 0), 3))


def analyze_patterns(
    profiles: list[ChannelProfile],
    reference_slug: str,
) -> list[CrossChannelPattern]:
    total = len(profiles)
    full_count = sum(1 for p in profiles if p.status == "full" or p.has_bibles)

    patterns: list[CrossChannelPattern] = []
    ref = next((p for p in profiles if p.slug == reference_slug), None)

    for pid, label in PATTERN_LABELS.items():
        observed = [p.slug for p in profiles if p.patterns.get(pid)]
        freq = len(observed) / max(total, 1)
        conf = _confidence_for_pattern(len(observed), total, full_count)

        # Performance correlation proxy: avg median vpd of channels with pattern
        vpd_vals = [p.median_views_per_day for p in profiles if p.slug in observed and p.median_views_per_day > 0]
        vpd_note = f"Median views/day among pattern channels: {sum(vpd_vals)/len(vpd_vals):,.0f}" if vpd_vals else "No performance data"

        if freq >= 0.5 and len(observed) >= 2:
            classification = "niche"
        elif ref and pid in [k for k, v in ref.patterns.items() if v] and len(observed) == 1:
            classification = "unique"
        elif freq >= 0.25:
            classification = "emerging"
        else:
            classification = "insufficient_data"

        patterns.append(
            CrossChannelPattern(
                pattern_id=pid,
                label=label,
                channels_observed=observed,
                frequency=freq,
                confidence=conf,
                performance_note=vpd_note,
                classification=classification,
            )
        )

    return sorted(patterns, key=lambda x: (-x.frequency, -x.confidence))


def build_niche_dna_sections(
    patterns: list[CrossChannelPattern],
    profiles: list[ChannelProfile],
    reference_slug: str,
) -> dict[str, str]:
    niche = [p for p in patterns if p.classification == "niche"]
    unique = [p for p in patterns if p.classification == "unique"]
    emerging = [p for p in patterns if p.classification == "emerging"]

    ref = next((p for p in profiles if p.slug == reference_slug), None)
    full_channels = [p.slug for p in profiles if p.has_bibles]
    discovery_only = [p.slug for p in profiles if p.status == "discovery_only"]

    overview = (
        f"**Channels in cohort:** {len(profiles)}\n"
        f"**Full analysis (bibles):** {len(full_channels)} — {', '.join(full_channels) or 'none'}\n"
        f"**Discovery only:** {len(discovery_only)}\n"
        f"**Reference:** `{reference_slug}`\n\n"
        "Purpose: distinguish **niche DNA** (shared) from **channel-specific DNA** (Whisprs-only)."
    )

    niche_body = "\n".join(
        f"- **{p.label}** — {p.frequency:.0%} of channels ({len(p.channels_observed)}/{len(profiles)}), "
        f"confidence {p.confidence:.2f} — observed in: {', '.join(p.channels_observed)}"
        for p in niche[:12]
    ) or "_No patterns yet meet niche threshold (≥50% channels, ≥2 observed). Run more full pipelines._"

    unique_body = "\n".join(
        f"- **{p.label}** — likely unique to {', '.join(p.channels_observed)} (confidence {p.confidence:.2f})"
        for p in unique
    ) or "_No unique patterns identified yet._"

    ref_summary = "_Reference channel not found._"
    if ref:
        ref_summary = (
            f"**{ref.name}** ({ref.slug}): {ref.top_video_count} top videos, "
            f"median {ref.median_views_per_day:,.0f} views/day, "
            f"bibles={'yes' if ref.has_bibles else 'no'}, comments={'yes' if ref.has_comments else 'no'}"
        )

    return {
        "Overview": overview,
        "Reference Channel": ref_summary,
        "Niche Patterns (Shared)": niche_body,
        "Emerging Patterns": "\n".join(
            f"- **{p.label}** ({p.frequency:.0%}, conf {p.confidence:.2f})"
            for p in emerging
        )
        or "_None._",
        "Unique Patterns (Whisprs-specific?)": unique_body,
        "Cohort Status": "\n".join(
            f"- `{p.slug}` ({p.group}): status={p.status}, videos={p.video_count}, "
            f"median_vpd={p.median_views_per_day:,.0f}"
            for p in profiles
        ),
    }


def build_viral_patterns_sections(patterns: list[CrossChannelPattern], profiles: list[ChannelProfile]) -> dict[str, str]:
    ranked = sorted(profiles, key=lambda p: -p.median_views_per_day)
    top = "\n".join(
        f"- **{p.name}** (`{p.slug}`): median {p.median_views_per_day:,.0f} views/day, max {p.max_views_per_day:,.0f}"
        for p in ranked[:5]
        if p.median_views_per_day > 0
    ) or "_No performance data yet — run discovery on benchmark channels._"

    high_conf = [p for p in patterns if p.confidence >= 0.5 and p.frequency >= 0.3]
    pattern_perf = "\n".join(
        f"- **{p.label}**: {p.frequency:.0%} frequency, conf {p.confidence:.2f} — {p.performance_note}"
        for p in high_conf[:10]
    ) or "_Insufficient cross-channel data._"

    return {
        "Top Performers in Cohort": top,
        "High-Confidence Viral Patterns": pattern_perf,
        "Pattern Frequency Table": "\n".join(
            f"| {p.label} | {p.frequency:.0%} | {p.confidence:.2f} | {p.classification} |"
            for p in patterns
        ),
    }


def build_unique_patterns_sections(
    patterns: list[CrossChannelPattern],
    reference_slug: str,
) -> dict[str, str]:
    unique = [p for p in patterns if p.classification == "unique"]
    ref_only = [p for p in unique if reference_slug in p.channels_observed]

    body = "\n".join(
        f"### {p.label}\n"
        f"- Channels: {', '.join(p.channels_observed)}\n"
        f"- Confidence: {p.confidence:.2f}\n"
        f"- Performance: {p.performance_note}\n"
        for p in ref_only
    ) or (
        f"_No patterns classified as unique to `{reference_slug}` yet. "
        "This may mean overfitting cannot be ruled out OR other channels lack full bibles._"
    )

    return {
        "WhisprsYT-Specific Signals": body,
        "Interpretation": (
            "Unique patterns are only reliable when ≥3 competitor channels have full bibles. "
            "Until then, treat Whisprs findings as **hypotheses**, not niche law."
        ),
    }


def build_benchmark_summary_sections(
    profiles: list[ChannelProfile],
    patterns: list[CrossChannelPattern],
) -> dict[str, str]:
    full = sum(1 for p in profiles if p.has_bibles)
    discovery = sum(1 for p in profiles if p.status == "discovery_only")

    return {
        "Cohort Summary": (
            f"- Total channels: {len(profiles)}\n"
            f"- Full analysis: {full}\n"
            f"- Discovery only: {discovery}\n"
            f"- Patterns tracked: {len(patterns)}\n"
            f"- Niche-classified: {sum(1 for p in patterns if p.classification == 'niche')}\n"
            f"- Unique-classified: {sum(1 for p in patterns if p.classification == 'unique')}"
        ),
        "Data Quality Warning": (
            "Cross-channel conclusions are **low confidence** until ≥5 channels have "
            "content_dna.md + audience_psychology.md + advanced_visual data. "
            "Currently most cohort members may be discovery-only."
        ),
        "Recommended Benchmark Actions": (
            "1. Run `--full` on 3-5 direct competitors\n"
            "2. Re-run cross_channel_synthesizer\n"
            "3. Paste CHATGPT_REVIEW_CROSS_CHANNEL.md for external critique"
        ),
    }

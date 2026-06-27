"""Human-readable channel intelligence report from MVP profile JSON (no LLM)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from assembler.helpers import reports_dir
from channel_analyzer.utils import load_json

LOG = logging.getLogger(__name__)

Confidence = str

CONFIDENCE_LABELS: dict[str, str] = {
    "HIGH": "HIGH",
    "MEDIUM": "MEDIUM",
    "LOW": "LOW",
    "N/A": "N/A",
}


def _mvp_profile_path(slug: str) -> Path:
    return reports_dir(slug) / "mvp_profile.json"


def _confidence_badge(level: Confidence) -> str:
    label = CONFIDENCE_LABELS.get(str(level).upper(), str(level))
    return f"`{label}`"


def _format_value(value: Any) -> str:
    if value is None:
        return "_No data available._"
    if isinstance(value, list):
        if not value:
            return "_Empty list._"
        return "\n".join(f"- {item}" for item in value)
    if isinstance(value, dict):
        if not value:
            return "_Empty object._"
        return "\n".join(f"- **{key}:** {val}" for key, val in value.items())
    return str(value)


def _render_evidence_field(title: str, field: dict[str, Any]) -> str:
    conf = field.get("confidence", "N/A")
    body = _format_value(field.get("value"))
    return (
        f"### {title}\n\n"
        f"**Confidence:** {_confidence_badge(conf)}\n\n"
        f"{body}\n"
    )


def _collect_confidence_rows(obj: Any, prefix: str = "") -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    if isinstance(obj, dict):
        if set(obj.keys()) >= {"value", "confidence", "source"}:
            label = prefix or "field"
            rows.append((label, str(obj.get("confidence", "N/A"))))
            return rows
        for key, val in obj.items():
            path = f"{prefix}.{key}" if prefix else key
            rows.extend(_collect_confidence_rows(val, path))
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            rows.extend(_collect_confidence_rows(item, f"{prefix}[{idx}]"))
    return rows


def _filter_recommendations(
    profile: dict[str, Any],
    category: str,
) -> list[dict[str, Any]]:
    items = profile.get("content_recommendations", {}).get("items", [])
    return [item for item in items if item.get("category") == category]


def _render_recommendation_list(items: list[dict[str, Any]]) -> str:
    if not items:
        return "_No items in this category._\n"
    blocks: list[str] = []
    for idx, item in enumerate(items, start=1):
        rec = item.get("recommendation", {})
        conf = rec.get("confidence", "N/A")
        value = _format_value(rec.get("value"))
        blocks.append(
            f"#### {idx}. Recommendation\n\n"
            f"**Confidence:** {_confidence_badge(conf)}\n\n"
            f"{value}\n"
        )
    return "\n".join(blocks)


def render_channel_report(slug: str, *, profile: dict[str, Any] | None = None) -> str:
    """Render markdown report from reports/{slug}/mvp_profile.json."""
    data = profile if profile is not None else load_json(_mvp_profile_path(slug))

    channel_name = data.get("channel_name") or slug
    lines: list[str] = [
        f"# Channel Intelligence Report — {channel_name}",
        "",
        f"**Slug:** `{data.get('channel_slug', slug)}`  ",
        f"**Pipeline status:** {data.get('pipeline_status', 'unknown')}  ",
        f"**Analyzed at:** {data.get('analyzed_at') or '—'}  ",
    ]
    if data.get("channel_url"):
        lines.append(f"**Channel URL:** {data['channel_url']}  ")
    lines.extend(["", "---", ""])

    outcome = data.get("outcome_profile", {})
    lines.extend([
        "## 1. Audience Outcome Profile",
        "",
        _render_evidence_field(
            "Dominant emotional outcome",
            outcome.get("dominant_emotional_outcome", {}),
        ),
        _render_evidence_field(
            "Secondary outcomes",
            outcome.get("secondary_outcomes", {}),
        ),
        "#### Emotional journey",
        "",
        _render_evidence_field(
            "Arrival state",
            outcome.get("emotional_journey", {}).get("arrival_state", {}),
        ),
        _render_evidence_field(
            "Transformation stages",
            outcome.get("emotional_journey", {}).get("transformation_stages", {}),
        ),
        _render_evidence_field(
            "Desired state",
            outcome.get("emotional_journey", {}).get("desired_state", {}),
        ),
        "#### Audience emotional need",
        "",
        _render_evidence_field(
            "Primary need",
            outcome.get("audience_emotional_need", {}).get("primary_need", {}),
        ),
        _render_evidence_field(
            "Save signals",
            outcome.get("audience_emotional_need", {}).get("save_signals", {}),
        ),
        _render_evidence_field(
            "Share signals",
            outcome.get("audience_emotional_need", {}).get("share_signals", {}),
        ),
        "---",
        "",
    ])

    brand = data.get("brand_profile", {})
    lines.extend([
        "## 2. Brand Identity Profile",
        "",
        "#### Visual identity",
        "",
        _render_evidence_field(
            "Style summary",
            brand.get("visual_identity", {}).get("style_summary", {}),
        ),
        _render_evidence_field(
            "Dominant motifs",
            brand.get("visual_identity", {}).get("dominant_motifs", {}),
        ),
        "#### Narrative identity",
        "",
        _render_evidence_field(
            "Structure template",
            brand.get("narrative_identity", {}).get("structure_template", {}),
        ),
        _render_evidence_field(
            "Voice / tone",
            brand.get("narrative_identity", {}).get("voice_tone", {}),
        ),
        "#### Production signature",
        "",
        _render_evidence_field(
            "Pacing / cadence",
            brand.get("production_signature", {}).get("pacing_cadence", {}),
        ),
        _render_evidence_field(
            "Music mood",
            brand.get("production_signature", {}).get("music_mood", {}),
        ),
        _render_evidence_field(
            "Overall profile confidence",
            brand.get("profile_confidence", {}),
        ),
        "---",
        "",
    ])

    lines.extend([
        "## 3. Content Opportunities",
        "",
        _render_recommendation_list(_filter_recommendations(data, "content_gaps")),
        "---",
        "",
    ])

    recs = data.get("content_recommendations", {})
    evidence_tier = recs.get("evidence_tier", {})
    conf_rows = _collect_confidence_rows({
        "outcome_profile": outcome,
        "brand_profile": brand,
    })
    tier_value = evidence_tier.get("value", "—")
    tier_conf = evidence_tier.get("confidence", "N/A")

    lines.extend([
        "## 4. Evidence Confidence",
        "",
        f"**Overall evidence tier:** {_format_value(tier_value)} "
        f"({_confidence_badge(tier_conf)})",
        "",
        "| Field | Confidence |",
        "| --- | --- |",
    ])
    for field_path, level in conf_rows:
        lines.append(f"| `{field_path}` | {_confidence_badge(level)} |")
    lines.extend(["", "---", ""])

    lines.extend([
        "## 5. Top Performing Patterns",
        "",
        _render_recommendation_list(_filter_recommendations(data, "performance_correlations")),
        "---",
        "",
    ])

    lines.extend([
        "## 6. Recommended Experiments",
        "",
        _render_recommendation_list(_filter_recommendations(data, "viral_patterns")),
        "",
        "---",
        "",
        "_Generated from MVP profile JSON — no inference or LLM. "
        "See `reports/{slug}/mvp_profile.json` for source paths per field._".format(slug=slug),
        "",
    ])

    return "\n".join(lines)


def write_channel_report(slug: str, output_path: Path | None = None) -> Path:
    """Write channel_intelligence_report.md for slug."""
    path = _mvp_profile_path(slug)
    if not path.exists():
        raise FileNotFoundError(f"MVP profile not found: {path}")

    out = output_path or (reports_dir(slug) / "channel_intelligence_report.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    content = render_channel_report(slug)
    out.write_text(content, encoding="utf-8")
    LOG.info("Wrote channel report: %s", out)
    return out

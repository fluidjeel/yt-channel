"""Shared helpers for reading pipeline artifacts (no LLM calls)."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from channel_analyzer.benchmark.config import channel_config
from channel_analyzer.config import PROJECT_ROOT
from channel_analyzer.utils import read_csv


def reports_dir(slug: str) -> Path:
    return channel_config(slug).reports_dir


def data_dir(slug: str) -> Path:
    return channel_config(slug).data_dir


def read_report(slug: str, name: str) -> str:
    path = reports_dir(slug) / name
    if path.exists():
        return path.read_text(encoding="utf-8", errors="replace")
    return ""


def report_path(slug: str, name: str) -> str:
    return str(reports_dir(slug) / name)


def data_path(slug: str, name: str) -> str:
    return str(data_dir(slug) / name)


def extract_section(md: str, heading: str) -> str:
    """Return markdown body under ## heading until next ##."""
    pattern = rf"^##\s+{re.escape(heading)}\s*$"
    match = re.search(pattern, md, re.MULTILINE | re.IGNORECASE)
    if not match:
        return ""
    start = match.end()
    nxt = re.search(r"^##\s+", md[start:], re.MULTILINE)
    return md[start : start + nxt.start()] if nxt else md[start:]


def extract_subsection(md: str, heading: str) -> str:
    pattern = rf"^###\s+{re.escape(heading)}\s*$"
    match = re.search(pattern, md, re.MULTILINE | re.IGNORECASE)
    if not match:
        return ""
    start = match.end()
    nxt = re.search(r"^###?\s+", md[start:], re.MULTILINE)
    return md[start : start + nxt.start()] if nxt else md[start:]


def first_bullet_matching(md: str, prefix: str = "-") -> str:
    for line in md.splitlines():
        line = line.strip()
        if line.startswith(prefix):
            return line.lstrip("- ").strip()
    return ""


def parse_percent_line(md: str, label: str) -> float | None:
    m = re.search(rf"\*\*{re.escape(label)}\*\*[:\s]*(\d+(?:\.\d+)?)\s*%", md, re.I)
    if m:
        return float(m.group(1))
    m = re.search(rf"{re.escape(label)}[:\s]*(\d+(?:\.\d+)?)\s*%", md, re.I)
    return float(m.group(1)) if m else None


def parse_narrative_template(slug: str) -> list[str] | None:
    md = read_report(slug, "narrative_patterns.md")
    m = re.search(r"Most common structure:\s*\*\*(.+?)\*\*", md)
    if not m:
        return None
    parts = [p.strip() for p in re.split(r"\s*→\s*", m.group(1)) if p.strip()]
    return parts or None


def parse_emotional_arc_from_bible(slug: str) -> list[str] | None:
    """Only emit emotional arc if explicitly stated in bible Facts (not Interpretations)."""
    md = read_report(slug, "master_emotional_bible.md")
    facts = extract_section(md, "Facts (Evidence-Based)")
    if not facts:
        return None
    m = re.search(
        r"(Pain\s*(?:→|to)\s*(?:Understanding,?\s*)?Acceptance(?:\s*(?:→|and)\s*Growth)?)",
        facts,
        re.I,
    )
    if not m:
        return None
    text = m.group(1)
    if "→" in text:
        return [p.strip() for p in text.split("→") if p.strip()]
    stages = re.split(r"\s+to\s+|\s+and\s+", text, flags=re.I)
    return [s.strip() for s in stages if s.strip()] or None


def dominant_from_csv(slug: str, filename: str, column: str) -> str | None:
    path = data_dir(slug) / filename
    if not path.exists():
        return None
    df = read_csv(path)
    if df.empty or column not in df.columns:
        return None
    counts = df[column].astype(str).value_counts()
    return str(counts.index[0]) if len(counts) else None


def mean_from_csv(slug: str, filename: str, column: str) -> float | None:
    path = data_dir(slug) / filename
    if not path.exists():
        return None
    df = read_csv(path)
    if df.empty or column not in df.columns:
        return None
    return float(df[column].astype(float).mean())


def cleaned_comment_count(slug: str) -> int:
    path = data_dir(slug) / "comments.csv"
    if not path.exists():
        return 0
    df = read_csv(path)
    if df.empty:
        return 0
    if "is_spam" in df.columns:
        df = df[df["is_spam"] == False]  # noqa: E712
    return len(df)


def comment_theme_counts(slug: str, top_n: int = 8) -> list[dict[str, Any]]:
    path = data_dir(slug) / "comments.csv"
    if not path.exists():
        return []
    df = read_csv(path)
    if df.empty or "theme" not in df.columns:
        return []
    if "is_spam" in df.columns:
        df = df[df["is_spam"] == False]  # noqa: E712
    total = len(df)
    if total == 0:
        return []
    counts = df["theme"].astype(str).value_counts().head(top_n)
    return [
        {"theme": str(k), "count": int(v), "pct": round(v / total, 4)}
        for k, v in counts.items()
        if k and k != "spam"
    ]


def quote_theme_counts(slug: str, top_n: int = 8) -> list[dict[str, Any]]:
    path = data_dir(slug) / "quote_database.csv"
    if not path.exists():
        return []
    df = read_csv(path)
    if df.empty or "theme" not in df.columns:
        return []
    counts = df["theme"].astype(str).value_counts().head(top_n)
    return [{"theme": str(k), "count": int(v)} for k, v in counts.items()]


def parse_emotional_triggers(slug: str, top_n: int = 3) -> list[str]:
    md = read_report(slug, "audience_psychology.md")
    section = extract_section(md, "Emotional Triggers")
    labels: list[str] = []
    for line in section.splitlines():
        m = re.match(r"^-\s+\*\*([^*]+)\*\*", line.strip())
        if m:
            labels.append(m.group(1).strip())
        if len(labels) >= top_n:
            break
    return labels


def parse_save_signals(slug: str, limit: int = 8) -> list[str]:
    md = read_report(slug, "audience_psychology.md")
    section = extract_section(md, "Why Viewers Save")
    signals: list[str] = []
    for line in section.splitlines():
        if line.strip().startswith("- ") and "comments" not in line.lower()[:20]:
            text = line.strip()[2:].strip().strip('"')
            if len(text) > 10:
                signals.append(text[:200])
        if len(signals) >= limit:
            break
    return signals


def parse_share_signals(slug: str, limit: int = 8) -> list[str]:
    md = read_report(slug, "audience_psychology.md")
    section = extract_section(md, "Why Viewers Share")
    signals: list[str] = []
    for line in section.splitlines():
        if line.strip().startswith("- ") and "comments" not in line.lower()[:20]:
            text = line.strip()[2:].strip().strip('"')
            if len(text) > 10 and "few explicit" not in text.lower():
                signals.append(text[:200])
        if len(signals) >= limit:
            break
    return signals


def parse_key_insight_first(slug: str) -> str:
    md = read_report(slug, "audience_psychology.md")
    section = extract_section(md, "Key Insights")
    return first_bullet_matching(section)


def parse_cohort_niche_patterns() -> list[str]:
    path = PROJECT_ROOT / "reports" / "cross_channel_synthesis_v2.md"
    if not path.exists():
        return []
    md = path.read_text(encoding="utf-8", errors="replace")
    section = extract_section(md, "Niche Patterns (Shared)")
    patterns: list[str] = []
    for line in section.splitlines():
        m = re.match(r"^-\s+\*\*([^*]+)\*\*", line.strip())
        if m:
            patterns.append(m.group(1).strip())
    return patterns


def parse_channel_unique_signals(slug: str) -> list[str]:
    path = PROJECT_ROOT / "reports" / "validation_phase2.md"
    if not path.exists():
        return []
    md = path.read_text(encoding="utf-8", errors="replace")
    signals: list[str] = []
    for line in md.splitlines():
        if f"`{slug}`" in line:
            signals.append(line.strip().lstrip("- "))
    whisprs = extract_section(md, "Whisprs-Specific Findings")
    if slug == "whisprs_yt":
        for line in whisprs.splitlines():
            if line.strip().startswith("- "):
                signals.append(line.strip()[2:])
    return signals[:10]


def parse_playbook_gaps(slug: str) -> list[str]:
    md = read_report(slug, "channel_playbook.md")
    section = extract_subsection(md, "6. Content Gaps")
    items: list[str] = []
    for line in section.splitlines():
        if line.strip().startswith("- "):
            items.append(line.strip()[2:])
    return items


def parse_playbook_viral_patterns(slug: str) -> list[str]:
    md = read_report(slug, "channel_playbook.md")
    section = extract_subsection(md, "7. Viral Patterns")
    items: list[str] = []
    for line in section.splitlines():
        if line.strip().startswith("- "):
            items.append(line.strip()[2:])
    return items


def parse_performance_correlations(slug: str) -> list[str]:
    md = read_report(slug, "advanced_visual_analysis.md")
    section = extract_section(md, "Performance Correlations")
    if not section:
        section = extract_section(md, "Key Insights")
    items: list[str] = []
    for line in section.splitlines():
        if line.strip().startswith("- "):
            items.append(line.strip()[2:])
    high = extract_subsection(md, "High performers")
    for line in high.splitlines():
        if line.strip().startswith("- "):
            items.append(f"High performers: {line.strip()[2:]}")
    return items[:15]


def parse_dna_facts(slug: str) -> list[str]:
    md = read_report(slug, "content_dna.md")
    section = extract_section(md, "Facts (Evidence-Based)")
    facts: list[str] = []
    for line in section.splitlines():
        if line.strip().startswith("- "):
            facts.append(line.strip()[2:])
    return facts


def parse_bible_gaps(slug: str) -> list[str]:
    items: list[str] = []
    for name in ("content_dna.md", "audience_persona.md", "master_emotional_bible.md"):
        md = read_report(slug, name)
        section = extract_section(md, "Unknowns / Gaps")
        for line in section.splitlines():
            if line.strip().startswith("- "):
                items.append(line.strip()[2:])
    return items


def channel_name(slug: str) -> str:
    df = read_csv(data_dir(slug) / "videos.csv")
    if not df.empty and "channel" in df.columns:
        val = str(df["channel"].iloc[0]).strip()
        if val:
            return val
    meta = reports_dir(slug) / "benchmark_meta.json"
    if meta.exists():
        try:
            data = json.loads(meta.read_text(encoding="utf-8"))
            return str(data.get("slug", slug))
        except json.JSONDecodeError:
            pass
    return slug


def pipeline_status(slug: str) -> str:
    meta = reports_dir(slug) / "benchmark_meta.json"
    if meta.exists():
        try:
            return str(json.loads(meta.read_text(encoding="utf-8")).get("status", "unknown"))
        except json.JSONDecodeError:
            pass
    bibles = all((reports_dir(slug) / f).exists() for f in (
        "content_dna.md",
        "audience_persona.md",
        "master_emotional_bible.md",
    ))
    return "full" if bibles else "partial"


def analyzed_at(slug: str) -> str | None:
    rdir = reports_dir(slug)
    if not rdir.exists():
        return None
    mtimes = [p.stat().st_mtime for p in rdir.glob("*") if p.is_file()]
    if not mtimes:
        return None
    return datetime.fromtimestamp(max(mtimes), tz=timezone.utc).isoformat()


def list_source_reports(slug: str) -> list[str]:
    paths: list[str] = []
    for base in (reports_dir(slug), data_dir(slug)):
        if base.exists():
            paths.extend(str(p) for p in sorted(base.iterdir()) if p.is_file())
    cohort = PROJECT_ROOT / "reports" / "cross_channel_synthesis_v2.md"
    if cohort.exists():
        paths.append(str(cohort))
    return paths

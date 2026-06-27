"""Tests for bible synthesis collector."""

from pathlib import Path

from channel_analyzer.config import Config
from channel_analyzer.llm_synthesis.collector import collect_synthesis_context, REPORT_FILES
from channel_analyzer.llm_synthesis.prompts import BIBLE_SPECS, build_bible_prompt


def test_report_files_exist_in_project():
    config = Config.from_yaml()
    found = sum(1 for name in REPORT_FILES if (config.reports_dir / name).exists())
    assert found >= 5, f"Expected at least 5 reports, found {found}"


def test_collect_synthesis_context():
    config = Config.from_yaml()
    ctx = collect_synthesis_context(config)
    assert ctx.reports
    assert ctx.source_hash
    assert len(ctx.report_bundle()) > 100


def test_bible_prompts_cover_all_specs():
    config = Config.from_yaml()
    ctx = collect_synthesis_context(config)
    for bible_id in BIBLE_SPECS:
        prompt = build_bible_prompt(ctx, bible_id)
        assert "Facts (Evidence-Based)" in prompt
        assert ctx.channel_name in prompt or "unknown" in prompt.lower()

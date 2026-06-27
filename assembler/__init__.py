"""MVP profile assembler — maps existing pipeline reports to structured JSON."""

from assembler.assemble import assemble_mvp_profile
from assembler.report_renderer import render_channel_report, write_channel_report

__all__ = [
    "assemble_mvp_profile",
    "render_channel_report",
    "write_channel_report",
]

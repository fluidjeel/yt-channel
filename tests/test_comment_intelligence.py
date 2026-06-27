"""Unit tests for comment intelligence."""

from channel_analyzer.comments.analyzer import (
    detect_save_signal,
    detect_share_signal,
    is_spam,
    _cross_video_phrases,
)
from channel_analyzer.comments.models import AnalyzedComment


def test_spam_detection():
    assert is_spam("hi")
    assert is_spam("check out my channel for more")
    assert is_spam("https://spam.com")
    assert not is_spam("This really spoke to my heart today")


def test_save_share_signals():
    assert detect_save_signal("I needed to hear this, saving for later")
    assert detect_share_signal("Sent this to my best friend")
    assert not detect_save_signal("Beautiful video")


def test_cross_video_phrases():
    comments = [
        AnalyzedComment(
            comment_id="1",
            video_id="a",
            channel="ch",
            video_title="t",
            video_rank=1,
            video_views_per_day=1000,
            text="love yourself more each day",
            like_count=5,
            author="u1",
            is_spam=False,
            cluster_id=0,
            theme="letting_go",
            emotional_state="acceptance",
            life_situation="breakup",
            save_signal=False,
            share_signal=False,
            pain_point_score=0.7,
            confidence=0.8,
        ),
        AnalyzedComment(
            comment_id="2",
            video_id="b",
            channel="ch",
            video_title="t2",
            video_rank=2,
            video_views_per_day=500,
            text="love yourself changed my life",
            like_count=3,
            author="u2",
            is_spam=False,
            cluster_id=0,
            theme="letting_go",
            emotional_state="acceptance",
            life_situation="breakup",
            save_signal=True,
            share_signal=False,
            pain_point_score=0.6,
            confidence=0.75,
        ),
    ]
    phrases = _cross_video_phrases(comments, min_videos=2)
    assert any("love yourself" in p["phrase"] for p in phrases)

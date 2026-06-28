"""Tests for Netscape cookie export."""

from __future__ import annotations

from scripts.cookie_netscape import filter_youtube_cookies, has_youtube_session, to_netscape


def test_has_youtube_session() -> None:
    assert has_youtube_session([{"name": "SID", "value": "x"}])
    assert not has_youtube_session([{"name": "PREF", "value": "x"}])


def test_to_netscape_youtube_only() -> None:
    cookies = [
        {
            "name": "SID",
            "value": "abc",
            "domain": ".youtube.com",
            "path": "/",
            "secure": True,
            "expires": 1893456000,
        },
        {
            "name": "unrelated",
            "value": "nope",
            "domain": ".google.com",
            "path": "/",
            "secure": True,
            "expires": -1,
        },
    ]
    yt = filter_youtube_cookies(cookies)
    text = to_netscape(yt)
    assert "SID\tabc" in text
    assert "unrelated" not in text

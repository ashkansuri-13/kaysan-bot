"""Unit tests for bot.handlers.groups."""
import pytest
import time
from bot.handlers.groups import (
    _flood_tracker, _last_msg_time,
    _BAD_WORDS_RE, _SPAM_LINKS_RE, _KEYWORD_REPLIES,
)


class TestStateDicts:
    def test_flood_tracker(self):
        assert isinstance(_flood_tracker, dict)

    def test_last_msg_time(self):
        assert isinstance(_last_msg_time, dict)


class TestSpamFilter:
    def test_spam_link(self):
        assert _SPAM_LINKS_RE.search("click here to win prize")
        assert _SPAM_LINKS_RE.search("t.me/joinchat/abc")
        assert _SPAM_LINKS_RE.search("bit.ly/xyz")

    def test_normal_link(self):
        assert not _SPAM_LINKS_RE.search("https://google.com")


class TestBadWords:
    def test_bad_word(self):
        assert _BAD_WORDS_RE.search("fuck you")
        assert _BAD_WORDS_RE.search("shit")

    def test_normal_text(self):
        assert not _BAD_WORDS_RE.search("hello how are you")


class TestKeywordReplies:
    def test_all_languages(self):
        assert "ku" in _KEYWORD_REPLIES
        assert "fa" in _KEYWORD_REPLIES
        assert "en" in _KEYWORD_REPLIES

    def test_patterns_exist(self):
        for lang, patterns in _KEYWORD_REPLIES.items():
            assert len(patterns) > 0
            for pattern, reply in patterns.items():
                assert len(pattern) > 0
                assert len(reply) > 0

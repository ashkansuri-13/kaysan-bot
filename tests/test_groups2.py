"""Groups handler tests — comprehensive."""
import pytest
import re
from bot.handlers.groups import (
    _flood_tracker, _last_msg_time,
    _BAD_WORDS_RE, _SPAM_LINKS_RE, _KEYWORD_REPLIES,
    _is_admin,
)


class TestIsAdmin:
    def test_exists(self):
        assert callable(_is_admin)


class TestFloodTracker:
    def test_defaultdict(self):
        _flood_tracker.clear()
        uid = 9999
        _flood_tracker[123][uid].append(1.0)
        assert len(_flood_tracker[123][uid]) == 1
        _flood_tracker.clear()


class TestSpamPatterns:
    def test_various_spam(self):
        assert _SPAM_LINKS_RE.search("t.me/joinchat/abc")
        assert _SPAM_LINKS_RE.search("bit.ly/xyz")
        assert _SPAM_LINKS_RE.search("click here free gift")

    def test_normal_urls(self):
        assert not _SPAM_LINKS_RE.search("https://google.com")
        assert not _SPAM_LINKS_RE.search("https://github.com")


class TestBadWordsPatterns:
    def test_various_bad(self):
        assert _BAD_WORDS_RE.search("fuck")
        assert _BAD_WORDS_RE.search("shit")
        assert _BAD_WORDS_RE.search("damn")

    def test_normal_text(self):
        assert not _BAD_WORDS_RE.search("hello world")
        assert not _BAD_WORDS_RE.search("سلام دنیا")


class TestKeywordRepliesExtended:
    def test_kurdish_patterns(self):
        patterns = _KEYWORD_REPLIES["ku"]
        for pattern, reply in patterns.items():
            assert re.search(pattern, "test", re.I) is None or len(reply) > 0

    def test_persian_patterns(self):
        patterns = _KEYWORD_REPLIES["fa"]
        for pattern, reply in patterns.items():
            assert len(pattern) > 0
            assert len(reply) > 0

    def test_english_patterns(self):
        patterns = _KEYWORD_REPLIES["en"]
        for pattern, reply in patterns.items():
            assert len(pattern) > 0
            assert len(reply) > 0

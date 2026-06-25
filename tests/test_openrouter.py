"""Unit tests for bot.openrouter — API client."""
import pytest
from bot.openrouter import with_system, vision_message


class TestWithSystem:
    def test_basic(self):
        msgs = with_system("system text", "user text")
        assert len(msgs) == 2
        assert msgs[0]["role"] == "system"
        assert msgs[1]["role"] == "user"

    def test_with_history(self):
        history = [{"role": "user", "content": "old"}]
        msgs = with_system("system", "new", history)
        assert len(msgs) == 3
        assert msgs[1]["role"] == "user"
        assert msgs[1]["content"] == "old"

    def test_empty_history(self):
        msgs = with_system("system", "user", [])
        assert len(msgs) == 2


class TestVisionMessage:
    def test_basic(self):
        msgs = vision_message("Analyze", "what is this", "data:image/jpeg;base64,abc")
        assert len(msgs) == 2
        assert msgs[0]["role"] == "system"
        assert msgs[1]["role"] == "user"
        assert isinstance(msgs[1]["content"], list)
        assert len(msgs[1]["content"]) == 2

    def test_content_types(self):
        msgs = vision_message("Analyze", "describe", "data:image/png;base64,xyz")
        content = msgs[1]["content"]
        assert content[0]["type"] == "text"
        assert content[1]["type"] == "image_url"

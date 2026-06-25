"""Unit tests for bot.services.image."""
import pytest
from bot.services.image import _enhance_prompt, STYLE_PROMPTS, STYLE_KEYWORDS


class TestImage:
    def test_style_prompts_exist(self):
        assert "realistic" in STYLE_PROMPTS
        assert "anime" in STYLE_PROMPTS

    def test_enhance_prompt_exists(self):
        assert callable(_enhance_prompt)

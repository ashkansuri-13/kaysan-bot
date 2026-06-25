"""Unit tests for bot.handlers.common."""
import pytest
from bot.handlers.common import (
    cmd_start, cmd_help, cmd_lang, cb_lang,
    cmd_image, cmd_clear,
)


class TestCommonHandlers:
    def test_cmd_start_exists(self):
        assert callable(cmd_start)

    def test_cmd_help_exists(self):
        assert callable(cmd_help)

    def test_cmd_lang_exists(self):
        assert callable(cmd_lang)

    def test_cb_lang_exists(self):
        assert callable(cb_lang)

    def test_cmd_image_exists(self):
        assert callable(cmd_image)

    def test_cmd_clear_exists(self):
        assert callable(cmd_clear)

"""Integration tests — تست‌های یکپارچگی."""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from bot.database import init_db, ensure_user, get_lang, set_lang
from bot.router import detect_intent, detect_lang
from bot.texts import t
from bot.keyboards import answer_kb, lang_kb
from bot.openrouter import with_system, vision_message


@pytest_asyncio.fixture
async def setup_db():
    await init_db()
    yield


class TestDatabaseIntegration:
    @pytest.mark.asyncio
    async def test_user_lifecycle(self, setup_db):
        uid = 777700
        import aiosqlite
        from bot import config
        async with aiosqlite.connect(str(config.DB_PATH)) as db:
            await db.execute("DELETE FROM users WHERE user_id=?", (uid,))
            await db.commit()
        await ensure_user(uid, lang="fa", name="Test User")
        lang = await get_lang(uid)
        assert lang == "fa"
        await set_lang(uid, "ku")
        lang = await get_lang(uid)
        assert lang == "ku"


class TestRouterIntegration:
    def test_intent_chain(self):
        assert detect_intent("عکس بکش") == "image"
        assert detect_intent("کد بنویس") == "code"
        assert detect_intent("سلام") == "chat"

    def test_lang_chain(self):
        assert detect_lang("سڵاو") == "ku"
        assert detect_lang("سلام") == "fa"
        assert detect_lang("hello") == "en"


class TestTextsIntegration:
    def test_all_languages_have_required_keys(self):
        required = ["welcome", "error", "help", "thinking"]
        for lang in ["ku", "fa", "en"]:
            for key in required:
                result = t(lang, key)
                assert len(result) > 0, f"{lang}.{key} is empty"


class TestKeyboardsIntegration:
    def test_all_languages_keyboards(self):
        for lang in ["ku", "fa", "en"]:
            kb = answer_kb(lang)
            assert kb is not None
            assert len(kb.inline_keyboard) > 0

    def test_lang_keyboard(self):
        kb = lang_kb()
        assert kb is not None
        assert len(kb.inline_keyboard[0]) == 3


class TestOpenRouterIntegration:
    def test_system_message(self):
        msgs = with_system("system", "user")
        assert len(msgs) == 2
        assert msgs[0]["role"] == "system"

    def test_vision_message(self):
        msgs = vision_message("Analyze", "describe", "data:image/jpeg;base64,abc")
        assert len(msgs) == 2
        assert isinstance(msgs[1]["content"], list)

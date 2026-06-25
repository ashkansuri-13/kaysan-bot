"""Comprehensive tests for bot.handlers.tools — all commands mocked."""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from bot.handlers.tools import (
    cmd_qr, cmd_short, cmd_screenshot, cmd_exchange,
    cmd_stock, cmd_password, cmd_text2img, cmd_calc,
    cmd_meme, cmd_invoice, cmd_done, cmd_flashcard,
    cmd_habit, cmd_expense, cmd_travel, cmd_recipe,
    cmd_news, cmd_challenge, cmd_advanced_poll, cmd_guess,
    handle_invoice_input, cb_flashcard_show,
    cb_challenge_done, cb_challenge_next, cb_guess as cb_guess_handler,
    _tool_state, _invoice_state, _flash_cards, _flash_idx,
    _habits, _expenses, _guess_games,
)


def make_message(text="/qr test", user_id=123):
    msg = AsyncMock()
    msg.text = text
    msg.from_user = MagicMock()
    msg.from_user.id = user_id
    msg.from_user.full_name = "Test User"
    msg.answer = AsyncMock()
    msg.answer_photo = AsyncMock()
    msg.answer_poll = AsyncMock()
    msg.bot = AsyncMock()
    return msg


def make_callback(data="fc:show", user_id=123):
    call = AsyncMock()
    call.data = data
    call.from_user = MagicMock()
    call.from_user.id = user_id
    call.message = AsyncMock()
    call.message.edit_text = AsyncMock()
    call.answer = AsyncMock()
    return call


class TestCommands:
    @pytest.mark.asyncio
    async def test_cmd_qr_no_args(self):
        msg = make_message("/qr")
        await cmd_qr(msg)
        msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_cmd_password(self):
        msg = make_message("/password 16")
        await cmd_password(msg)
        msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_cmd_calc(self):
        msg = make_message("/calc 2+2")
        await cmd_calc(msg)
        msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_cmd_calc_no_args(self):
        msg = make_message("/calc")
        await cmd_calc(msg)
        msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_cmd_meme_no_args(self):
        msg = make_message("/meme")
        await cmd_meme(msg)
        msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_cmd_invoice(self):
        msg = make_message("/invoice")
        await cmd_invoice(msg)
        msg.answer.assert_called()
        assert 123 in _invoice_state

    @pytest.mark.asyncio
    async def test_cmd_done_no_items(self):
        msg = make_message("/done")
        _invoice_state.pop(123, None)
        await cmd_done(msg)
        msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_cmd_flashcard_add(self):
        msg = make_message("/flashcard add Q | A")
        await cmd_flashcard(msg)
        msg.answer.assert_called()
        _flash_cards.pop(123, None)

    @pytest.mark.asyncio
    async def test_cmd_flashcard_no_args(self):
        msg = make_message("/flashcard")
        await cmd_flashcard(msg)
        msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_cmd_habit_add(self):
        msg = make_message("/habit add exercise")
        await cmd_habit(msg)
        msg.answer.assert_called()
        _habits.pop(123, None)

    @pytest.mark.asyncio
    async def test_cmd_habit_no_args(self):
        msg = make_message("/habit")
        await cmd_habit(msg)
        msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_cmd_expense(self):
        msg = make_message("/expense 50000 lunch")
        await cmd_expense(msg)
        msg.answer.assert_called()
        _expenses.pop(123, None)

    @pytest.mark.asyncio
    async def test_cmd_expense_no_args(self):
        msg = make_message("/expense")
        await cmd_expense(msg)
        msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_cmd_expense_list(self):
        msg = make_message("/expense list")
        _expenses[123] = [(50000, "lunch")]
        await cmd_expense(msg)
        msg.answer.assert_called()
        _expenses.pop(123, None)

    @pytest.mark.asyncio
    async def test_cmd_expense_total(self):
        msg = make_message("/expense total")
        _expenses[123] = [(50000, "lunch")]
        await cmd_expense(msg)
        msg.answer.assert_called()
        _expenses.pop(123, None)

    @pytest.mark.asyncio
    async def test_cmd_guess(self):
        msg = make_message("/guess")
        await cmd_guess(msg)
        msg.answer.assert_called()
        assert 123 in _guess_games
        _guess_games.pop(123, None)

    @pytest.mark.asyncio
    async def test_cmd_travel_no_args(self):
        msg = make_message("/travel")
        await cmd_travel(msg)
        msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_cmd_recipe_no_args(self):
        msg = make_message("/recipe")
        await cmd_recipe(msg)
        msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_cmd_advanced_poll(self):
        msg = make_message("/advancedpoll Title | A, B, C")
        await cmd_advanced_poll(msg)
        msg.answer_poll.assert_called()

    @pytest.mark.asyncio
    async def test_cmd_advanced_poll_no_args(self):
        msg = make_message("/advancedpoll")
        await cmd_advanced_poll(msg)
        msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_cmd_short_no_args(self):
        msg = make_message("/short")
        await cmd_short(msg)
        msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_cmd_screenshot_no_args(self):
        msg = make_message("/screenshot")
        await cmd_screenshot(msg)
        msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_cmd_exchange_no_args(self):
        msg = make_message("/exchange")
        await cmd_exchange(msg)
        msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_cmd_stock_no_args(self):
        msg = make_message("/stock")
        await cmd_stock(msg)
        msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_cmd_text2img_no_args(self):
        msg = make_message("/text2img")
        await cmd_text2img(msg)
        msg.answer.assert_called()


class TestCallbacks:
    @pytest.mark.asyncio
    async def test_cb_flashcard_show(self):
        call = make_callback("fc:show")
        _flash_cards[123] = [{"q": "Q", "a": "A", "score": 0}]
        _flash_idx[123] = 0
        await cb_flashcard_show(call)
        call.answer.assert_called()
        _flash_cards.pop(123, None)
        _flash_idx.pop(123, None)

    @pytest.mark.asyncio
    async def test_cb_challenge_done(self):
        call = make_callback("challenge_done")
        await cb_challenge_done(call)
        call.answer.assert_called()

    @pytest.mark.asyncio
    async def test_cb_challenge_next(self):
        call = make_callback("challenge_next")
        with patch("bot.handlers.tools.cmd_challenge", new_callable=AsyncMock):
            await cb_challenge_next(call)
            call.answer.assert_called()

    @pytest.mark.asyncio
    async def test_cb_guess_correct(self):
        call = make_callback("guess:5")
        _guess_games[123] = {"target": 5, "tries": 0, "max": 7}
        await cb_guess_handler(call)
        call.message.edit_text.assert_called()
        _guess_games.pop(123, None)

    @pytest.mark.asyncio
    async def test_cb_guess_wrong(self):
        call = make_callback("guess:3")
        _guess_games[123] = {"target": 5, "tries": 0, "max": 7}
        await cb_guess_handler(call)
        call.answer.assert_called()
        _guess_games.pop(123, None)

    @pytest.mark.asyncio
    async def test_cb_guess_game_over(self):
        call = make_callback("guess:1")
        _guess_games[123] = {"target": 5, "tries": 7, "max": 7}
        await cb_guess_handler(call)
        call.message.edit_text.assert_called()
        _guess_games.pop(123, None)

    @pytest.mark.asyncio
    async def test_cb_guess_no_game(self):
        call = make_callback("guess:5")
        _guess_games.pop(123, None)
        await cb_guess_handler(call)
        call.answer.assert_called()


class TestInvoiceInput:
    @pytest.mark.asyncio
    async def test_invoice_input(self):
        msg = make_message("lunch | 50000 | 2")
        _invoice_state[123] = []
        await handle_invoice_input(msg)
        msg.answer.assert_called()
        _invoice_state.pop(123, None)

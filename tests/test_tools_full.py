"""Comprehensive tests for bot.handlers.tools — full coverage."""
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
    _safe_calc, _tool_state, _invoice_state, _flash_cards,
    _flash_idx, _habits, _expenses, _guess_games,
    _clean, _set, _get,
)


def make_message(text="/test", user_id=123):
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


def make_callback(data="test", user_id=123):
    call = AsyncMock()
    call.data = data
    call.from_user = MagicMock()
    call.from_user.id = user_id
    call.message = AsyncMock()
    call.message.edit_text = AsyncMock()
    call.message.delete = AsyncMock()
    call.answer = AsyncMock()
    return call


class TestSafeCalcFull:
    def test_all_operations(self):
        assert _safe_calc("2+3") == 5
        assert _safe_calc("10-4") == 6
        assert _safe_calc("3*4") == 12
        assert _safe_calc("10/2") == 5.0
        assert _safe_calc("7//2") == 3
        assert _safe_calc("10%3") == 1
        assert _safe_calc("2**3") == 8

    def test_functions(self):
        import math
        assert _safe_calc("sqrt(9)") == 3.0
        assert abs(_safe_calc("sin(0)")) < 0.001
        assert abs(_safe_calc("cos(0)") - 1.0) < 0.001
        assert abs(_safe_calc("tan(0)")) < 0.001
        assert _safe_calc("log10(100)") == 2.0
        assert abs(_safe_calc("log(1)") < 0.001)
        assert _safe_calc("abs(-5)") == 5
        assert _safe_calc("round(3.7)") == 4
        assert _safe_calc("ceil(3.2)") == 4
        assert _safe_calc("floor(3.7)") == 3

    def test_constants(self):
        import math
        assert abs(_safe_calc("pi") - math.pi) < 0.001
        assert abs(_safe_calc("e") - math.e) < 0.001

    def test_complex(self):
        assert _safe_calc("(2+3)*4") == 20
        assert _safe_calc("2+3*4") == 14
        assert _safe_calc("-5+3") == -2
        assert _safe_calc("+5") == 5
        assert _safe_calc("sqrt(2**4)") == 4.0

    def test_errors(self):
        with pytest.raises(ZeroDivisionError):
            _safe_calc("1/0")
        with pytest.raises((ValueError, SyntaxError)):
            _safe_calc("import os")
        with pytest.raises(ValueError):
            _safe_calc("__import__('os')")
        with pytest.raises((ValueError, SyntaxError)):
            _safe_calc("exec('print(1)')")


class TestCommandsFull:
    @pytest.mark.asyncio
    async def test_qr_no_args(self):
        msg = make_message("/qr")
        await cmd_qr(msg)
        msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_short_no_args(self):
        msg = make_message("/short")
        await cmd_short(msg)
        msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_screenshot_no_args(self):
        msg = make_message("/screenshot")
        await cmd_screenshot(msg)
        msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_exchange_no_args(self):
        msg = make_message("/exchange")
        await cmd_exchange(msg)
        msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_exchange_invalid(self):
        msg = make_message("/exchange abc USD IRR")
        await cmd_exchange(msg)
        msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_stock_no_args(self):
        msg = make_message("/stock")
        await cmd_stock(msg)
        msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_password_default(self):
        msg = make_message("/password")
        await cmd_password(msg)
        msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_password_custom(self):
        msg = make_message("/password 32")
        await cmd_password(msg)
        msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_text2img_no_args(self):
        msg = make_message("/text2img")
        await cmd_text2img(msg)
        msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_calc_no_args(self):
        msg = make_message("/calc")
        await cmd_calc(msg)
        msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_calc_valid(self):
        msg = make_message("/calc 2+2")
        await cmd_calc(msg)
        msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_calc_division_by_zero(self):
        msg = make_message("/calc 1/0")
        await cmd_calc(msg)
        msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_calc_invalid(self):
        msg = make_message("/calc !@#")
        await cmd_calc(msg)
        msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_meme_no_args(self):
        msg = make_message("/meme")
        await cmd_meme(msg)
        msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_invoice(self):
        msg = make_message("/invoice")
        await cmd_invoice(msg)
        msg.answer.assert_called()
        assert 123 in _invoice_state
        _invoice_state.pop(123, None)

    @pytest.mark.asyncio
    async def test_done_no_items(self):
        msg = make_message("/done")
        _invoice_state.pop(123, None)
        await cmd_done(msg)
        msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_done_with_items(self):
        _invoice_state[123] = [("Item", 10000, 2)]
        msg = make_message("/done")
        await cmd_done(msg)
        msg.answer_photo.assert_called()
        _invoice_state.pop(123, None)

    @pytest.mark.asyncio
    async def test_flashcard_no_args(self):
        msg = make_message("/flashcard")
        await cmd_flashcard(msg)
        msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_flashcard_add(self):
        msg = make_message("/flashcard add What? | Answer")
        await cmd_flashcard(msg)
        msg.answer.assert_called()
        _flash_cards.pop(123, None)

    @pytest.mark.asyncio
    async def test_flashcard_add_no_pipe(self):
        msg = make_message("/flashcard add What?")
        await cmd_flashcard(msg)
        msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_flashcard_start(self):
        _flash_cards[123] = [{"q": "Q1", "a": "A1", "score": 0}]
        msg = make_message("/flashcard start")
        await cmd_flashcard(msg)
        msg.answer.assert_called()
        _flash_cards.pop(123, None)
        _flash_idx.pop(123, None)

    @pytest.mark.asyncio
    async def test_flashcard_start_empty(self):
        _flash_cards.pop(123, None)
        msg = make_message("/flashcard start")
        await cmd_flashcard(msg)
        msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_flashcard_next(self):
        _flash_cards[123] = [{"q": "Q1", "a": "A1"}, {"q": "Q2", "a": "A2"}]
        _flash_idx[123] = 0
        msg = make_message("/flashcard next")
        await cmd_flashcard(msg)
        msg.answer.assert_called()
        _flash_cards.pop(123, None)
        _flash_idx.pop(123, None)

    @pytest.mark.asyncio
    async def test_flashcard_next_done(self):
        _flash_cards[123] = [{"q": "Q1", "a": "A1"}]
        _flash_idx[123] = 0
        msg = make_message("/flashcard next")
        await cmd_flashcard(msg)
        msg.answer.assert_called()
        _flash_cards.pop(123, None)
        _flash_idx.pop(123, None)

    @pytest.mark.asyncio
    async def test_flashcard_show(self):
        _flash_cards[123] = [{"q": "Q1", "a": "A1"}]
        _flash_idx[123] = 0
        msg = make_message("/flashcard show")
        await cmd_flashcard(msg)
        msg.answer.assert_called()
        _flash_cards.pop(123, None)
        _flash_idx.pop(123, None)

    @pytest.mark.asyncio
    async def test_flashcard_show_empty(self):
        _flash_cards.pop(123, None)
        msg = make_message("/flashcard show")
        await cmd_flashcard(msg)
        msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_habit_no_args(self):
        msg = make_message("/habit")
        await cmd_habit(msg)
        msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_habit_list(self):
        _habits[123] = {"exercise": 1}
        msg = make_message("/habit list")
        await cmd_habit(msg)
        msg.answer.assert_called()
        _habits.pop(123, None)

    @pytest.mark.asyncio
    async def test_habit_list_empty(self):
        _habits.pop(123, None)
        msg = make_message("/habit list")
        await cmd_habit(msg)
        msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_habit_add(self):
        msg = make_message("/habit add exercise")
        await cmd_habit(msg)
        msg.answer.assert_called()
        _habits.pop(123, None)

    @pytest.mark.asyncio
    async def test_habit_add_empty(self):
        msg = make_message("/habit add")
        await cmd_habit(msg)
        msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_habit_done(self):
        _habits[123] = {"exercise": 0}
        msg = make_message("/habit done exercise")
        await cmd_habit(msg)
        msg.answer.assert_called()
        _habits.pop(123, None)

    @pytest.mark.asyncio
    async def test_habit_done_not_found(self):
        _habits.pop(123, None)
        msg = make_message("/habit done exercise")
        await cmd_habit(msg)
        msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_expense_no_args(self):
        msg = make_message("/expense")
        await cmd_expense(msg)
        msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_expense_list(self):
        _expenses[123] = [(50000, "lunch")]
        msg = make_message("/expense list")
        await cmd_expense(msg)
        msg.answer.assert_called()
        _expenses.pop(123, None)

    @pytest.mark.asyncio
    async def test_expense_list_empty(self):
        _expenses.pop(123, None)
        msg = make_message("/expense list")
        await cmd_expense(msg)
        msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_expense_total(self):
        _expenses[123] = [(50000, "lunch")]
        msg = make_message("/expense total")
        await cmd_expense(msg)
        msg.answer.assert_called()
        _expenses.pop(123, None)

    @pytest.mark.asyncio
    async def test_expense_add(self):
        msg = make_message("/expense 50000 lunch")
        await cmd_expense(msg)
        msg.answer.assert_called()
        _expenses.pop(123, None)

    @pytest.mark.asyncio
    async def test_expense_invalid(self):
        msg = make_message("/expense abc lunch")
        await cmd_expense(msg)
        msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_travel_no_args(self):
        msg = make_message("/travel")
        await cmd_travel(msg)
        msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_recipe_no_args(self):
        msg = make_message("/recipe")
        await cmd_recipe(msg)
        msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_news_no_args(self):
        msg = make_message("/news")
        await cmd_news(msg)
        msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_challenge(self):
        msg = make_message("/challenge")
        await cmd_challenge(msg)
        msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_challenge_error(self):
        msg = make_message("/challenge")
        await cmd_challenge(msg)
        msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_advanced_poll_no_args(self):
        msg = make_message("/advancedpoll")
        await cmd_advanced_poll(msg)
        msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_advanced_poll_no_pipe(self):
        msg = make_message("/advancedpoll Title")
        await cmd_advanced_poll(msg)
        msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_advanced_poll_too_few(self):
        msg = make_message("/advancedpoll Title | A")
        await cmd_advanced_poll(msg)
        msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_advanced_poll_too_many(self):
        opts = ", ".join([f"O{i}" for i in range(15)])
        msg = make_message(f"/advancedpoll Title | {opts}")
        await cmd_advanced_poll(msg)
        msg.answer.assert_called()

    @pytest.mark.asyncio
    async def test_guess(self):
        msg = make_message("/guess")
        await cmd_guess(msg)
        msg.answer.assert_called()
        assert 123 in _guess_games
        _guess_games.pop(123, None)


class TestCallbacksFull:
    @pytest.mark.asyncio
    async def test_flashcard_show_ok(self):
        _flash_cards[123] = [{"q": "Q", "a": "A"}]
        _flash_idx[123] = 0
        call = make_callback("fc:show")
        await cb_flashcard_show(call)
        call.answer.assert_called()
        _flash_cards.pop(123, None)
        _flash_idx.pop(123, None)

    @pytest.mark.asyncio
    async def test_flashcard_show_empty(self):
        call = make_callback("fc:show")
        await cb_flashcard_show(call)
        call.answer.assert_called()

    @pytest.mark.asyncio
    async def test_challenge_done(self):
        call = make_callback("challenge_done")
        await cb_challenge_done(call)
        call.answer.assert_called()

    @pytest.mark.asyncio
    async def test_challenge_next(self):
        call = make_callback("challenge_next")
        with patch("bot.handlers.tools.cmd_challenge", new_callable=AsyncMock):
            await cb_challenge_next(call)
            call.answer.assert_called()

    @pytest.mark.asyncio
    async def test_guess_correct(self):
        _guess_games[123] = {"target": 5, "tries": 0, "max": 7}
        call = make_callback("guess:5")
        await cb_guess_handler(call)
        call.message.edit_text.assert_called()
        _guess_games.pop(123, None)

    @pytest.mark.asyncio
    async def test_guess_wrong(self):
        _guess_games[123] = {"target": 5, "tries": 0, "max": 7}
        call = make_callback("guess:3")
        await cb_guess_handler(call)
        call.answer.assert_called()
        _guess_games.pop(123, None)

    @pytest.mark.asyncio
    async def test_guess_game_over(self):
        _guess_games[123] = {"target": 5, "tries": 7, "max": 7}
        call = make_callback("guess:1")
        await cb_guess_handler(call)
        call.message.edit_text.assert_called()
        _guess_games.pop(123, None)

    @pytest.mark.asyncio
    async def test_guess_no_game(self):
        call = make_callback("guess:5")
        await cb_guess_handler(call)
        call.answer.assert_called()


class TestInvoiceInput:
    @pytest.mark.asyncio
    async def test_valid_input(self):
        _invoice_state[123] = []
        msg = make_message("lunch | 50000 | 2")
        await handle_invoice_input(msg)
        msg.answer.assert_called()
        assert len(_invoice_state[123]) == 1
        _invoice_state.pop(123, None)

    @pytest.mark.asyncio
    async def test_invalid_input(self):
        _invoice_state[123] = []
        msg = make_message("lunch")
        await handle_invoice_input(msg)
        msg.answer.assert_called()
        _invoice_state.pop(123, None)

    @pytest.mark.asyncio
    async def test_invalid_price(self):
        _invoice_state[123] = []
        msg = make_message("lunch | abc")
        await handle_invoice_input(msg)
        msg.answer.assert_called()
        _invoice_state.pop(123, None)

"""Unit tests for bot.handlers.remind."""
import pytest
from datetime import timedelta
from bot.handlers.remind import _parse_time


class TestParseTime:
    def test_seconds(self):
        delta, msg = _parse_time("30s hello")
        assert delta == timedelta(seconds=30)
        assert msg == "hello"

    def test_minutes(self):
        delta, msg = _parse_time("5m drink water")
        assert delta == timedelta(minutes=5)
        assert msg == "drink water"

    def test_hours(self):
        delta, msg = _parse_time("2h meeting")
        assert delta == timedelta(hours=2)
        assert msg == "meeting"

    def test_days(self):
        delta, msg = _parse_time("1d task")
        assert delta == timedelta(days=1)
        assert msg == "task"

    def test_weeks(self):
        delta, msg = _parse_time("1w project")
        assert delta == timedelta(weeks=1)
        assert msg == "project"

    def test_invalid(self):
        delta, msg = _parse_time("invalid")
        assert delta is None

    def test_empty(self):
        delta, msg = _parse_time("")
        assert delta is None

    def test_english_units(self):
        delta, msg = _parse_time("10 sec test")
        assert delta == timedelta(seconds=10)

    def test_minute_full(self):
        delta, msg = _parse_time("3 minute rest")
        assert delta == timedelta(minutes=3)

    def test_hour_full(self):
        delta, msg = _parse_time("1 hour break")
        assert delta == timedelta(hours=1)

    def test_day_full(self):
        delta, msg = _parse_time("2 day deadline")
        assert delta == timedelta(days=2)

    def test_week_full(self):
        delta, msg = _parse_time("1 week review")
        assert delta == timedelta(weeks=1)

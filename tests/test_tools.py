"""Unit tests for bot.handlers.tools — safe calculator and utilities."""
import math
import pytest
from bot.handlers.tools import _safe_calc


class TestSafeCalc:
    def test_basic_add(self):
        assert _safe_calc("2+2") == 4

    def test_basic_sub(self):
        assert _safe_calc("10-3") == 7

    def test_basic_mul(self):
        assert _safe_calc("5*4") == 20

    def test_basic_div(self):
        assert _safe_calc("10/2") == 5.0

    def test_floor_div(self):
        assert _safe_calc("7//2") == 3

    def test_modulo(self):
        assert _safe_calc("10%3") == 1

    def test_power(self):
        assert _safe_calc("2**3") == 8

    def test_sqrt(self):
        assert _safe_calc("sqrt(16)") == 4.0

    def test_sin(self):
        assert abs(_safe_calc("sin(0)")) < 0.001

    def test_cos(self):
        assert abs(_safe_calc("cos(0)") - 1.0) < 0.001

    def test_pi(self):
        assert abs(_safe_calc("pi") - math.pi) < 0.001

    def test_e(self):
        assert abs(_safe_calc("e") - math.e) < 0.001

    def test_complex_expr(self):
        assert _safe_calc("2+3*4") == 14

    def test_parentheses(self):
        assert _safe_calc("(2+3)*4") == 20

    def test_unary_minus(self):
        assert _safe_calc("-5") == -5

    def test_nested_func(self):
        assert _safe_calc("sqrt(2**4)") == 4.0

    def test_division_by_zero(self):
        with pytest.raises(ZeroDivisionError):
            _safe_calc("1/0")

    def test_invalid_func(self):
        with pytest.raises((ValueError, SyntaxError)):
            _safe_calc("import os")

    def test_invalid_name(self):
        with pytest.raises(ValueError):
            _safe_calc("__import__")

    def test_no_builtin(self):
        with pytest.raises(ValueError):
            _safe_calc("exec('print(1)')")


class TestPasswordGeneration:
    def test_length(self):
        import secrets, string
        alphabet = string.ascii_letters + string.digits
        pw = "".join(secrets.choice(alphabet) for _ in range(16))
        assert len(pw) == 16

    def test_has_letters(self):
        import secrets, string
        alphabet = string.ascii_letters + string.digits
        pw = "".join(secrets.choice(alphabet) for _ in range(16))
        assert any(c.isalpha() for c in pw)

    def test_has_digits(self):
        import secrets, string
        alphabet = string.ascii_letters + string.digits
        pw = "".join(secrets.choice(alphabet) for _ in range(16))
        assert any(c.isdigit() for c in pw)


class TestQRCode:
    def test_generate(self):
        import qrcode
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data("https://example.com")
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        assert img is not None

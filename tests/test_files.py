"""Unit tests for bot.handlers.files."""
import pytest
from bot.handlers.files import on_document, _extract_text_from_pdf, _extract_text_from_docx


class TestFilesHandlers:
    def test_on_document_exists(self):
        assert callable(on_document)

    def test_extract_pdf_empty(self):
        result = _extract_text_from_pdf(b"")
        assert result == ""

    def test_extract_docx_empty(self):
        result = _extract_text_from_docx(b"")
        assert result == ""

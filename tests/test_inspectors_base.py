"""Tests for pathlib_gui.inspectors.base — is_text_like (no GUI needed)."""

from __future__ import annotations

from pathlib_gui.inspectors.base import is_text_like


class TestIsTextLike:
    def test_pure_ascii_text(self) -> None:
        assert is_text_like(b"Hello, world! This is plain ASCII text.\n") is True

    def test_valid_utf8(self) -> None:
        assert is_text_like("café résumé naïve".encode()) is True

    def test_empty_bytes_is_true_via_utf8_decode(self) -> None:
        # Empty bytes decodes as valid UTF-8, so is_text_like returns True
        assert is_text_like(b"") is True

    def test_null_bytes_are_valid_utf8_so_text_like(self) -> None:
        # Null bytes decode as valid UTF-8 in Python, so UTF-8 path triggers True
        assert is_text_like(b"\x00\x01\x02\x03" * 20) is True

    def test_mostly_printable(self) -> None:
        data = b"A" * 90 + b"\x00" * 10
        assert is_text_like(data) is True

    def test_non_utf8_mostly_non_printable_returns_false(self) -> None:
        # High bytes that are invalid UTF-8 AND mostly non-printable ASCII
        data = b"\x80\x81\x82\x83\x84\x85\x86\x87\x88\x89" * 30
        assert is_text_like(data) is False

    def test_newlines_and_tabs_are_printable(self) -> None:
        data = b"line1\tcolumn\nline2\rline3\n"
        assert is_text_like(data) is True

    def test_png_magic_bytes(self) -> None:
        # \x89 makes it invalid UTF-8; and mostly non-printable bytes
        png_header = b"\x89PNG\r\n\x1a\n" + b"\x80\x90\xa0\xb0" * 40
        assert is_text_like(png_header) is False

    def test_invalid_utf8_but_mostly_printable_ascii(self) -> None:
        # Invalid UTF-8 but >75% of bytes are printable ASCII
        data = b"\xff" + b"A" * 99
        assert is_text_like(data) is True

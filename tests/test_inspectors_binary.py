"""Tests for pathlib_gui.inspectors.binary — hex_dump (no GUI needed)."""

from __future__ import annotations

from pathlib_gui.inspectors.binary import BYTES_PER_ROW, hex_dump


class TestHexDump:
    def test_empty_bytes_returns_empty(self) -> None:
        assert hex_dump(b"") == ""

    def test_single_byte(self) -> None:
        result = hex_dump(b"\x41")
        assert "41" in result
        assert "A" in result
        assert "00000000" in result

    def test_non_printable_shown_as_dot(self) -> None:
        result = hex_dump(b"\x00")
        assert "." in result
        assert "00" in result

    def test_row_format(self) -> None:
        data = b"ABCDEFGHIJKLMNOP"  # exactly 16 bytes
        result = hex_dump(data)
        lines = result.splitlines()
        assert len(lines) == 1
        assert lines[0].startswith("00000000")
        assert "|ABCDEFGHIJKLMNOP|" in lines[0]

    def test_two_rows(self) -> None:
        data = b"A" * (BYTES_PER_ROW + 1)
        result = hex_dump(data)
        lines = result.splitlines()
        assert len(lines) == 2

    def test_offset_increments(self) -> None:
        data = b"x" * (BYTES_PER_ROW * 3)
        result = hex_dump(data)
        lines = result.splitlines()
        assert lines[0].startswith("00000000")
        assert lines[1].startswith("00000010")
        assert lines[2].startswith("00000020")

    def test_non_printable_shown_as_dot_in_ascii_column(self) -> None:
        # Only non-printable bytes (outside 0x20-0x7E) are shown as '.' in the ASCII column
        data = b"\x00\xff"
        result = hex_dump(data)
        assert "|..|" in result

    def test_printable_ascii_dot_appears_literally(self) -> None:
        # 0x2E is '.' and IS printable, so it appears as '.' literally in the ASCII column
        data = b"."
        result = hex_dump(data)
        assert "|.|" in result

    def test_partial_row_pads_correctly(self) -> None:
        data = b"ABC"
        result = hex_dump(data)
        assert "|ABC|" in result

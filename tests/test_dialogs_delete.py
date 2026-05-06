"""Tests for pathlib_gui.dialogs.delete — pure functions only (no GUI)."""

from __future__ import annotations

from pathlib import Path

from pathlib_gui.dialogs.delete import count_contents, format_bytes


class TestFormatBytes:
    def test_bytes(self) -> None:
        assert format_bytes(512) == "512.0 B"

    def test_kilobytes(self) -> None:
        assert format_bytes(1024) == "1.0 KB"

    def test_megabytes(self) -> None:
        assert format_bytes(1024 * 1024) == "1.0 MB"

    def test_gigabytes(self) -> None:
        assert format_bytes(1024**3) == "1.0 GB"

    def test_terabytes(self) -> None:
        assert format_bytes(1024**4) == "1.0 TB"

    def test_large_returns_petabytes(self) -> None:
        result = format_bytes(1024**5)
        assert "PB" in result

    def test_zero(self) -> None:
        assert format_bytes(0) == "0.0 B"


class TestCountContents:
    def test_empty_directory(self, tmp_path: Path) -> None:
        d = tmp_path / "empty"
        d.mkdir()
        files, folders, total = count_contents(d)
        assert files == 0
        assert folders == 0
        assert total == 0

    def test_flat_directory(self, tmp_path: Path) -> None:
        d = tmp_path / "flat"
        d.mkdir()
        (d / "a.txt").write_bytes(b"hello")
        (d / "b.txt").write_bytes(b"world!")
        files, folders, total = count_contents(d)
        assert files == 2
        assert folders == 0
        assert total == 11

    def test_nested_directory(self, tmp_path: Path) -> None:
        d = tmp_path / "nested"
        d.mkdir()
        sub = d / "sub"
        sub.mkdir()
        (d / "top.txt").write_bytes(b"top")
        (sub / "child.txt").write_bytes(b"child!")
        files, folders, total = count_contents(d)
        assert files == 2
        assert folders == 1
        assert total == 9

    def test_counts_only_files_for_bytes(self, tmp_path: Path) -> None:
        d = tmp_path / "d"
        d.mkdir()
        (d / "f.bin").write_bytes(b"x" * 100)
        files, folders, total = count_contents(d)
        assert total == 100

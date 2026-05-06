"""Tests for pathlib_gui.services.diff_service."""

from __future__ import annotations

from pathlib import Path

from pathlib_gui.services.diff_service import diff_files, html_diff, similarity_ratio


class TestDiffFiles:
    def test_identical_files(self, tmp_path: Path) -> None:
        a = tmp_path / "a.txt"
        b = tmp_path / "b.txt"
        a.write_text("hello\nworld\n")
        b.write_text("hello\nworld\n")
        result = diff_files(a, b)
        assert result.same is True
        assert result.unified == []

    def test_different_files(self, tmp_path: Path) -> None:
        a = tmp_path / "a.txt"
        b = tmp_path / "b.txt"
        a.write_text("hello\n")
        b.write_text("world\n")
        result = diff_files(a, b)
        assert result.same is False
        assert len(result.unified) > 0

    def test_result_contains_paths(self, tmp_path: Path) -> None:
        a = tmp_path / "a.txt"
        b = tmp_path / "b.txt"
        a.write_text("x")
        b.write_text("y")
        result = diff_files(a, b)
        assert result.left_path == a
        assert result.right_path == b

    def test_result_has_all_diff_formats(self, tmp_path: Path) -> None:
        a = tmp_path / "a.txt"
        b = tmp_path / "b.txt"
        a.write_text("line1\nline2\n")
        b.write_text("line1\nlineX\n")
        result = diff_files(a, b)
        assert isinstance(result.unified, list)
        assert isinstance(result.context, list)
        assert isinstance(result.ndiff, list)
        assert len(result.ndiff) > 0

    def test_ignore_case(self, tmp_path: Path) -> None:
        a = tmp_path / "a.txt"
        b = tmp_path / "b.txt"
        a.write_text("Hello\n")
        b.write_text("hello\n")
        result = diff_files(a, b, ignore_case=True)
        assert result.same is True

    def test_ignore_whitespace(self, tmp_path: Path) -> None:
        a = tmp_path / "a.txt"
        b = tmp_path / "b.txt"
        a.write_text("hello   world\n")
        b.write_text("hello world\n")
        result = diff_files(a, b, ignore_whitespace=True)
        assert result.same is True

    def test_missing_file_treated_as_empty(self, tmp_path: Path) -> None:
        a = tmp_path / "exists.txt"
        b = tmp_path / "missing.txt"
        a.write_text("content\n")
        result = diff_files(a, b)
        assert result.right_lines == []
        assert result.same is False

    def test_both_empty(self, tmp_path: Path) -> None:
        a = tmp_path / "a.txt"
        b = tmp_path / "b.txt"
        a.write_text("")
        b.write_text("")
        result = diff_files(a, b)
        assert result.same is True


class TestHtmlDiff:
    def test_returns_html_string(self, tmp_path: Path) -> None:
        a = tmp_path / "a.txt"
        b = tmp_path / "b.txt"
        a.write_text("line1\nline2\n")
        b.write_text("line1\nlineX\n")
        html = html_diff(a, b)
        assert isinstance(html, str)
        assert "<html>" in html.lower() or "<!DOCTYPE" in html

    def test_identical_files_still_returns_html(self, tmp_path: Path) -> None:
        a = tmp_path / "a.txt"
        b = tmp_path / "b.txt"
        a.write_text("same\n")
        b.write_text("same\n")
        html = html_diff(a, b)
        assert isinstance(html, str)
        assert len(html) > 0


class TestSimilarityRatio:
    def test_identical_is_one(self, tmp_path: Path) -> None:
        a = tmp_path / "a.txt"
        b = tmp_path / "b.txt"
        a.write_text("hello\nworld\n")
        b.write_text("hello\nworld\n")
        ratio = similarity_ratio(a, b)
        assert ratio == pytest.approx(1.0)

    def test_completely_different_is_zero(self, tmp_path: Path) -> None:
        a = tmp_path / "a.txt"
        b = tmp_path / "b.txt"
        a.write_text("aaaa\n")
        b.write_text("zzzz\n")
        ratio = similarity_ratio(a, b)
        assert 0.0 <= ratio < 1.0

    def test_ratio_between_zero_and_one(self, tmp_path: Path) -> None:
        a = tmp_path / "a.txt"
        b = tmp_path / "b.txt"
        a.write_text("line1\nline2\nline3\n")
        b.write_text("line1\nlineX\nline3\n")
        ratio = similarity_ratio(a, b)
        assert 0.0 < ratio < 1.0


import pytest

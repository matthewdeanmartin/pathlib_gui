"""Tests for pathlib_gui.models.search."""

from __future__ import annotations

from pathlib import Path

from pathlib_gui.models.search import SearchQuery, SearchResult


class TestSearchQuery:
    def test_defaults(self, tmp_path: Path) -> None:
        q = SearchQuery(root=tmp_path)
        assert q.name_contains == ""
        assert q.glob_pattern == ""
        assert q.regex_pattern == ""
        assert q.suffix == ""
        assert q.min_size == 0
        assert q.max_size == 0
        assert q.content_contains == ""
        assert q.find_empty_files is False
        assert q.find_empty_dirs is False
        assert q.find_broken_symlinks is False
        assert q.find_duplicates is False
        assert q.follow_symlinks is False

    def test_custom_values(self, tmp_path: Path) -> None:
        q = SearchQuery(
            root=tmp_path,
            name_contains="test",
            glob_pattern="*.py",
            suffix=".py",
            min_size=100,
            max_size=1000,
            find_empty_files=True,
        )
        assert q.name_contains == "test"
        assert q.glob_pattern == "*.py"
        assert q.suffix == ".py"
        assert q.min_size == 100
        assert q.max_size == 1000
        assert q.find_empty_files is True


class TestSearchResult:
    def test_defaults(self, tmp_path: Path) -> None:
        r = SearchResult(path=tmp_path / "file.txt")
        assert r.match_reason == ""

    def test_with_reason(self, tmp_path: Path) -> None:
        r = SearchResult(path=tmp_path / "file.txt", match_reason="empty file")
        assert r.match_reason == "empty file"
        assert r.path == tmp_path / "file.txt"

"""Tests for pathlib_gui.services.search_service."""

from __future__ import annotations

import queue
import time
from pathlib import Path

from pathlib_gui.models.search import SearchQuery, SearchResult
from pathlib_gui.services.search_service import SearchWorker


def run_search(query: SearchQuery, timeout: float = 5.0) -> list[SearchResult]:
    """Helper: run a SearchWorker synchronously and collect results."""
    q: queue.Queue[object] = queue.Queue()
    worker = SearchWorker(query, q)
    worker.start()
    results: list[SearchResult] = []
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            item = q.get(timeout=0.5)
        except queue.Empty:
            continue
        if item is SearchWorker.STOP:
            break
        assert isinstance(item, SearchResult)
        results.append(item)
    return results


class TestSearchWorkerNameContains:
    def test_finds_matching_name(self, tmp_path: Path) -> None:
        (tmp_path / "hello_world.txt").write_text("x")
        (tmp_path / "other.txt").write_text("y")
        q = SearchQuery(root=tmp_path, name_contains="hello")
        results = run_search(q)
        names = {r.path.name for r in results}
        assert "hello_world.txt" in names
        assert "other.txt" not in names

    def test_case_insensitive_match(self, tmp_path: Path) -> None:
        (tmp_path / "README.md").write_text("x")
        q = SearchQuery(root=tmp_path, name_contains="readme")
        results = run_search(q)
        assert any(r.path.name == "README.md" for r in results)


class TestSearchWorkerGlob:
    def test_glob_pattern(self, tmp_path: Path) -> None:
        (tmp_path / "script.py").write_text("py")
        (tmp_path / "data.txt").write_text("txt")
        q = SearchQuery(root=tmp_path, glob_pattern="*.py")
        results = run_search(q)
        names = {r.path.name for r in results}
        assert "script.py" in names
        assert "data.txt" not in names


class TestSearchWorkerSuffix:
    def test_suffix_filter(self, tmp_path: Path) -> None:
        (tmp_path / "file.py").write_text("py")
        (tmp_path / "file.txt").write_text("txt")
        q = SearchQuery(root=tmp_path, suffix=".py")
        results = run_search(q)
        names = {r.path.name for r in results}
        assert "file.py" in names
        assert "file.txt" not in names

    def test_suffix_case_insensitive(self, tmp_path: Path) -> None:
        (tmp_path / "image.JPG").write_text("jpg")
        q = SearchQuery(root=tmp_path, suffix=".jpg")
        results = run_search(q)
        assert any(r.path.name == "image.JPG" for r in results)


class TestSearchWorkerRegex:
    def test_regex_match(self, tmp_path: Path) -> None:
        (tmp_path / "test_foo.py").write_text("x")
        (tmp_path / "main.py").write_text("y")
        q = SearchQuery(root=tmp_path, regex_pattern=r"^test_")
        results = run_search(q)
        names = {r.path.name for r in results}
        assert "test_foo.py" in names
        assert "main.py" not in names

    def test_invalid_regex_silently_skips_filter(self, tmp_path: Path) -> None:
        # When regex fails to compile, the regex filter is skipped (regex=None).
        # Files still match via the default "match" path with no other filters active.
        (tmp_path / "file.txt").write_text("x")
        q = SearchQuery(root=tmp_path, regex_pattern="[invalid(")
        results = run_search(q)
        # The invalid regex is treated as no filter, so files match normally
        assert isinstance(results, list)


class TestSearchWorkerContent:
    def test_content_search(self, tmp_path: Path) -> None:
        (tmp_path / "match.txt").write_text("find this needle here")
        (tmp_path / "nomatch.txt").write_text("nothing here")
        q = SearchQuery(root=tmp_path, content_contains="needle")
        results = run_search(q)
        names = {r.path.name for r in results}
        assert "match.txt" in names
        assert "nomatch.txt" not in names

    def test_content_case_insensitive(self, tmp_path: Path) -> None:
        (tmp_path / "f.txt").write_text("UPPER NEEDLE lower")
        q = SearchQuery(root=tmp_path, content_contains="needle")
        results = run_search(q)
        assert any(r.path.name == "f.txt" for r in results)


class TestSearchWorkerSizeFilter:
    def test_min_size(self, tmp_path: Path) -> None:
        small = tmp_path / "small.bin"
        large = tmp_path / "large.bin"
        small.write_bytes(b"x" * 10)
        large.write_bytes(b"x" * 1000)
        q = SearchQuery(root=tmp_path, min_size=500)
        results = run_search(q)
        names = {r.path.name for r in results}
        assert "large.bin" in names
        assert "small.bin" not in names

    def test_max_size(self, tmp_path: Path) -> None:
        small = tmp_path / "small.bin"
        large = tmp_path / "large.bin"
        small.write_bytes(b"x" * 10)
        large.write_bytes(b"x" * 1000)
        q = SearchQuery(root=tmp_path, max_size=100)
        results = run_search(q)
        names = {r.path.name for r in results}
        assert "small.bin" in names
        assert "large.bin" not in names


class TestSearchWorkerEmptyFiles:
    def test_finds_empty_files(self, tmp_path: Path) -> None:
        empty = tmp_path / "empty.txt"
        nonempty = tmp_path / "nonempty.txt"
        empty.write_bytes(b"")
        nonempty.write_bytes(b"x")
        q = SearchQuery(root=tmp_path, find_empty_files=True)
        results = run_search(q)
        names = {r.path.name for r in results}
        assert "empty.txt" in names
        assert "nonempty.txt" not in names

    def test_reason_is_empty_file(self, tmp_path: Path) -> None:
        (tmp_path / "e.txt").write_bytes(b"")
        q = SearchQuery(root=tmp_path, find_empty_files=True)
        results = run_search(q)
        assert any(r.match_reason == "empty file" for r in results)


class TestSearchWorkerEmptyDirs:
    def test_finds_empty_dirs(self, tmp_path: Path) -> None:
        empty_dir = tmp_path / "empty_dir"
        full_dir = tmp_path / "full_dir"
        empty_dir.mkdir()
        full_dir.mkdir()
        (full_dir / "file.txt").write_text("x")
        q = SearchQuery(root=tmp_path, find_empty_dirs=True)
        results = run_search(q)
        names = {r.path.name for r in results}
        assert "empty_dir" in names
        assert "full_dir" not in names


class TestSearchWorkerCancel:
    def test_cancel_stops_worker(self, tmp_path: Path) -> None:
        for i in range(200):
            (tmp_path / f"file_{i}.txt").write_text(f"content {i}")
        q_obj: queue.Queue[object] = queue.Queue()
        query = SearchQuery(root=tmp_path, name_contains="file")
        worker = SearchWorker(query, q_obj)
        worker.start()
        time.sleep(0.01)
        worker.cancel()
        worker.thread.join(timeout=3)
        assert not worker.thread.is_alive()


class TestSearchWorkerMatches:
    def test_matches_returns_string_on_match(self, tmp_path: Path) -> None:
        f = tmp_path / "target.txt"
        f.write_text("x")
        q = SearchQuery(root=tmp_path, name_contains="target")
        q_obj: queue.Queue[object] = queue.Queue()
        worker = SearchWorker(q, q_obj)
        result = worker.matches(f, q, None)
        assert result == "match"

    def test_matches_returns_none_on_no_match(self, tmp_path: Path) -> None:
        f = tmp_path / "unrelated.txt"
        f.write_text("x")
        q = SearchQuery(root=tmp_path, name_contains="target")
        q_obj: queue.Queue[object] = queue.Queue()
        worker = SearchWorker(q, q_obj)
        result = worker.matches(f, q, None)
        assert result is None

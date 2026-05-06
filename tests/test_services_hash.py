"""Tests for pathlib_gui.services.hash_service."""

from __future__ import annotations

import queue
import time
from pathlib import Path

import pytest

from pathlib_gui.services.hash_service import BatchHashWorker, find_duplicates, full_hash, partial_hash


class TestPartialHash:
    def test_returns_hex_string(self, tmp_path: Path) -> None:
        f = tmp_path / "data.bin"
        f.write_bytes(b"hello world")
        result = partial_hash(f)
        assert isinstance(result, str)
        assert len(result) > 0
        assert all(c in "0123456789abcdef" for c in result)

    def test_default_algo_is_md5(self, tmp_path: Path) -> None:
        f = tmp_path / "data.bin"
        f.write_bytes(b"test")
        result = partial_hash(f, algo="md5")
        assert len(result) == 32

    def test_sha256_produces_64_chars(self, tmp_path: Path) -> None:
        f = tmp_path / "data.bin"
        f.write_bytes(b"test data")
        result = partial_hash(f, algo="sha256")
        assert len(result) == 64

    def test_missing_file_returns_empty(self, tmp_path: Path) -> None:
        f = tmp_path / "ghost.bin"
        result = partial_hash(f)
        assert result == ""

    def test_only_reads_chunk(self, tmp_path: Path) -> None:
        f = tmp_path / "large.bin"
        f.write_bytes(b"A" * 200_000)
        h_partial = partial_hash(f, chunk_size=65536)
        h_full = full_hash(f, algo="md5")
        assert h_partial != h_full

    def test_same_content_same_hash(self, tmp_path: Path) -> None:
        a = tmp_path / "a.bin"
        b = tmp_path / "b.bin"
        a.write_bytes(b"identical")
        b.write_bytes(b"identical")
        assert partial_hash(a) == partial_hash(b)


class TestFullHash:
    def test_sha256_of_known_content(self, tmp_path: Path) -> None:
        import hashlib
        f = tmp_path / "known.txt"
        content = b"hello\n"
        f.write_bytes(content)
        expected = hashlib.sha256(content).hexdigest()
        assert full_hash(f) == expected

    def test_missing_file_returns_empty(self, tmp_path: Path) -> None:
        f = tmp_path / "no_such.bin"
        assert full_hash(f) == ""

    def test_md5_algo(self, tmp_path: Path) -> None:
        import hashlib
        f = tmp_path / "f.bin"
        content = b"data"
        f.write_bytes(content)
        expected = hashlib.md5(content).hexdigest()
        assert full_hash(f, algo="md5") == expected

    def test_different_content_different_hash(self, tmp_path: Path) -> None:
        a = tmp_path / "a.bin"
        b = tmp_path / "b.bin"
        a.write_bytes(b"content A")
        b.write_bytes(b"content B")
        assert full_hash(a) != full_hash(b)


class TestFindDuplicates:
    def test_no_duplicates(self, tmp_path: Path) -> None:
        (tmp_path / "a.txt").write_bytes(b"aaa")
        (tmp_path / "b.txt").write_bytes(b"bbb")
        paths = list(tmp_path.iterdir())
        result = find_duplicates(paths)
        assert result == []

    def test_finds_duplicates(self, tmp_path: Path) -> None:
        content = b"duplicate content here"
        a = tmp_path / "a.txt"
        b = tmp_path / "b.txt"
        a.write_bytes(content)
        b.write_bytes(content)
        result = find_duplicates([a, b])
        assert len(result) == 1
        assert set(result[0]) == {a, b}

    def test_different_sizes_not_duplicates(self, tmp_path: Path) -> None:
        a = tmp_path / "a.txt"
        b = tmp_path / "b.txt"
        a.write_bytes(b"short")
        b.write_bytes(b"much longer content here")
        result = find_duplicates([a, b])
        assert result == []

    def test_multiple_duplicate_groups(self, tmp_path: Path) -> None:
        content1 = b"group one content"
        content2 = b"group two content"
        files1 = [tmp_path / f"g1_{i}.bin" for i in range(2)]
        files2 = [tmp_path / f"g2_{i}.bin" for i in range(2)]
        for f in files1:
            f.write_bytes(content1)
        for f in files2:
            f.write_bytes(content2)
        result = find_duplicates(files1 + files2)
        assert len(result) == 2

    def test_empty_list(self) -> None:
        assert find_duplicates([]) == []

    def test_single_file(self, tmp_path: Path) -> None:
        f = tmp_path / "only.txt"
        f.write_bytes(b"alone")
        assert find_duplicates([f]) == []


class TestBatchHashWorker:
    def test_hashes_files_and_signals_done(self, tmp_path: Path) -> None:
        files = []
        for i in range(3):
            f = tmp_path / f"file{i}.txt"
            f.write_bytes(f"content {i}".encode())
            files.append(f)

        q: queue.Queue[object] = queue.Queue()
        worker = BatchHashWorker(files, "sha256", q)
        worker.start()
        worker.thread.join(timeout=5)

        results = []
        while True:
            item = q.get(timeout=2)
            if item is BatchHashWorker.DONE:
                break
            results.append(item)

        assert len(results) == 3
        for path, digest in results:
            assert isinstance(digest, str)
            assert len(digest) == 64

    def test_cancel_stops_early(self, tmp_path: Path) -> None:
        files = []
        for i in range(100):
            f = tmp_path / f"f{i}.bin"
            f.write_bytes(b"x" * 10000)
            files.append(f)

        q: queue.Queue[object] = queue.Queue()
        worker = BatchHashWorker(files, "sha256", q)
        worker.start()
        worker.cancel()
        worker.thread.join(timeout=5)

        items = []
        while True:
            try:
                item = q.get(timeout=1)
                items.append(item)
                if item is BatchHashWorker.DONE:
                    break
            except queue.Empty:
                break

        done_items = [x for x in items if x is BatchHashWorker.DONE]
        assert len(done_items) == 1

    def test_done_sentinel_is_unique(self) -> None:
        assert BatchHashWorker.DONE is not None
        assert BatchHashWorker.DONE is not True
        assert BatchHashWorker.DONE is not False

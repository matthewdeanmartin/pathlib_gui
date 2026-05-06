"""Threaded hash service for batch operations and duplicate finder."""

from __future__ import annotations

import hashlib
import queue
import threading
from contextlib import suppress
from pathlib import Path


def partial_hash(path: Path, algo: str = "md5", chunk_size: int = 65536) -> str:
    h = hashlib.new(algo)
    try:
        with path.open("rb") as fh:
            h.update(fh.read(chunk_size))
    except OSError:
        return ""
    return h.hexdigest()


def full_hash(path: Path, algo: str = "sha256") -> str:
    h = hashlib.new(algo)
    try:
        with path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk)
    except OSError:
        return ""
    return h.hexdigest()


def find_duplicates(paths: list[Path]) -> list[list[Path]]:
    """Staged duplicate detection: size → partial hash → full hash."""
    from collections import defaultdict

    by_size: dict[int, list[Path]] = defaultdict(list)
    for p in paths:
        with suppress(OSError):
            by_size[p.stat().st_size].append(p)

    candidates = [group for group in by_size.values() if len(group) > 1]

    by_partial: dict[str, list[Path]] = defaultdict(list)
    for group in candidates:
        for p in group:
            h = partial_hash(p)
            if h:
                by_partial[h].append(p)

    candidates2 = [g for g in by_partial.values() if len(g) > 1]

    by_full: dict[str, list[Path]] = defaultdict(list)
    for group in candidates2:
        for p in group:
            h = full_hash(p)
            if h:
                by_full[h].append(p)

    return [g for g in by_full.values() if len(g) > 1]


class BatchHashWorker:
    """Hash a list of files in a background thread."""

    DONE = object()

    def __init__(self, paths: list[Path], algo: str, result_queue: queue.Queue[object]) -> None:
        self.paths = paths
        self.algo = algo
        self.result_queue = result_queue
        self.cancel_event = threading.Event()
        self.thread = threading.Thread(target=self.run, daemon=True)

    def start(self) -> None:
        self.thread.start()

    def cancel(self) -> None:
        self.cancel_event.set()

    def run(self) -> None:
        for path in self.paths:
            if self.cancel_event.is_set():
                break
            digest = full_hash(path, self.algo)
            self.result_queue.put((path, digest))
        self.result_queue.put(self.DONE)

"""Threaded filesystem search service."""

from __future__ import annotations

import fnmatch
import mimetypes
import queue
import re
import threading
from pathlib import Path

from pathlib_gui.models.search import SearchQuery, SearchResult


class SearchWorker:
    """Runs a search in a background thread, posting results to a queue."""

    STOP = object()

    def __init__(self, query: SearchQuery, result_queue: queue.Queue[object]) -> None:
        self.query = query
        self.result_queue = result_queue
        self.cancel_event = threading.Event()
        self.thread = threading.Thread(target=self.run, daemon=True)

    def start(self) -> None:
        self.thread.start()

    def cancel(self) -> None:
        self.cancel_event.set()

    def run(self) -> None:
        q = self.query
        regex: re.Pattern[str] | None = None
        if q.regex_pattern:
            try:
                regex = re.compile(q.regex_pattern)
            except re.error:
                pass

        try:
            for path in q.root.rglob("*"):
                if self.cancel_event.is_set():
                    break
                reason = self.matches(path, q, regex)
                if reason is not None:
                    self.result_queue.put(SearchResult(path=path, match_reason=reason))
        except PermissionError:
            pass
        finally:
            self.result_queue.put(self.STOP)

    def matches(self, path: Path, q: SearchQuery, regex: re.Pattern[str] | None) -> str | None:
        name = path.name

        if q.find_broken_symlinks:
            if path.is_symlink() and not path.exists():
                return "broken symlink"
            return None

        if q.find_empty_files:
            if path.is_file():
                try:
                    if path.stat().st_size == 0:
                        return "empty file"
                except OSError:
                    pass
            return None

        if q.find_empty_dirs:
            if path.is_dir():
                try:
                    if not any(path.iterdir()):
                        return "empty folder"
                except PermissionError:
                    pass
            return None

        # File-type filter
        if q.file_type == "file" and not path.is_file():
            return None
        if q.file_type == "directory" and not path.is_dir():
            return None
        if q.file_type == "symlink" and not path.is_symlink():
            return None

        if q.glob_pattern and not fnmatch.fnmatch(name, q.glob_pattern):
            return None

        if q.name_contains and q.name_contains.lower() not in name.lower():
            return None

        if q.suffix and path.suffix.lower() != q.suffix.lower():
            return None

        if regex and not regex.search(name):
            return None

        if q.min_size or q.max_size:
            if not path.is_file():
                return None
            try:
                size = path.stat().st_size
            except OSError:
                return None
            if q.min_size and size < q.min_size:
                return None
            if q.max_size and size > q.max_size:
                return None

        # Date-range filter
        if q.modified_after or q.modified_before:
            try:
                mtime = path.stat().st_mtime
            except OSError:
                return None
            if q.modified_after and mtime < q.modified_after:
                return None
            if q.modified_before and mtime > q.modified_before:
                return None

        # MIME-type filter
        if q.mime_contains:
            mime, _ = mimetypes.guess_type(name)
            if not mime or q.mime_contains.lower() not in mime.lower():
                return None

        if q.content_contains:
            if not path.is_file():
                return None
            try:
                text = path.read_text(errors="replace")
                if q.content_contains.lower() not in text.lower():
                    return None
            except OSError:
                return None
            return f"content match: {q.content_contains!r}"

        return "match"

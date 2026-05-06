"""Filesystem search panel — threaded, cancellable."""

from __future__ import annotations

import datetime
import queue
import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from tkinter import ttk
from typing import Any

from pathlib_gui.models.search import SearchQuery, SearchResult
from pathlib_gui.services.search_service import SearchWorker

FILE_TYPES = ["any", "file", "directory", "symlink"]


def _parse_date(s: str) -> float:
    """Parse YYYY-MM-DD to a Unix timestamp, or return 0.0 on failure."""
    s = s.strip()
    if not s:
        return 0.0
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y"):
        try:
            return datetime.datetime.strptime(s, fmt).timestamp()
        except ValueError:
            continue
    return 0.0


class SearchView(ttk.Frame):
    """Search criteria form + results list."""

    def __init__(
        self,
        parent: tk.Misc,
        on_navigate: Callable[[Path], None] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(parent, **kwargs)
        self.on_navigate = on_navigate
        self.worker: SearchWorker | None = None
        self.result_queue: queue.Queue[object] = queue.Queue()
        self.results: list[SearchResult] = []
        self.build_widgets()

    def build_widgets(self) -> None:
        ttk.Label(
            self,
            text="Search  —  Backend: pathlib.rglob / re / fnmatch / mimetypes",
            foreground="gray",
        ).pack(anchor="w", padx=6, pady=(4, 2))

        criteria = ttk.LabelFrame(self, text="Criteria", padding=6)
        criteria.pack(fill=tk.X, padx=6, pady=4)

        self.root_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.glob_var = tk.StringVar()
        self.regex_var = tk.StringVar()
        self.suffix_var = tk.StringVar()
        self.content_var = tk.StringVar()
        self.min_size_var = tk.StringVar()
        self.max_size_var = tk.StringVar()
        self.modified_after_var = tk.StringVar()
        self.modified_before_var = tk.StringVar()
        self.mime_var = tk.StringVar()
        self.file_type_var = tk.StringVar(value="any")
        self.empty_files_var = tk.BooleanVar()
        self.empty_dirs_var = tk.BooleanVar()
        self.broken_links_var = tk.BooleanVar()

        text_rows = [
            ("Search in:", self.root_var, None),
            ("Name contains:", self.name_var, None),
            ("Glob pattern:", self.glob_var, "e.g. *.py"),
            ("Regex pattern:", self.regex_var, "e.g. test_.*\\.py"),
            ("Extension:", self.suffix_var, "e.g. .txt"),
            ("Content contains:", self.content_var, None),
            ("Min size (bytes):", self.min_size_var, None),
            ("Max size (bytes):", self.max_size_var, None),
            ("Modified after:", self.modified_after_var, "YYYY-MM-DD"),
            ("Modified before:", self.modified_before_var, "YYYY-MM-DD"),
            ("MIME type contains:", self.mime_var, "e.g. image, text/plain"),
        ]
        for i, (label, var, hint) in enumerate(text_rows):
            ttk.Label(criteria, text=label).grid(row=i, column=0, sticky="e", padx=4, pady=2)
            entry = ttk.Entry(criteria, textvariable=var, width=36)
            entry.grid(row=i, column=1, sticky="w", padx=2)
            if hint:
                ttk.Label(criteria, text=hint, foreground="gray").grid(row=i, column=2, sticky="w", padx=4)

        next_row = len(text_rows)

        ttk.Label(criteria, text="File type:").grid(row=next_row, column=0, sticky="e", padx=4, pady=2)
        type_combo = ttk.Combobox(
            criteria, textvariable=self.file_type_var, values=FILE_TYPES, state="readonly", width=14
        )
        type_combo.grid(row=next_row, column=1, sticky="w", padx=2)

        checks = ttk.Frame(criteria)
        checks.grid(row=next_row + 1, column=0, columnspan=3, sticky="w", pady=4)
        ttk.Checkbutton(checks, text="Empty files", variable=self.empty_files_var).pack(side=tk.LEFT, padx=4)
        ttk.Checkbutton(checks, text="Empty folders", variable=self.empty_dirs_var).pack(side=tk.LEFT, padx=4)
        ttk.Checkbutton(checks, text="Broken symlinks", variable=self.broken_links_var).pack(side=tk.LEFT, padx=4)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=6, pady=2)
        self.search_btn = ttk.Button(btn_frame, text="Search", command=self.start_search)
        self.search_btn.pack(side=tk.LEFT, padx=2)
        self.stop_btn = ttk.Button(btn_frame, text="Stop", command=self.stop_search, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=2)
        self.count_label = ttk.Label(btn_frame, text="", foreground="gray")
        self.count_label.pack(side=tk.LEFT, padx=8)

        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=6)
        self.tree = ttk.Treeview(
            tree_frame,
            columns=("path", "reason"),
            show="headings",
            selectmode="browse",
        )
        self.tree.heading("path", text="Path")
        self.tree.heading("reason", text="Match reason")
        self.tree.column("path", width=440)
        self.tree.column("reason", width=160)
        vsb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.bind("<Double-1>", self.navigate_to_result)
        self.tree.bind("<Return>", self.navigate_to_result)

    def set_root(self, path: Path) -> None:
        self.root_var.set(str(path))

    def start_search(self) -> None:
        root_str = self.root_var.get().strip()
        if not root_str:
            return
        root = Path(root_str)
        if not root.is_dir():
            return

        self.tree.delete(*self.tree.get_children())
        self.results = []
        self.count_label.configure(text="Searching...")
        self.search_btn.configure(state=tk.DISABLED)
        self.stop_btn.configure(state=tk.NORMAL)

        self.result_queue = queue.Queue()
        try:
            min_size = int(self.min_size_var.get() or 0)
            max_size = int(self.max_size_var.get() or 0)
        except ValueError:
            min_size = max_size = 0

        query = SearchQuery(
            root=root,
            name_contains=self.name_var.get().strip(),
            glob_pattern=self.glob_var.get().strip(),
            regex_pattern=self.regex_var.get().strip(),
            suffix=self.suffix_var.get().strip(),
            content_contains=self.content_var.get().strip(),
            min_size=min_size,
            max_size=max_size,
            find_empty_files=self.empty_files_var.get(),
            find_empty_dirs=self.empty_dirs_var.get(),
            find_broken_symlinks=self.broken_links_var.get(),
            modified_after=_parse_date(self.modified_after_var.get()),
            modified_before=_parse_date(self.modified_before_var.get()),
            file_type=self.file_type_var.get(),
            mime_contains=self.mime_var.get().strip(),
        )
        self.worker = SearchWorker(query, self.result_queue)
        self.worker.start()
        self.after(100, self.poll_results)

    def stop_search(self) -> None:
        if self.worker:
            self.worker.cancel()

    def poll_results(self) -> None:
        batch = 0
        while batch < 50:
            try:
                item = self.result_queue.get_nowait()
            except queue.Empty:
                break
            if item is SearchWorker.STOP:
                self.search_btn.configure(state=tk.NORMAL)
                self.stop_btn.configure(state=tk.DISABLED)
                self.count_label.configure(text=f"{len(self.results)} result(s)")
                return
            if isinstance(item, SearchResult):
                self.results.append(item)
                self.tree.insert("", tk.END, values=(str(item.path), item.match_reason))
            batch += 1
        self.count_label.configure(text=f"{len(self.results)} so far…")
        self.after(100, self.poll_results)

    def navigate_to_result(self, event: tk.Event) -> None:
        sel = self.tree.selection()
        if not sel or not self.on_navigate:
            return
        values = self.tree.item(sel[0], "values")
        if values:
            p = Path(values[0])
            dest = p.parent if p.is_file() else p
            self.on_navigate(dest)

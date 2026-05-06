"""Duplicate file finder widget."""

from __future__ import annotations

import threading
import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Any

from pathlib_gui.dialogs.delete import confirm_delete
from pathlib_gui.services.filesystem import send2trash_available
from pathlib_gui.services.hash_service import find_duplicates


class DuplicateFinderView(ttk.Frame):
    """Finds and displays duplicate files using staged hash comparison."""

    def __init__(
        self,
        parent: tk.Misc,
        on_navigate: Callable[[Path], None] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(parent, **kwargs)
        self.on_navigate = on_navigate
        self.groups: list[list[Path]] = []
        self.build_widgets()

    def build_widgets(self) -> None:
        ttk.Label(
            self,
            text="Duplicate Finder  —  Backend: hashlib (size → partial hash → full hash)",
            foreground="gray",
        ).pack(anchor="w", padx=6, pady=(4, 2))

        top = ttk.Frame(self)
        top.pack(fill=tk.X, padx=6, pady=4)
        ttk.Label(top, text="Scan folder:").pack(side=tk.LEFT)
        self.root_var = tk.StringVar()
        ttk.Entry(top, textvariable=self.root_var, width=44).pack(side=tk.LEFT, padx=4)
        self.scan_btn = ttk.Button(top, text="Scan", command=self.start_scan)
        self.scan_btn.pack(side=tk.LEFT)
        self.status_label = ttk.Label(top, text="", foreground="gray")
        self.status_label.pack(side=tk.LEFT, padx=8)

        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)

        self.tree = ttk.Treeview(tree_frame, columns=("path", "size"), show="tree headings", selectmode="extended")
        self.tree.heading("path", text="Path")
        self.tree.heading("size", text="Size")
        self.tree.column("#0", width=100)
        self.tree.column("path", width=380)
        self.tree.column("size", width=90)
        vsb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        action_frame = ttk.Frame(self)
        action_frame.pack(fill=tk.X, padx=6, pady=4)
        ttk.Button(action_frame, text="Open folder", command=self.action_open_folder).pack(side=tk.LEFT, padx=2)
        ttk.Button(action_frame, text="Keep newest (delete others)", command=self.action_keep_newest).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(action_frame, text="Keep oldest (delete others)", command=self.action_keep_oldest).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(action_frame, text="Keep shortest path", command=self.action_keep_shortest).pack(
            side=tk.LEFT, padx=2
        )
        if send2trash_available():
            ttk.Button(action_frame, text="Trash selected", command=self.action_trash).pack(side=tk.RIGHT, padx=2)
        ttk.Button(action_frame, text="Delete selected permanently", command=self.action_delete).pack(
            side=tk.RIGHT, padx=2
        )

    def set_root(self, path: Path) -> None:
        self.root_var.set(str(path))

    def start_scan(self) -> None:
        root_str = self.root_var.get().strip()
        if not root_str:
            return
        root = Path(root_str)
        if not root.is_dir():
            return
        self.scan_btn.configure(state=tk.DISABLED)
        self.status_label.configure(text="Scanning…")
        self.tree.delete(*self.tree.get_children())
        self.groups = []
        result_holder: list[list[list[Path]]] = []

        def worker() -> None:
            all_files = [p for p in root.rglob("*") if p.is_file()]
            groups = find_duplicates(all_files)
            result_holder.append(groups)

        def after_scan() -> None:
            if result_holder:
                self.groups = result_holder[0]
                self.render_groups()
            self.scan_btn.configure(state=tk.NORMAL)

        def thread_body() -> None:
            worker()
            self.after(0, after_scan)

        threading.Thread(target=thread_body, daemon=True).start()

    def render_groups(self) -> None:
        self.tree.delete(*self.tree.get_children())
        from pathlib_gui.models.paths import format_size

        for i, group in enumerate(self.groups):
            size = group[0].stat().st_size if group else 0
            label = f"Group {i + 1}  ({len(group)} files, {format_size(size)} each)"
            group_node = self.tree.insert("", tk.END, text=label, values=("", ""), open=True)
            for p in group:
                self.tree.insert(group_node, tk.END, text="", values=(str(p), format_size(size)))
        self.status_label.configure(text=f"{len(self.groups)} duplicate group(s)")

    def selected_paths(self) -> list[Path]:
        paths: list[Path] = []
        for iid in self.tree.selection():
            vals = self.tree.item(iid, "values")
            if vals and vals[0]:
                paths.append(Path(vals[0]))
        return paths

    def action_open_folder(self) -> None:
        paths = self.selected_paths()
        if paths and self.on_navigate:
            self.on_navigate(paths[0].parent)

    def action_delete(self) -> None:
        paths = self.selected_paths()
        if not paths:
            return
        if confirm_delete(self, paths):
            for p in paths:
                try:
                    p.unlink()
                except OSError as e:
                    messagebox.showerror("Delete Error", str(e), parent=self)
            self.start_scan()

    def action_trash(self) -> None:
        from pathlib_gui.dialogs.delete import confirm_trash
        from pathlib_gui.services.filesystem import trash_path

        paths = self.selected_paths()
        if not paths:
            return
        if confirm_trash(self, paths):
            for p in paths:
                try:
                    trash_path(p)
                except Exception as e:
                    messagebox.showerror("Trash Error", str(e), parent=self)
            self.start_scan()

    def action_keep_newest(self) -> None:
        self.keep_strategy(lambda group: sorted(group, key=lambda p: p.stat().st_mtime, reverse=True)[1:])

    def action_keep_oldest(self) -> None:
        self.keep_strategy(lambda group: sorted(group, key=lambda p: p.stat().st_mtime)[1:])

    def action_keep_shortest(self) -> None:
        self.keep_strategy(lambda group: sorted(group, key=lambda p: len(str(p)))[1:])

    def keep_strategy(self, to_delete_fn: Callable[[list[Path]], list[Path]]) -> None:
        all_to_delete: list[Path] = []
        for group in self.groups:
            all_to_delete.extend(to_delete_fn(group))
        if not all_to_delete:
            return
        if confirm_delete(self, all_to_delete):
            for p in all_to_delete:
                try:
                    p.unlink()
                except OSError as e:
                    messagebox.showerror("Delete Error", str(e), parent=self)
            self.start_scan()

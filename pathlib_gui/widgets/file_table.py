"""File list table widget backed by ttk.Treeview."""

from __future__ import annotations

import datetime
import tkinter as tk
from pathlib import Path
from tkinter import ttk
from typing import Callable

from pathlib_gui.models.paths import PathInfo, format_size, list_directory

COLUMNS = ("name", "size", "type", "modified", "permissions")
COLUMN_HEADINGS = {
    "name": "Name",
    "size": "Size",
    "type": "Type",
    "modified": "Modified",
    "permissions": "Permissions",
}
COLUMN_WIDTHS = {
    "name": 250,
    "size": 80,
    "type": 120,
    "modified": 140,
    "permissions": 100,
}


def format_timestamp(ts: float) -> str:
    if ts == 0.0:
        return ""
    return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")


class FileTable(ttk.Frame):
    """Treeview-based file listing with sortable columns."""

    def __init__(
        self,
        parent: tk.Widget,
        on_select: Callable[[list[PathInfo]], None] | None = None,
        on_open: Callable[[PathInfo], None] | None = None,
        show_hidden: bool = False,
        **kwargs: object,
    ) -> None:
        super().__init__(parent, **kwargs)
        self.on_select = on_select
        self.on_open = on_open
        self.show_hidden = show_hidden
        self.current_path: Path | None = None
        self.entries: list[PathInfo] = []
        self.sort_column: str = "name"
        self.sort_reverse: bool = False

        self.build_tree()
        self.build_context_menu()

    def build_tree(self) -> None:
        frame = ttk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True)

        self.tree = ttk.Treeview(frame, columns=COLUMNS, show="headings", selectmode="extended")
        vsb = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.tree.yview)
        hsb = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        for col in COLUMNS:
            self.tree.heading(
                col,
                text=COLUMN_HEADINGS[col],
                command=lambda c=col: self.sort_by(c),
            )
            self.tree.column(col, width=COLUMN_WIDTHS[col], minwidth=40)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(fill=tk.X)

        self.tree.bind("<<TreeviewSelect>>", self.handle_selection)
        self.tree.bind("<Double-1>", self.handle_double_click)
        self.tree.bind("<Return>", self.handle_double_click)
        self.tree.bind("<Button-3>", self.show_context_menu)

    def build_context_menu(self) -> None:
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Open", command=self.context_open)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Copy", command=self.context_copy)
        self.context_menu.add_command(label="Move", command=self.context_move)
        self.context_menu.add_command(label="Rename", command=self.context_rename)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Delete...", command=self.context_delete)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Properties", command=self.context_properties)

    def load(self, path: Path) -> None:
        self.current_path = path
        self.entries = list_directory(path, show_hidden=self.show_hidden)
        self.apply_sort()
        self.refresh_tree()

    def refresh_tree(self) -> None:
        self.tree.delete(*self.tree.get_children())
        self.tree.tag_configure("broken_symlink", foreground="red")
        for info in self.entries:
            if info.is_broken_symlink:
                icon = "🔗"
                kind = info.kind_label() + " → broken"
                tags = ("broken_symlink",)
            elif info.is_symlink:
                icon = "🔗"
                kind = info.kind_label()
                tags = ()
            elif info.is_dir:
                icon = "📁"
                kind = info.kind_label()
                tags = ()
            else:
                icon = "📄"
                kind = info.kind_label()
                tags = ()
            self.tree.insert(
                "",
                tk.END,
                iid=str(info.path),
                values=(
                    f"{icon} {info.name}",
                    format_size(info.size, info.is_dir),
                    kind,
                    format_timestamp(info.modified),
                    info.permissions_string(),
                ),
                tags=tags,
            )

    def sort_by(self, column: str) -> None:
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = False
        self.apply_sort()
        self.refresh_tree()

    def apply_sort(self) -> None:
        key_funcs = {
            "name": lambda e: (not e.is_dir, e.name.lower()),
            "size": lambda e: (not e.is_dir, e.size),
            "type": lambda e: (not e.is_dir, e.kind_label().lower()),
            "modified": lambda e: (not e.is_dir, e.modified),
            "permissions": lambda e: (not e.is_dir, e.mode),
        }
        key = key_funcs.get(self.sort_column, key_funcs["name"])
        self.entries.sort(key=key, reverse=self.sort_reverse)

    def selected_infos(self) -> list[PathInfo]:
        selected_ids = self.tree.selection()
        by_path = {str(e.path): e for e in self.entries}
        return [by_path[iid] for iid in selected_ids if iid in by_path]

    def handle_selection(self, event: tk.Event) -> None:  # type: ignore[type-arg]
        if self.on_select:
            self.on_select(self.selected_infos())

    def handle_double_click(self, event: tk.Event) -> None:  # type: ignore[type-arg]
        infos = self.selected_infos()
        if infos and self.on_open:
            self.on_open(infos[0])

    def show_context_menu(self, event: tk.Event) -> None:  # type: ignore[type-arg]
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def context_open(self) -> None:
        infos = self.selected_infos()
        if infos and self.on_open:
            self.on_open(infos[0])

    def context_copy(self) -> None:
        self.event_generate("<<FileTableCopy>>")

    def context_move(self) -> None:
        self.event_generate("<<FileTableMove>>")

    def context_rename(self) -> None:
        self.event_generate("<<FileTableRename>>")

    def context_delete(self) -> None:
        self.event_generate("<<FileTableDelete>>")

    def context_properties(self) -> None:
        self.event_generate("<<FileTableProperties>>")

    def toggle_hidden(self) -> None:
        self.show_hidden = not self.show_hidden
        if self.current_path:
            self.load(self.current_path)

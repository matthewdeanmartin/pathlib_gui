"""TOML file preview inspector (Python 3.11+ tomllib)."""

from __future__ import annotations

import importlib
import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk
from typing import Any

from pathlib_gui.inspectors.base import BaseInspector

MAX_BYTES = 256 * 1024


def build_tree_items(tree: ttk.Treeview, parent: str, value: object, depth: int = 0) -> None:
    if depth > 20:
        tree.insert(parent, tk.END, text="...(depth limit)")
        return
    if isinstance(value, dict):
        for k, v in value.items():
            label = f"{k}: {type(v).__name__}"
            node = tree.insert(parent, tk.END, text=label, open=depth < 2)
            build_tree_items(tree, node, v, depth + 1)
    elif isinstance(value, list):
        for i, v in enumerate(value[:200]):
            label = f"[{i}]: {type(v).__name__}"
            node = tree.insert(parent, tk.END, text=label, open=depth < 1)
            build_tree_items(tree, node, v, depth + 1)
        if len(value) > 200:
            tree.insert(parent, tk.END, text=f"... {len(value) - 200} more items")
    else:
        tree.insert(parent, tk.END, text=repr(value))


class TomlInspector(BaseInspector):
    label = "TOML"

    def __init__(self, parent: tk.Misc, **kwargs: Any) -> None:
        super().__init__(parent, **kwargs)
        self.build_widgets()

    def build_widgets(self) -> None:
        top = ttk.Frame(self)
        top.pack(fill=tk.X, padx=4, pady=2)
        version_note = f"Python {sys.version_info.major}.{sys.version_info.minor}"
        ttk.Label(top, text=f"Backend: tomllib.loads ({version_note})", foreground="gray").pack(side=tk.LEFT)
        self.info_label = ttk.Label(top, text="", foreground="gray")
        self.info_label.pack(side=tk.RIGHT)

        if sys.version_info < (3, 11):
            ttk.Label(self, text="tomllib requires Python 3.11+. This file cannot be parsed.", foreground="red").pack(
                padx=8, pady=8
            )
            self.tree = None
            return

        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        self.tree = ttk.Treeview(tree_frame, show="tree", selectmode="browse")
        vsb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

    def load(self, path: Path) -> None:
        if self.tree is None:
            return
        self.tree.delete(*self.tree.get_children())

        if sys.version_info < (3, 11):
            return

        try:
            tomllib = importlib.import_module("tomllib")
            with path.open("rb") as fh:
                data = tomllib.load(fh)
        except Exception as e:
            self.info_label.configure(text=f"Parse error: {e}")
            self.tree.insert("", tk.END, text=f"Error: {e}")
            return

        self.info_label.configure(text=f"Valid TOML — {len(data)} top-level keys")
        build_tree_items(self.tree, "", data)

    def clear(self) -> None:
        if self.tree:
            self.tree.delete(*self.tree.get_children())
        self.info_label.configure(text="")

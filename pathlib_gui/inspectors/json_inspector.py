"""JSON file preview inspector."""

from __future__ import annotations

import json
import tkinter as tk
from pathlib import Path
from tkinter import ttk

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


class JsonInspector(BaseInspector):
    label = "JSON"

    def __init__(self, parent: tk.Widget, **kwargs: object) -> None:
        super().__init__(parent, **kwargs)
        self.build_widgets()

    def build_widgets(self) -> None:
        top = ttk.Frame(self)
        top.pack(fill=tk.X, padx=4, pady=2)
        ttk.Label(top, text="Backend: json.loads / json.dumps", foreground="gray").pack(side=tk.LEFT)
        self.info_label = ttk.Label(top, text="", foreground="gray")
        self.info_label.pack(side=tk.RIGHT)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        tree_frame = ttk.Frame(self.notebook)
        self.notebook.add(tree_frame, text="Tree")

        self.tree = ttk.Treeview(tree_frame, show="tree", selectmode="browse")
        vsb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        pretty_frame = ttk.Frame(self.notebook)
        self.notebook.add(pretty_frame, text="Pretty")
        self.pretty_text = tk.Text(pretty_frame, wrap=tk.NONE, state=tk.DISABLED, relief=tk.FLAT, font=("Courier", 10))
        vsb2 = ttk.Scrollbar(pretty_frame, orient=tk.VERTICAL, command=self.pretty_text.yview)
        hsb2 = ttk.Scrollbar(pretty_frame, orient=tk.HORIZONTAL, command=self.pretty_text.xview)
        self.pretty_text.configure(yscrollcommand=vsb2.set, xscrollcommand=hsb2.set)
        self.pretty_text.grid(row=0, column=0, sticky="nsew")
        vsb2.grid(row=0, column=1, sticky="ns")
        hsb2.grid(row=1, column=0, sticky="ew")
        pretty_frame.rowconfigure(0, weight=1)
        pretty_frame.columnconfigure(0, weight=1)

    def load(self, path: Path) -> None:
        self.tree.delete(*self.tree.get_children())
        self.pretty_text.configure(state=tk.NORMAL)
        self.pretty_text.delete("1.0", tk.END)

        try:
            raw = path.read_bytes()[:MAX_BYTES]
            text = raw.decode("utf-8", errors="replace")
            data = json.loads(text)
        except json.JSONDecodeError as e:
            self.info_label.configure(text=f"JSON error: {e}")
            self.pretty_text.insert("1.0", f"Parse error:\n{e}")
            self.pretty_text.configure(state=tk.DISABLED)
            return
        except OSError as e:
            self.info_label.configure(text=f"Error: {e}")
            self.pretty_text.configure(state=tk.DISABLED)
            return

        kind = type(data).__name__
        if isinstance(data, (dict, list)):
            count = len(data)
            self.info_label.configure(text=f"Valid JSON — {kind} with {count} top-level items")
        else:
            self.info_label.configure(text=f"Valid JSON — {kind}")

        build_tree_items(self.tree, "", data)
        pretty = json.dumps(data, indent=2, ensure_ascii=False)
        self.pretty_text.insert("1.0", pretty)
        self.pretty_text.configure(state=tk.DISABLED)

    def clear(self) -> None:
        self.tree.delete(*self.tree.get_children())
        self.pretty_text.configure(state=tk.NORMAL)
        self.pretty_text.delete("1.0", tk.END)
        self.pretty_text.configure(state=tk.DISABLED)
        self.info_label.configure(text="")

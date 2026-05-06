"""INI/config inspector — uses configparser."""

from __future__ import annotations

import configparser
import tkinter as tk
from pathlib import Path
from tkinter import ttk

from pathlib_gui.inspectors.base import BaseInspector


class IniInspector(BaseInspector):
    label = "INI/Config"

    def __init__(self, parent: tk.Widget, **kwargs: object) -> None:
        super().__init__(parent, **kwargs)
        ttk.Label(self, text="Backend: configparser.ConfigParser", foreground="gray").pack(
            anchor="w", padx=4, pady=2
        )
        self.tree = ttk.Treeview(self, columns=("key", "value"), show="tree headings")
        self.tree.heading("#0", text="Section")
        self.tree.heading("key", text="Key")
        self.tree.heading("value", text="Value")
        self.tree.column("#0", width=140)
        self.tree.column("key", width=160)
        self.tree.column("value", width=280)
        sb = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(4, 0), pady=4)
        sb.pack(side=tk.RIGHT, fill=tk.Y, pady=4)

    def load(self, path: Path) -> None:
        self.tree.delete(*self.tree.get_children())
        cfg = configparser.ConfigParser()
        try:
            cfg.read(str(path), encoding="utf-8")
        except Exception as e:
            self.tree.insert("", tk.END, text=f"Error: {e}")
            return
        for section in cfg.sections():
            node = self.tree.insert("", tk.END, text=section, open=True)
            for key, value in cfg.items(section):
                self.tree.insert(node, tk.END, text="", values=(key, value))

    def clear(self) -> None:
        self.tree.delete(*self.tree.get_children())

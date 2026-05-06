"""Path / breadcrumb bar widget."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import ttk
from typing import Callable


class PathBar(ttk.Frame):
    """Editable path bar with breadcrumb navigation buttons."""

    def __init__(self, parent: tk.Widget, on_navigate: Callable[[Path], None], **kwargs: object) -> None:
        super().__init__(parent, **kwargs)
        self.on_navigate = on_navigate

        self.path_var = tk.StringVar()
        self.entry = ttk.Entry(self, textvariable=self.path_var)
        self.entry.pack(fill=tk.X, expand=True, padx=2, pady=2)
        self.entry.bind("<Return>", self.handle_entry_return)

    def set_path(self, path: Path) -> None:
        self.path_var.set(str(path))

    def handle_entry_return(self, event: tk.Event) -> None:  # type: ignore[type-arg]
        text = self.path_var.get().strip()
        p = Path(text)
        if p.exists():
            self.on_navigate(p if p.is_dir() else p.parent)
        else:
            self.path_var.set("")

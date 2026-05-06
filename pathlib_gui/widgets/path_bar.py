"""Path / breadcrumb bar widget."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import ttk
from collections.abc import Callable


class PathBar(ttk.Frame):
    """Editable path bar with clickable breadcrumb buttons above the text entry."""

    def __init__(self, parent: tk.Widget, on_navigate: Callable[[Path], None], **kwargs: object) -> None:
        super().__init__(parent, **kwargs)
        self.on_navigate = on_navigate

        self.crumb_frame = ttk.Frame(self)
        self.crumb_frame.pack(fill=tk.X, padx=2, pady=(2, 0))

        self.path_var = tk.StringVar()
        self.entry = ttk.Entry(self, textvariable=self.path_var)
        self.entry.pack(fill=tk.X, expand=True, padx=2, pady=(0, 2))
        self.entry.bind("<Return>", self.handle_entry_return)

    def set_path(self, path: Path) -> None:
        self.path_var.set(str(path))
        self._rebuild_crumbs(path)

    def _rebuild_crumbs(self, path: Path) -> None:
        for w in self.crumb_frame.winfo_children():
            w.destroy()

        parts = path.parts
        cumulative = Path(parts[0]) if parts else path
        for i, part in enumerate(parts):
            if i > 0:
                cumulative = cumulative / part
            label = part if part not in ("/", "\\") else part
            btn_path = cumulative  # capture for closure
            btn = ttk.Button(
                self.crumb_frame,
                text=label,
                command=lambda p=btn_path: self.on_navigate(p),
                style="Crumb.TButton",
            )
            btn.pack(side=tk.LEFT, padx=0, pady=0)
            if i < len(parts) - 1:
                ttk.Label(self.crumb_frame, text="›").pack(side=tk.LEFT)

        try:
            self.crumb_frame.tk.call("ttk::style", "configure", "Crumb.TButton", "-padding", "2 0")
        except Exception:
            pass

    def handle_entry_return(self, event: tk.Event) -> None:  # type: ignore[type-arg]
        text = self.path_var.get().strip()
        p = Path(text)
        if p.exists():
            self.on_navigate(p if p.is_dir() else p.parent)
        else:
            self.path_var.set("")

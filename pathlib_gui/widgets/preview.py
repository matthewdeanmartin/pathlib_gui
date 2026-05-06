"""PreviewPane widget — dispatches to the right inspector based on file type."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import ttk

from pathlib_gui.inspectors.base import BaseInspector, inspector_for_path
from pathlib_gui.models.paths import PathInfo


class PreviewPane(ttk.Frame):
    """A pane that shows a type-appropriate preview for the selected file."""

    def __init__(self, parent: tk.Widget, **kwargs: object) -> None:
        super().__init__(parent, **kwargs)
        self.current_inspector: BaseInspector | None = None
        self.current_path: Path | None = None

        header = ttk.Frame(self)
        header.pack(fill=tk.X)
        ttk.Label(header, text="Preview", font=("", 10, "bold")).pack(side=tk.LEFT, padx=6, pady=(6, 2))
        self.type_label = ttk.Label(header, text="", foreground="gray")
        self.type_label.pack(side=tk.LEFT, padx=4, pady=(6, 2))

        self.content_frame = ttk.Frame(self)
        self.content_frame.pack(fill=tk.BOTH, expand=True)

        self.placeholder = ttk.Label(self.content_frame, text="Select a file to preview.", foreground="gray")
        self.placeholder.pack(expand=True)

    def show(self, info: PathInfo) -> None:
        if not info.is_file:
            self.clear()
            return

        if self.current_inspector:
            self.current_inspector.destroy()
            self.current_inspector = None
        self.placeholder.pack_forget()

        self.current_path = info.path
        inspector = inspector_for_path(self.content_frame, info.path)
        inspector.pack(fill=tk.BOTH, expand=True)
        inspector.load(info.path)
        self.current_inspector = inspector
        self.type_label.configure(text=f"[{inspector.label}]")

    def clear(self) -> None:
        if self.current_inspector:
            self.current_inspector.destroy()
            self.current_inspector = None
        self.current_path = None
        self.type_label.configure(text="")
        self.placeholder.pack(expand=True)

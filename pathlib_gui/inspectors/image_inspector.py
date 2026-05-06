"""Image preview inspector using tkinter.PhotoImage."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import ttk

from pathlib_gui.inspectors.base import BaseInspector

SUPPORTED = {".gif", ".ppm", ".pgm", ".pbm", ".png"}


class ImageInspector(BaseInspector):
    label = "Image"

    def __init__(self, parent: tk.Widget, **kwargs: object) -> None:
        super().__init__(parent, **kwargs)
        self.photo: tk.PhotoImage | None = None
        self.build_widgets()

    def build_widgets(self) -> None:
        ttk.Label(self, text="Backend: tkinter.PhotoImage", foreground="gray").pack(anchor="w", padx=4, pady=2)
        self.info_label = ttk.Label(self, text="", foreground="gray")
        self.info_label.pack(anchor="w", padx=4)
        self.canvas = tk.Canvas(self, background="#888")
        self.canvas.pack(fill=tk.BOTH, expand=True)

    def load(self, path: Path) -> None:
        self.canvas.delete("all")
        self.photo = None
        suffix = path.suffix.lower()
        if suffix not in SUPPORTED:
            self.info_label.configure(
                text=f"Format {suffix!r} not natively supported by Tk. Install Pillow for richer image support."
            )
            return
        try:
            self.photo = tk.PhotoImage(file=str(path))
            w, h = self.photo.width(), self.photo.height()
            self.info_label.configure(text=f"{w} × {h} px  |  {path.stat().st_size:,} bytes")
            self.canvas.create_image(0, 0, anchor="nw", image=self.photo)
            self.canvas.configure(scrollregion=(0, 0, w, h))
        except tk.TclError as e:
            self.info_label.configure(text=f"Cannot display: {e}")

    def clear(self) -> None:
        self.canvas.delete("all")
        self.photo = None
        self.info_label.configure(text="")

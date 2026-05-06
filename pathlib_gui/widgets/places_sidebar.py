"""Places / bookmarks sidebar widget."""

from __future__ import annotations

import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk
from collections.abc import Callable


def default_places() -> list[tuple[str, Path]]:
    home = Path.home()
    places = [
        ("Home", home),
        ("Desktop", home / "Desktop"),
        ("Documents", home / "Documents"),
        ("Downloads", home / "Downloads"),
        ("Pictures", home / "Pictures"),
    ]
    if sys.platform == "win32":
        import string

        drives = [Path(f"{d}:\\") for d in string.ascii_uppercase if Path(f"{d}:\\").exists()]
        for drive in drives:
            places.append((str(drive), drive))
    elif sys.platform == "darwin":
        volumes = Path("/Volumes")
        if volumes.exists():
            places.append(("Volumes", volumes))
    else:
        places.append(("Root", Path("/")))
        media = Path("/media")
        if media.exists():
            places.append(("Media", media))

    return [(label, p) for label, p in places if p.exists()]


class PlacesSidebar(ttk.Frame):
    """Sidebar listing common filesystem places."""

    def __init__(self, parent: tk.Widget, on_navigate: Callable[[Path], None], **kwargs: object) -> None:
        super().__init__(parent, **kwargs)
        self.on_navigate = on_navigate
        self.places: list[tuple[str, Path]] = []

        self.listbox = tk.Listbox(self, selectmode=tk.SINGLE, activestyle="none", width=18)
        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scrollbar.set)

        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.listbox.bind("<<ListboxSelect>>", self.handle_selection)
        self.refresh_places()

    def refresh_places(self) -> None:
        self.places = default_places()
        self.listbox.delete(0, tk.END)
        for label, _ in self.places:
            self.listbox.insert(tk.END, label)

    def handle_selection(self, event: tk.Event) -> None:  # type: ignore[type-arg]
        sel = self.listbox.curselection()
        if not sel:
            return
        _, path = self.places[sel[0]]
        if path.exists():
            self.on_navigate(path)

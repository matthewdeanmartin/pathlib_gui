"""Copy/move destination picker dialog."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog


def ask_copy_destination(parent: tk.Misc, source_name: str) -> Path | None:
    """Ask user where to copy a file/folder. Returns None if cancelled."""
    result = filedialog.askdirectory(
        title=f"Copy '{source_name}' to folder...",
        mustexist=True,
        parent=parent,
    )
    return Path(result) if result else None


def ask_move_destination(parent: tk.Misc, source_name: str) -> Path | None:
    """Ask user where to move a file/folder. Returns None if cancelled."""
    result = filedialog.askdirectory(
        title=f"Move '{source_name}' to folder...",
        mustexist=True,
        parent=parent,
    )
    return Path(result) if result else None


def ask_save_file(parent: tk.Misc, initial_name: str = "") -> Path | None:
    result = filedialog.asksaveasfilename(
        title="Save as",
        initialfile=initial_name,
        parent=parent,
    )
    return Path(result) if result else None

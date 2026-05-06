"""Rename dialog."""

from __future__ import annotations

import tkinter as tk
from tkinter import simpledialog


def ask_rename(parent: tk.Misc, current_name: str) -> str | None:
    """Prompt for a new filename. Returns None if cancelled."""
    return simpledialog.askstring(
        "Rename",
        f"Rename '{current_name}' to:",
        initialvalue=current_name,
        parent=parent,
    )

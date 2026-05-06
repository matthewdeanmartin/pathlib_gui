"""Pair-picker dialog for compare mode."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk


def pick_compare_pair(parent: tk.Misc, initial_left: Path | None = None) -> tuple[Path, Path] | None:
    """Show a dialog to pick two files or directories to compare."""
    result: list[tuple[Path, Path]] = []

    win = tk.Toplevel(parent)
    win.title("Compare — pick two paths")
    win.geometry("500x180")
    win.resizable(False, False)
    win.grab_set()

    left_var = tk.StringVar(value=str(initial_left) if initial_left else "")
    right_var = tk.StringVar()

    def browse(var: tk.StringVar, label: str) -> None:
        path = filedialog.askdirectory(title=f"Select {label}...", parent=win)
        if not path:
            path = filedialog.askopenfilename(title=f"Select {label} file...", parent=win)
        if path:
            var.set(path)

    grid = ttk.Frame(win, padding=12)
    grid.pack(fill=tk.BOTH, expand=True)

    ttk.Label(grid, text="Left:").grid(row=0, column=0, sticky="e", padx=4, pady=4)
    ttk.Entry(grid, textvariable=left_var, width=44).grid(row=0, column=1, padx=2)
    ttk.Button(grid, text="…", width=3, command=lambda: browse(left_var, "Left")).grid(row=0, column=2)

    ttk.Label(grid, text="Right:").grid(row=1, column=0, sticky="e", padx=4, pady=4)
    ttk.Entry(grid, textvariable=right_var, width=44).grid(row=1, column=1, padx=2)
    ttk.Button(grid, text="…", width=3, command=lambda: browse(right_var, "Right")).grid(row=1, column=2)

    def confirm() -> None:
        left = Path(left_var.get().strip())
        right = Path(right_var.get().strip())
        if left.exists() and right.exists():
            result.append((left, right))
            win.destroy()

    def cancel() -> None:
        win.destroy()

    btn_frame = ttk.Frame(win)
    btn_frame.pack(fill=tk.X, padx=12, pady=(0, 8))
    ttk.Button(btn_frame, text="Compare", command=confirm).pack(side=tk.RIGHT, padx=4)
    ttk.Button(btn_frame, text="Cancel", command=cancel).pack(side=tk.RIGHT)

    win.wait_window()
    return result[0] if result else None

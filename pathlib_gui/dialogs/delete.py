"""Delete confirmation dialog."""

from __future__ import annotations

import shutil
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from pathlib_gui.services.filesystem import send2trash_available


def count_contents(path: Path) -> tuple[int, int, int]:
    """Return (files, folders, total_bytes) for a directory."""
    files = folders = total = 0
    try:
        for p in path.rglob("*"):
            if p.is_file():
                files += 1
                try:
                    total += p.stat().st_size
                except OSError:
                    pass
            elif p.is_dir():
                folders += 1
    except PermissionError:
        pass
    return files, folders, total


def format_bytes(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n = int(n / 1024)
    return f"{n:.1f} PB"


def confirm_delete(parent: tk.Widget, paths: list[Path]) -> bool:
    """Show delete confirmation. Returns True if user confirms permanent delete."""
    lines: list[str] = ["You are about to permanently delete:\n"]

    for p in paths[:5]:
        lines.append(f"  {p}")
        if p.is_dir():
            files, folders, total = count_contents(p)
            lines.append(f"    Contains: {files} files, {folders} folders")
            lines.append(f"    Total size: {format_bytes(total)}")
    if len(paths) > 5:
        lines.append(f"  ... and {len(paths) - 5} more")

    lines.append("\nThis cannot be undone by pathlib_gui.")

    backend = "pathlib.Path.unlink" if len(paths) == 1 and paths[0].is_file() else "shutil.rmtree"
    lines.append(f"\nBackend: {backend}")

    return messagebox.askokcancel(
        "Confirm Permanent Delete",
        "\n".join(lines),
        icon=messagebox.WARNING,
        parent=parent,
    )


def confirm_trash(parent: tk.Widget, paths: list[Path]) -> bool:
    """Show move-to-trash confirmation."""
    names = "\n".join(f"  {p.name}" for p in paths[:5])
    if len(paths) > 5:
        names += f"\n  ... and {len(paths) - 5} more"
    return messagebox.askokcancel(
        "Move to Trash",
        f"Move to trash:\n{names}\n\nBackend: send2trash.send2trash",
        parent=parent,
    )

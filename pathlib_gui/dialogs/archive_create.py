"""Archive creation dialog."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk
from typing import cast

from pathlib_gui.services.archive_service import ARCHIVE_PRESETS, ArchiveCompression, ArchiveFormat


def show_create_archive_dialog(
    parent: tk.Misc, sources: list[Path]
) -> tuple[Path, ArchiveFormat, ArchiveCompression] | None:
    """Show archive creation dialog. Returns (dest_path, preset_label, compression) or None."""
    result: list[tuple[Path, ArchiveFormat, ArchiveCompression]] = []

    win = tk.Toplevel(parent)
    win.title("Create Archive")
    win.geometry("520x320")
    win.resizable(False, False)
    win.grab_set()

    ttk.Label(win, text="Sources:", font=("", 9, "bold")).pack(anchor="w", padx=12, pady=(10, 2))
    src_text = tk.Text(win, height=4, wrap=tk.NONE, state=tk.NORMAL, relief=tk.SUNKEN)
    src_text.insert("1.0", "\n".join(str(s) for s in sources))
    src_text.configure(state=tk.DISABLED)
    src_text.pack(fill=tk.X, padx=12)

    preset_var = tk.StringVar(value=ARCHIVE_PRESETS[1][0])

    ttk.Label(win, text="Format:").pack(anchor="w", padx=12, pady=(8, 2))
    preset_frame = ttk.Frame(win)
    preset_frame.pack(fill=tk.X, padx=12)
    for label, _, _ in ARCHIVE_PRESETS:
        ttk.Radiobutton(preset_frame, text=label, variable=preset_var, value=label).pack(anchor="w")

    dest_var = tk.StringVar()
    ttk.Label(win, text="Save as:").pack(anchor="w", padx=12, pady=(8, 2))
    dest_frame = ttk.Frame(win)
    dest_frame.pack(fill=tk.X, padx=12)
    ttk.Entry(dest_frame, textvariable=dest_var, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True)

    def browse_dest() -> None:
        path = filedialog.asksaveasfilename(
            title="Save archive as…",
            defaultextension=".zip",
            filetypes=[
                ("ZIP", "*.zip"),
                ("TAR", "*.tar"),
                ("TAR.GZ", "*.tar.gz *.tgz"),
                ("TAR.BZ2", "*.tar.bz2"),
                ("TAR.XZ", "*.tar.xz"),
                ("GZ", "*.gz"),
                ("BZ2", "*.bz2"),
                ("XZ", "*.xz"),
            ],
            parent=win,
        )
        if path:
            dest_var.set(path)

    ttk.Button(dest_frame, text="…", width=3, command=browse_dest).pack(side=tk.LEFT, padx=2)

    def confirm() -> None:
        dest_str = dest_var.get().strip()
        if not dest_str:
            return
        selected = preset_var.get()
        for label, fmt, compression in ARCHIVE_PRESETS:
            if label == selected:
                result.append((Path(dest_str), cast(ArchiveFormat, fmt), cast(ArchiveCompression, compression)))
                break
        win.destroy()

    btn_frame = ttk.Frame(win)
    btn_frame.pack(fill=tk.X, padx=12, pady=8)
    ttk.Button(btn_frame, text="Create", command=confirm).pack(side=tk.RIGHT, padx=4)
    ttk.Button(btn_frame, text="Cancel", command=win.destroy).pack(side=tk.RIGHT)

    win.wait_window()
    return result[0] if result else None

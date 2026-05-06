"""Preferences dialog."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from pathlib_gui.config import get_prefs

ARCHIVE_FORMATS = ["zip", "tar.gz", "tar.bz2", "tar.xz", "tar"]
HASH_ALGORITHMS = ["md5", "sha1", "sha256", "sha512", "blake2b", "blake2s"]
COMPARE_MODES = ["text", "binary", "hash", "metadata"]


class PreferencesDialog(tk.Toplevel):
    def __init__(self, parent: tk.Widget) -> None:
        super().__init__(parent)
        self.title("Preferences")
        self.geometry("420x380")
        self.resizable(False, False)
        self.grab_set()
        prefs = get_prefs()

        self.show_hidden = tk.BooleanVar(value=bool(prefs.get("show_hidden")))
        self.confirm_deletes = tk.BooleanVar(value=bool(prefs.get("confirm_deletes")))
        self.prefer_trash = tk.BooleanVar(value=bool(prefs.get("prefer_trash")))
        self.follow_symlinks = tk.BooleanVar(value=bool(prefs.get("follow_symlinks_search")))
        self.archive_fmt = tk.StringVar(value=str(prefs.get("default_archive_format")))
        self.hash_algo = tk.StringVar(value=str(prefs.get("hash_algorithm")))
        self.compare_mode = tk.StringVar(value=str(prefs.get("default_compare_mode")))
        self.font_size = tk.StringVar(value=str(prefs.get("font_size")))

        nb = ttk.Notebook(self)
        nb.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # --- General tab ---
        gen = ttk.Frame(nb, padding=10)
        nb.add(gen, text="General")
        ttk.Checkbutton(gen, text="Show hidden files by default", variable=self.show_hidden).pack(anchor="w", pady=2)
        ttk.Checkbutton(gen, text="Confirm before deleting files", variable=self.confirm_deletes).pack(anchor="w", pady=2)
        ttk.Checkbutton(gen, text="Prefer Trash over permanent delete (if available)", variable=self.prefer_trash).pack(
            anchor="w", pady=2
        )
        ttk.Checkbutton(gen, text="Follow symlinks during search", variable=self.follow_symlinks).pack(
            anchor="w", pady=2
        )
        ttk.Label(gen, text="Font size:").pack(anchor="w", pady=(8, 0))
        ttk.Entry(gen, textvariable=self.font_size, width=6).pack(anchor="w")

        # --- Files tab ---
        files = ttk.Frame(nb, padding=10)
        nb.add(files, text="Files")
        ttk.Label(files, text="Default archive format:").pack(anchor="w")
        ttk.Combobox(files, textvariable=self.archive_fmt, values=ARCHIVE_FORMATS, state="readonly", width=16).pack(
            anchor="w", pady=2
        )
        ttk.Label(files, text="Default hash algorithm:").pack(anchor="w", pady=(8, 0))
        ttk.Combobox(files, textvariable=self.hash_algo, values=HASH_ALGORITHMS, state="readonly", width=16).pack(
            anchor="w", pady=2
        )
        ttk.Label(files, text="Default compare mode:").pack(anchor="w", pady=(8, 0))
        ttk.Combobox(files, textvariable=self.compare_mode, values=COMPARE_MODES, state="readonly", width=16).pack(
            anchor="w", pady=2
        )

        # --- Buttons ---
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=8, pady=(0, 8))
        ttk.Button(btn_frame, text="Save", command=self.save).pack(side=tk.RIGHT, padx=4)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT)

    def save(self) -> None:
        prefs = get_prefs()
        prefs.set("show_hidden", self.show_hidden.get())
        prefs.set("confirm_deletes", self.confirm_deletes.get())
        prefs.set("prefer_trash", self.prefer_trash.get())
        prefs.set("follow_symlinks_search", self.follow_symlinks.get())
        prefs.set("default_archive_format", self.archive_fmt.get())
        prefs.set("hash_algorithm", self.hash_algo.get())
        prefs.set("default_compare_mode", self.compare_mode.get())
        try:
            prefs.set("font_size", int(self.font_size.get()))
        except ValueError:
            pass
        prefs.save()
        self.destroy()

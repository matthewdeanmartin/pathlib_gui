"""Create symlink dialog."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk


class CreateSymlinkDialog(tk.Toplevel):
    """Dialog to create a symbolic link."""

    def __init__(self, parent: tk.Widget, cwd: Path) -> None:
        super().__init__(parent)
        self.title("Create Symlink")
        self.resizable(False, False)
        self.grab_set()
        self.cwd = cwd
        self.created: Path | None = None

        ttk.Label(self, text="Backend: pathlib.Path.symlink_to", foreground="gray").pack(
            anchor="w", padx=8, pady=(8, 0)
        )

        form = ttk.Frame(self, padding=8)
        form.pack(fill=tk.X)

        ttk.Label(form, text="Link name (in current folder):").grid(row=0, column=0, sticky="e", padx=4, pady=4)
        self.name_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.name_var, width=32).grid(row=0, column=1, sticky="w", padx=2)

        ttk.Label(form, text="Target path:").grid(row=1, column=0, sticky="e", padx=4, pady=4)
        self.target_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.target_var, width=32).grid(row=1, column=1, sticky="w", padx=2)
        ttk.Button(form, text="Browse…", command=self.browse_target).grid(row=1, column=2, padx=4)

        self.relative_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(form, text="Use relative target path where possible", variable=self.relative_var).grid(
            row=2, column=0, columnspan=3, sticky="w", padx=4, pady=4
        )

        btn_frame = ttk.Frame(self, padding=(8, 0, 8, 8))
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="Create", command=self.create).pack(side=tk.RIGHT, padx=4)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT)

    def browse_target(self) -> None:
        p = filedialog.askopenfilename(title="Select symlink target", parent=self)
        if p:
            self.target_var.set(p)

    def create(self) -> None:
        name = self.name_var.get().strip()
        target_str = self.target_var.get().strip()
        if not name or not target_str:
            messagebox.showerror("Error", "Both link name and target are required.", parent=self)
            return
        link = self.cwd / name
        target = Path(target_str)
        if self.relative_var.get():
            try:
                target = target.relative_to(self.cwd)
            except ValueError:
                pass
        try:
            link.symlink_to(target)
            self.created = link
            self.destroy()
        except OSError as e:
            messagebox.showerror("Symlink Error", str(e), parent=self)

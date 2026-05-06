"""Permissions display and editor widget."""

from __future__ import annotations

import os
import stat
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

BITS = [
    ("Owner read", stat.S_IRUSR, 0),
    ("Owner write", stat.S_IWUSR, 0),
    ("Owner execute", stat.S_IXUSR, 0),
    ("Group read", stat.S_IRGRP, 1),
    ("Group write", stat.S_IWGRP, 1),
    ("Group execute", stat.S_IXGRP, 1),
    ("Other read", stat.S_IROTH, 2),
    ("Other write", stat.S_IWOTH, 2),
    ("Other execute", stat.S_IXOTH, 2),
]


class PermissionsEditor(ttk.Frame):
    """Displays and edits POSIX-style permissions."""

    def __init__(self, parent: tk.Widget, **kwargs: object) -> None:
        super().__init__(parent, **kwargs)
        self.path: Path | None = None
        self.current_mode: int = 0
        self.bit_vars: list[tk.BooleanVar] = []
        self.octal_var = tk.StringVar()
        self.symbolic_var = tk.StringVar()
        self.recursive_var = tk.BooleanVar(value=False)
        self.build_widgets()

    def build_widgets(self) -> None:
        ttk.Label(self, text="Backend: Path.chmod / os.chmod", foreground="gray").pack(anchor="w", padx=4, pady=2)

        summary = ttk.Frame(self)
        summary.pack(fill=tk.X, padx=4, pady=2)
        ttk.Label(summary, text="Symbolic:").grid(row=0, column=0, sticky="e", padx=4)
        ttk.Label(summary, textvariable=self.symbolic_var, font=("Courier", 11)).grid(row=0, column=1, sticky="w")
        ttk.Label(summary, text="Octal:").grid(row=1, column=0, sticky="e", padx=4)
        octal_entry = ttk.Entry(summary, textvariable=self.octal_var, width=8, font=("Courier", 11))
        octal_entry.grid(row=1, column=1, sticky="w")
        octal_entry.bind("<Return>", self.apply_octal_input)
        ttk.Label(summary, text="(edit and press Enter to apply)", foreground="gray").grid(
            row=1, column=2, sticky="w", padx=4
        )

        grid = ttk.LabelFrame(self, text="Permissions")
        grid.pack(fill=tk.X, padx=4, pady=4)

        headers = ["", "Read", "Write", "Execute"]
        groups = ["Owner", "Group", "Other"]
        for col, h in enumerate(headers):
            ttk.Label(grid, text=h, font=("", 9, "bold")).grid(row=0, column=col, padx=6, pady=2)

        self.bit_vars = []
        bit_index = 0
        for row_i, group in enumerate(groups):
            ttk.Label(grid, text=group).grid(row=row_i + 1, column=0, sticky="e", padx=6)
            for col_i in range(3):
                _, bit_mask, _ = BITS[bit_index]
                var = tk.BooleanVar()
                self.bit_vars.append(var)
                ttk.Checkbutton(
                    grid,
                    variable=var,
                    command=self.sync_from_checkboxes,
                ).grid(row=row_i + 1, column=col_i + 1, padx=6, pady=2)
                bit_index += 1

        apply_frame = ttk.Frame(self)
        apply_frame.pack(fill=tk.X, padx=4, pady=4)
        ttk.Checkbutton(apply_frame, text="Apply recursively (directories)", variable=self.recursive_var).pack(
            side=tk.LEFT
        )
        ttk.Button(apply_frame, text="Apply chmod", command=self.apply_chmod).pack(side=tk.RIGHT, padx=4)

    def load(self, path: Path) -> None:
        self.path = path
        try:
            self.current_mode = stat.S_IMODE(path.lstat().st_mode)
        except OSError:
            self.current_mode = 0
        self.refresh_display()

    def refresh_display(self) -> None:
        self.symbolic_var.set(stat.filemode(self.current_mode))
        self.octal_var.set(oct(self.current_mode))
        for i, (_, bit_mask, _) in enumerate(BITS):
            self.bit_vars[i].set(bool(self.current_mode & bit_mask))

    def sync_from_checkboxes(self) -> None:
        mode = 0
        for i, (_, bit_mask, _) in enumerate(BITS):
            if self.bit_vars[i].get():
                mode |= bit_mask
        self.current_mode = mode
        self.symbolic_var.set(stat.filemode(mode))
        self.octal_var.set(oct(mode))

    def apply_octal_input(self, event: tk.Event) -> None:  # type: ignore[type-arg]
        raw = self.octal_var.get().strip()
        try:
            mode = int(raw, 8)
        except ValueError:
            messagebox.showerror("Invalid", f"Not a valid octal value: {raw!r}", parent=self)
            return
        self.current_mode = mode
        self.refresh_display()

    def apply_chmod(self) -> None:
        if not self.path:
            return
        recursive = self.recursive_var.get()
        mode = self.current_mode

        if recursive and self.path.is_dir():
            self.show_recursive_chmod_preview(mode)
        else:
            try:
                self.path.chmod(mode)
            except OSError as e:
                messagebox.showerror("chmod Failed", str(e), parent=self)
                return
            self.load(self.path)

    def show_recursive_chmod_preview(self, mode: int) -> None:
        """Show a dry-run table of recursive chmod before applying."""
        import tkinter as tk
        from tkinter import ttk

        win = tk.Toplevel(self)
        win.title("Recursive chmod — Dry Run Preview")
        win.geometry("680x420")
        win.grab_set()

        ttk.Label(
            win,
            text=f"Proposed change: {oct(mode)}  {stat.filemode(mode)}\n" f"Target directory: {self.path}",
            foreground="gray",
        ).pack(anchor="w", padx=8, pady=(8, 4))

        tree = ttk.Treeview(win, columns=("path", "old", "new"), show="headings")
        tree.heading("path", text="Path")
        tree.heading("old", text="Current")
        tree.heading("new", text="New")
        tree.column("path", width=380)
        tree.column("old", width=110)
        tree.column("new", width=110)
        sb = ttk.Scrollbar(win, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(8, 0), pady=4)
        sb.pack(side=tk.LEFT, fill=tk.Y, pady=4, padx=(0, 8))

        assert self.path is not None
        candidates = [self.path] + list(self.path.rglob("*"))
        for p in candidates[:500]:
            try:
                old_mode = stat.S_IMODE(p.lstat().st_mode)
            except OSError:
                continue
            tree.insert(
                "",
                tk.END,
                values=(
                    str(p.relative_to(self.path.parent)),
                    stat.filemode(old_mode),
                    stat.filemode(mode),
                ),
            )

        if len(candidates) > 500:
            ttk.Label(win, text=f"(showing first 500 of {len(candidates)} paths)", foreground="gray").pack(
                anchor="w", padx=8
            )

        def apply_all() -> None:
            errors: list[str] = []
            assert self.path is not None
            for p in self.path.rglob("*"):
                try:
                    os.chmod(p, mode)
                except OSError as e:
                    errors.append(f"{p}: {e}")
            try:
                os.chmod(self.path, mode)
            except OSError as e:
                errors.append(f"{self.path}: {e}")
            win.destroy()
            if errors:
                messagebox.showerror("chmod Errors", "\n".join(errors[:10]), parent=self)
            self.load(self.path)

        btn = ttk.Frame(win)
        btn.pack(fill=tk.X, padx=8, pady=(0, 8))
        ttk.Button(btn, text="Apply", command=apply_all).pack(side=tk.RIGHT, padx=4)
        ttk.Button(btn, text="Cancel", command=win.destroy).pack(side=tk.RIGHT)

    def clear(self) -> None:
        self.path = None
        self.current_mode = 0
        self.symbolic_var.set("")
        self.octal_var.set("")
        for var in self.bit_vars:
            var.set(False)

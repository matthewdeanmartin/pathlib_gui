"""Batch rename dialog with live dry-run preview."""

from __future__ import annotations

import re
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk


MODES = [
    "Add prefix",
    "Add suffix",
    "Replace text",
    "Regex replace",
    "Change extension",
    "Number sequence",
    "Lowercase",
    "Uppercase",
    "Title case",
    "Slugify",
]


def apply_rename_mode(name: str, mode: str, params: dict[str, str]) -> str:
    stem = Path(name).stem
    suffix = Path(name).suffix

    if mode == "Add prefix":
        return params.get("prefix", "") + name
    if mode == "Add suffix":
        return stem + params.get("suffix_text", "") + suffix
    if mode == "Replace text":
        return name.replace(params.get("find", ""), params.get("replace", ""))
    if mode == "Regex replace":
        try:
            return re.sub(params.get("pattern", ""), params.get("replace", ""), name)
        except re.error:
            return name
    if mode == "Change extension":
        new_ext = params.get("new_ext", "")
        if new_ext and not new_ext.startswith("."):
            new_ext = "." + new_ext
        return stem + new_ext
    if mode == "Number sequence":
        start = int(params.get("start", "1"))
        pad = int(params.get("pad", "3"))
        return f"{start:0{pad}d}_{name}"
    if mode == "Lowercase":
        return name.lower()
    if mode == "Uppercase":
        return name.upper()
    if mode == "Title case":
        return name.title()
    if mode == "Slugify":
        base = re.sub(r"[^\w\s-]", "", stem).strip()
        base = re.sub(r"[\s_-]+", "_", base).lower()
        return base + suffix
    return name


class BatchRenameDialog(tk.Toplevel):
    """Batch rename dialog with live preview table and conflict detection."""

    def __init__(self, parent: tk.Widget, paths: list[Path]) -> None:
        super().__init__(parent)
        self.paths = paths
        self.confirmed = False
        self.preview_map: list[tuple[Path, str]] = []
        self.title("Batch Rename")
        self.geometry("760x520")
        self.grab_set()
        self.build_widgets()
        self.refresh_preview()

    def build_widgets(self) -> None:
        top = ttk.Frame(self, padding=8)
        top.pack(fill=tk.X)

        ttk.Label(top, text="Mode:").grid(row=0, column=0, sticky="e", padx=4, pady=4)
        self.mode_var = tk.StringVar(value=MODES[0])
        mode_combo = ttk.Combobox(top, textvariable=self.mode_var, values=MODES, state="readonly", width=20)
        mode_combo.grid(row=0, column=1, sticky="w", padx=2)
        mode_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_params())

        self.params_frame = ttk.LabelFrame(self, text="Parameters", padding=6)
        self.params_frame.pack(fill=tk.X, padx=8, pady=4)
        self.param_widgets: dict[str, tk.StringVar] = {}
        self.refresh_params()

        ttk.Label(self, text="Preview (Backend: pathlib.Path.rename / re)", foreground="gray").pack(
            anchor="w", padx=8
        )

        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=8)
        self.tree = ttk.Treeview(
            tree_frame,
            columns=("original", "new", "status"),
            show="headings",
            selectmode="browse",
        )
        self.tree.heading("original", text="Original name")
        self.tree.heading("new", text="New name")
        self.tree.heading("status", text="Status")
        self.tree.column("original", width=280)
        self.tree.column("new", width=280)
        self.tree.column("status", width=100)
        vsb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.tag_configure("conflict", background="#f8d7da")
        self.tree.tag_configure("unchanged", foreground="gray")
        self.tree.tag_configure("ok", background="#d4edda")

        btn_frame = ttk.Frame(self, padding=8)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="Refresh Preview", command=self.refresh_preview).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Execute Rename", command=self.execute).pack(side=tk.RIGHT, padx=4)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT)

    def refresh_params(self) -> None:
        for w in self.params_frame.winfo_children():
            w.destroy()
        self.param_widgets.clear()
        mode = self.mode_var.get()

        def add_param(label: str, key: str, default: str = "") -> None:
            ttk.Label(self.params_frame, text=label + ":").pack(side=tk.LEFT, padx=4)
            var = tk.StringVar(value=default)
            entry = ttk.Entry(self.params_frame, textvariable=var, width=18)
            entry.pack(side=tk.LEFT, padx=2)
            entry.bind("<KeyRelease>", lambda e: self.refresh_preview())
            self.param_widgets[key] = var

        if mode == "Add prefix":
            add_param("Prefix", "prefix")
        elif mode == "Add suffix":
            add_param("Suffix text", "suffix_text")
        elif mode == "Replace text":
            add_param("Find", "find")
            add_param("Replace with", "replace")
        elif mode == "Regex replace":
            add_param("Pattern", "pattern")
            add_param("Replace", "replace")
        elif mode == "Change extension":
            add_param("New extension", "new_ext", ".txt")
        elif mode == "Number sequence":
            add_param("Start", "start", "1")
            add_param("Pad width", "pad", "3")

        self.refresh_preview()

    def get_params(self) -> dict[str, str]:
        return {k: v.get() for k, v in self.param_widgets.items()}

    def refresh_preview(self) -> None:
        self.tree.delete(*self.tree.get_children())
        mode = self.mode_var.get()
        params = self.get_params()
        self.preview_map = []
        seen: set[str] = set()
        conflicts: set[str] = set()

        new_names: list[str] = []
        for p in self.paths:
            new_name = apply_rename_mode(p.name, mode, params)
            new_names.append(new_name)
            if new_name in seen:
                conflicts.add(new_name)
            seen.add(new_name)

        counter_map: dict[str, int] = {}
        for p, new_name in zip(self.paths, new_names):
            if mode == "Number sequence":
                start = int(self.param_widgets.get("start", tk.StringVar(value="1")).get() or "1")
                pad = int(self.param_widgets.get("pad", tk.StringVar(value="3")).get() or "3")
                idx = counter_map.get("_seq", start)
                new_name = f"{idx:0{pad}d}_{p.name}"
                counter_map["_seq"] = idx + 1

            changed = new_name != p.name
            conflict = new_name in conflicts and new_name != p.name
            exists = (p.parent / new_name).exists() and new_name != p.name

            if conflict or exists:
                status = "CONFLICT"
                tag = "conflict"
            elif not changed:
                status = "unchanged"
                tag = "unchanged"
            else:
                status = "OK"
                tag = "ok"

            self.tree.insert("", tk.END, values=(p.name, new_name, status), tags=(tag,))
            self.preview_map.append((p, new_name))

    def execute(self) -> None:
        renames = [(p, new) for p, new in self.preview_map if p.name != new]
        if not renames:
            messagebox.showinfo("Nothing to do", "No files would be renamed.", parent=self)
            return

        errors: list[str] = []
        for p, new_name in renames:
            dst = p.parent / new_name
            if dst.exists():
                errors.append(f"Skipped {p.name} → {new_name} (destination exists)")
                continue
            try:
                p.rename(dst)
            except OSError as e:
                errors.append(f"{p.name}: {e}")

        if errors:
            messagebox.showerror("Rename Errors", "\n".join(errors), parent=self)
        else:
            messagebox.showinfo("Done", f"Renamed {len(renames)} file(s).", parent=self)
        self.confirmed = True
        self.destroy()

"""Operation queue progress view widget."""

from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from tkinter import ttk


@dataclass
class OperationEntry:
    label: str
    total: int = 0
    done: int = 0
    status: str = "pending"
    error: str = ""


class OperationQueueView(ttk.Frame):
    """Shows running/completed operations with progress bars."""

    def __init__(self, parent: tk.Widget, **kwargs: object) -> None:
        super().__init__(parent, **kwargs)
        self.entries: list[OperationEntry] = []
        self.rows: list[dict[str, tk.Widget]] = []
        self.build_widgets()

    def build_widgets(self) -> None:
        ttk.Label(self, text="Operations", font=("", 10, "bold")).pack(anchor="w", padx=6, pady=(4, 2))
        ttk.Button(self, text="Clear completed", command=self.clear_completed).pack(anchor="e", padx=6)

        canvas_frame = ttk.Frame(self)
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(canvas_frame, highlightthickness=0)
        vsb = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=vsb.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        self.inner = ttk.Frame(self.canvas)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>", self.on_inner_configure)
        self.canvas.bind("<Configure>", self.on_canvas_configure)

    def on_inner_configure(self, event: tk.Event) -> None:  # type: ignore[type-arg]
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_canvas_configure(self, event: tk.Event) -> None:  # type: ignore[type-arg]
        self.canvas.itemconfigure(self.canvas_window, width=event.width)

    def add_operation(self, entry: OperationEntry) -> int:
        self.entries.append(entry)
        idx = len(self.entries) - 1
        row = ttk.Frame(self.inner)
        row.pack(fill=tk.X, padx=4, pady=2)
        lbl = ttk.Label(row, text=entry.label, anchor="w")
        lbl.pack(fill=tk.X)
        bar = ttk.Progressbar(row, maximum=max(entry.total, 1), mode="determinate")
        bar.pack(fill=tk.X)
        status_lbl = ttk.Label(row, text=entry.status, foreground="gray", anchor="w")
        status_lbl.pack(anchor="w")
        ttk.Separator(self.inner).pack(fill=tk.X, padx=4)
        self.rows.append({"frame": row, "bar": bar, "status": status_lbl, "label": lbl})
        return idx

    def update_operation(self, idx: int, done: int, status: str = "") -> None:
        entry = self.entries[idx]
        entry.done = done
        if status:
            entry.status = status
        row = self.rows[idx]
        bar: ttk.Progressbar = row["bar"]  # type: ignore[assignment]
        bar.configure(maximum=max(entry.total, 1), value=done)
        status_lbl: ttk.Label = row["status"]  # type: ignore[assignment]
        status_lbl.configure(text=entry.status)

    def mark_done(self, idx: int, error: str = "") -> None:
        entry = self.entries[idx]
        entry.status = f"Error: {error}" if error else "Done"
        entry.error = error
        row = self.rows[idx]
        bar: ttk.Progressbar = row["bar"]  # type: ignore[assignment]
        bar.configure(value=entry.total or 1)
        status_lbl: ttk.Label = row["status"]  # type: ignore[assignment]
        color = "red" if error else "green"
        status_lbl.configure(text=entry.status, foreground=color)

    def clear_completed(self) -> None:
        keep_entries: list[OperationEntry] = []
        keep_rows: list[dict[str, tk.Widget]] = []
        for i, (entry, row) in enumerate(zip(self.entries, self.rows)):
            if entry.status in ("pending", "running"):
                keep_entries.append(entry)
                keep_rows.append(row)
            else:
                row["frame"].destroy()  # type: ignore[union-attr]
        self.entries = keep_entries
        self.rows = keep_rows

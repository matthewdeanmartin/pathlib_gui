"""CSV file preview inspector."""

from __future__ import annotations

import csv
import io
import tkinter as tk
from pathlib import Path
from tkinter import ttk

from pathlib_gui.inspectors.base import BaseInspector

MAX_ROWS = 500
MAX_BYTES = 256 * 1024


class CsvInspector(BaseInspector):
    label = "CSV"

    def __init__(self, parent: tk.Widget, **kwargs: object) -> None:
        super().__init__(parent, **kwargs)
        self.build_widgets()

    def build_widgets(self) -> None:
        info_frame = ttk.Frame(self)
        info_frame.pack(fill=tk.X, padx=4, pady=2)
        ttk.Label(info_frame, text="Backend: csv.Sniffer / csv.reader", foreground="gray").pack(side=tk.LEFT)
        self.info_label = ttk.Label(info_frame, text="", foreground="gray")
        self.info_label.pack(side=tk.RIGHT)

        self.tree_frame = ttk.Frame(self)
        self.tree_frame.pack(fill=tk.BOTH, expand=True)
        self.tree: ttk.Treeview | None = None

    def load(self, path: Path) -> None:
        if self.tree:
            self.tree.destroy()
            self.tree = None

        try:
            raw = path.read_bytes()[:MAX_BYTES]
            text = raw.decode("utf-8", errors="replace")
        except OSError as e:
            self.info_label.configure(text=f"Error: {e}")
            return

        try:
            dialect = csv.Sniffer().sniff(text[:4096], delimiters=",\t;|")
        except csv.Error:
            dialect = csv.excel

        has_header = False
        try:
            has_header = csv.Sniffer().has_header(text[:4096])
        except csv.Error:
            pass

        reader = csv.reader(io.StringIO(text), dialect)
        rows: list[list[str]] = []
        for row in reader:
            rows.append(row)
            if len(rows) >= MAX_ROWS + 1:
                break

        if not rows:
            self.info_label.configure(text="Empty file")
            return

        if has_header:
            headers = rows[0]
            data_rows = rows[1:]
        else:
            headers = [f"Col {i + 1}" for i in range(len(rows[0]))]
            data_rows = rows

        delim_name = repr(dialect.delimiter)
        row_count = len(data_rows)
        truncated = row_count >= MAX_ROWS
        label = f"Delimiter: {delim_name}  |  {row_count}{'+ (truncated)' if truncated else ''} rows  |  {len(headers)} cols"
        if has_header:
            label += "  |  header detected"
        self.info_label.configure(text=label)

        vsb = ttk.Scrollbar(self.tree_frame, orient=tk.VERTICAL)
        hsb = ttk.Scrollbar(self.tree_frame, orient=tk.HORIZONTAL)
        self.tree = ttk.Treeview(
            self.tree_frame,
            columns=headers,
            show="headings",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set,
            selectmode="browse",
        )
        vsb.configure(command=self.tree.yview)
        hsb.configure(command=self.tree.xview)

        for col in headers:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, minwidth=40)

        for row in data_rows:
            padded = row + [""] * max(0, len(headers) - len(row))
            self.tree.insert("", tk.END, values=padded[: len(headers)])

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        self.tree_frame.rowconfigure(0, weight=1)
        self.tree_frame.columnconfigure(0, weight=1)

    def clear(self) -> None:
        if self.tree:
            self.tree.destroy()
            self.tree = None
        self.info_label.configure(text="")

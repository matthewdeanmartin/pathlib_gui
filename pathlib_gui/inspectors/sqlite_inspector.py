"""SQLite database inspector — read-only."""

from __future__ import annotations

import sqlite3
import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Any, cast

from pathlib_gui.inspectors.base import BaseInspector

MAX_PREVIEW_ROWS = 200


class SqliteInspector(BaseInspector):
    label = "SQLite"

    def __init__(self, parent: tk.Misc, **kwargs: Any) -> None:
        super().__init__(parent, **kwargs)
        self.db_path: Path | None = None
        self.build_widgets()

    def build_widgets(self) -> None:
        ttk.Label(self, text="Backend: sqlite3 (read-only via URI)", foreground="gray").pack(anchor="w", padx=4, pady=2)

        pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        pane.pack(fill=tk.BOTH, expand=True)

        left = ttk.Frame(pane)
        pane.add(left, weight=1)

        ttk.Label(left, text="Tables").pack(anchor="w", padx=4)
        self.table_list = tk.Listbox(left, selectmode=tk.SINGLE, activestyle="none", exportselection=False)
        self.table_list.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        self.table_list.bind("<<ListboxSelect>>", self.on_table_select)

        right = ttk.Frame(pane)
        pane.add(right, weight=3)

        nb = ttk.Notebook(right)
        nb.pack(fill=tk.BOTH, expand=True)

        schema_frame = ttk.Frame(nb)
        nb.add(schema_frame, text="Schema")
        self.schema_text = tk.Text(schema_frame, wrap=tk.WORD, state=tk.DISABLED, relief=tk.FLAT, font=("Courier", 10))
        vsb = ttk.Scrollbar(schema_frame, orient=tk.VERTICAL, command=self.schema_text.yview)
        self.schema_text.configure(yscrollcommand=vsb.set)
        self.schema_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        rows_frame = ttk.Frame(nb)
        nb.add(rows_frame, text="Rows")
        self.rows_info = ttk.Label(rows_frame, text="", foreground="gray")
        self.rows_info.pack(anchor="w", padx=4)

        query_frame = ttk.Frame(rows_frame)
        query_frame.pack(fill=tk.X, padx=4, pady=2)
        ttk.Label(query_frame, text="SELECT").pack(side=tk.LEFT)
        self.query_var = tk.StringVar(value="* FROM <table> LIMIT 100")
        self.query_entry = ttk.Entry(query_frame, textvariable=self.query_var)
        self.query_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        ttk.Button(query_frame, text="Run", command=self.run_query, width=5).pack(side=tk.LEFT)

        self.rows_tree_frame = ttk.Frame(rows_frame)
        self.rows_tree_frame.pack(fill=tk.BOTH, expand=True)
        self.rows_tree: ttk.Treeview | None = None
        self.nb = nb

    def load(self, path: Path) -> None:
        self.db_path = path
        self.table_list.delete(0, tk.END)
        self.set_schema("")

        try:
            uri = path.as_uri() + "?mode=ro"
            conn = sqlite3.connect(uri, uri=True)
            cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = [row[0] for row in cur.fetchall()]
            conn.close()
        except sqlite3.Error as e:
            self.set_schema(f"Error opening database:\n{e}")
            return

        for t in tables:
            self.table_list.insert(tk.END, t)

        if tables:
            self.table_list.selection_set(0)
            self.load_table(tables[0])

    def on_table_select(self, event: tk.Event) -> None:
        curselection = cast(Callable[[], tuple[int, ...]], self.table_list.curselection)
        sel = curselection()
        if sel:
            self.load_table(self.table_list.get(sel[0]))

    def load_table(self, table: str) -> None:
        if not self.db_path:
            return
        self.query_var.set(f'* FROM "{table}" LIMIT 100')
        try:
            uri = self.db_path.as_uri() + "?mode=ro"
            conn = sqlite3.connect(uri, uri=True)
            schema_cur = conn.execute("SELECT sql FROM sqlite_master WHERE name=?", (table,))
            schema_row = schema_cur.fetchone()
            schema = schema_row[0] if schema_row else f"(no schema for {table})"
            conn.close()
        except sqlite3.Error as e:
            schema = f"Error: {e}"
        self.set_schema(schema)
        self.run_query()

    def run_query(self) -> None:
        if not self.db_path:
            return
        raw = self.query_var.get().strip()
        if not raw.upper().startswith("SELECT") and not raw.startswith("*"):
            sql = f"SELECT {raw}"
        else:
            sql = raw if raw.upper().startswith("SELECT") else f"SELECT {raw}"

        # Block any non-SELECT statements
        first_word = sql.strip().split()[0].upper()
        if first_word != "SELECT":
            messagebox.showwarning("Read-only", "Only SELECT queries are allowed.", parent=self)
            return

        try:
            uri = self.db_path.as_uri() + "?mode=ro"
            conn = sqlite3.connect(uri, uri=True)
            cur = conn.execute(sql)
            cols = [d[0] for d in cur.description] if cur.description else []
            rows = cur.fetchmany(MAX_PREVIEW_ROWS)
            conn.close()
        except sqlite3.Error as e:
            self.rows_info.configure(text=f"Error: {e}")
            return

        self.rebuild_rows_tree(cols, rows)
        self.rows_info.configure(text=f"{len(rows)} row(s) shown  (max {MAX_PREVIEW_ROWS})")

    def rebuild_rows_tree(self, columns: list[str], rows: list[tuple[object, ...]]) -> None:
        if self.rows_tree:
            self.rows_tree.destroy()
            self.rows_tree = None

        if not columns:
            return

        vsb = ttk.Scrollbar(self.rows_tree_frame, orient=tk.VERTICAL)
        hsb = ttk.Scrollbar(self.rows_tree_frame, orient=tk.HORIZONTAL)
        self.rows_tree = ttk.Treeview(
            self.rows_tree_frame,
            columns=columns,
            show="headings",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set,
            selectmode="browse",
        )
        vsb.configure(command=self.rows_tree.yview)
        hsb.configure(command=self.rows_tree.xview)
        for col in columns:
            self.rows_tree.heading(col, text=col)
            self.rows_tree.column(col, width=100, minwidth=40)
        for row in rows:
            self.rows_tree.insert("", tk.END, values=[str(v) if v is not None else "NULL" for v in row])

        self.rows_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        self.rows_tree_frame.rowconfigure(0, weight=1)
        self.rows_tree_frame.columnconfigure(0, weight=1)

    def set_schema(self, text: str) -> None:
        self.schema_text.configure(state=tk.NORMAL)
        self.schema_text.delete("1.0", tk.END)
        self.schema_text.insert("1.0", text)
        self.schema_text.configure(state=tk.DISABLED)

    def clear(self) -> None:
        self.db_path = None
        self.table_list.delete(0, tk.END)
        self.set_schema("")
        if self.rows_tree:
            self.rows_tree.destroy()
            self.rows_tree = None

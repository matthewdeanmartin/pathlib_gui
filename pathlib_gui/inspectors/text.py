"""Text file preview inspector."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import ttk
from typing import Any, Literal

from pathlib_gui.inspectors.base import BaseInspector

MAX_BYTES = 512 * 1024


def detect_encoding(path: Path) -> str:
    try:
        import tokenize

        with path.open("rb") as fh:
            enc = tokenize.detect_encoding(fh.readline)[0]
        return enc or "utf-8"
    except Exception:
        return "utf-8"


class TextInspector(BaseInspector):
    label = "Text"

    def __init__(self, parent: tk.Misc, **kwargs: Any) -> None:
        super().__init__(parent, **kwargs)
        self.path: Path | None = None
        self.show_line_numbers = tk.BooleanVar(value=True)
        self.wrap_var = tk.BooleanVar(value=True)
        self.search_var = tk.StringVar()
        self.encoding_var = tk.StringVar(value="utf-8")
        self.build_widgets()

    def build_widgets(self) -> None:
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=2, pady=2)

        ttk.Label(toolbar, text="Backend: Path.read_text / tokenize.detect_encoding", foreground="gray").pack(
            side=tk.LEFT, padx=4
        )
        ttk.Checkbutton(toolbar, text="Line nums", variable=self.show_line_numbers, command=self.reload).pack(
            side=tk.RIGHT
        )
        ttk.Checkbutton(toolbar, text="Wrap", variable=self.wrap_var, command=self.toggle_wrap).pack(side=tk.RIGHT)

        search_frame = ttk.Frame(self)
        search_frame.pack(fill=tk.X, padx=2)
        ttk.Label(search_frame, text="Find:").pack(side=tk.LEFT)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side=tk.LEFT, padx=2)
        search_entry.bind("<Return>", lambda e: self.find_next())
        ttk.Button(search_frame, text="Find", command=self.find_next, width=5).pack(side=tk.LEFT)
        ttk.Label(search_frame, text="Encoding:").pack(side=tk.LEFT, padx=(8, 2))
        ttk.Label(search_frame, textvariable=self.encoding_var, foreground="gray").pack(side=tk.LEFT)

        text_frame = ttk.Frame(self)
        text_frame.pack(fill=tk.BOTH, expand=True)

        self.line_text = tk.Text(
            text_frame,
            width=5,
            state=tk.DISABLED,
            background="#f0f0f0",
            foreground="gray",
            relief=tk.FLAT,
            wrap=tk.NONE,
        )
        self.main_text = tk.Text(
            text_frame,
            wrap=tk.WORD,
            state=tk.DISABLED,
            relief=tk.FLAT,
            undo=False,
        )
        vsb = ttk.Scrollbar(text_frame, orient=tk.VERTICAL)
        hsb = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.main_text.xview)

        vsb.configure(command=self.sync_scroll)
        self.main_text.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.line_text.configure(yscrollcommand=vsb.set)

        self.line_text.pack(side=tk.LEFT, fill=tk.Y)
        self.main_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(fill=tk.X)

        self.main_text.tag_configure("found", background="yellow")

    def sync_scroll(self, *args: object) -> None:
        self.main_text.yview(*args)
        self.line_text.yview(*args)

    def load(self, path: Path) -> None:
        self.path = path
        enc = detect_encoding(path)
        self.encoding_var.set(enc)
        try:
            raw = path.read_bytes()[:MAX_BYTES]
            content = raw.decode(enc, errors="replace")
        except OSError as e:
            content = f"(Error reading file: {e})"
        self.set_content(content)

    def reload(self) -> None:
        if self.path:
            self.load(self.path)

    def set_content(self, content: str) -> None:
        lines = content.splitlines()

        self.main_text.configure(state=tk.NORMAL)
        self.main_text.delete("1.0", tk.END)
        self.main_text.insert("1.0", content)
        self.main_text.configure(state=tk.DISABLED)

        self.line_text.configure(state=tk.NORMAL)
        self.line_text.delete("1.0", tk.END)
        if self.show_line_numbers.get():
            nums = "\n".join(str(i + 1) for i in range(len(lines)))
            self.line_text.insert("1.0", nums)
            self.line_text.pack(side=tk.LEFT, fill=tk.Y)
        else:
            self.line_text.pack_forget()
        self.line_text.configure(state=tk.DISABLED)

    def toggle_wrap(self) -> None:
        mode: Literal["word", "none"] = "word" if self.wrap_var.get() else "none"
        self.main_text.configure(wrap=mode)

    def find_next(self) -> None:
        term = self.search_var.get()
        if not term:
            return
        self.main_text.tag_remove("found", "1.0", tk.END)
        start = self.main_text.search(term, "insert", stopindex=tk.END)
        if not start:
            start = self.main_text.search(term, "1.0", stopindex=tk.END)
        if start:
            end = f"{start}+{len(term)}c"
            self.main_text.tag_add("found", start, end)
            self.main_text.mark_set("insert", end)
            self.main_text.see(start)

    def clear(self) -> None:
        self.path = None
        self.set_content("")

"""Binary / hex view inspector."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import ttk
from typing import Any

from pathlib_gui.inspectors.base import BaseInspector

MAX_BYTES = 64 * 1024
BYTES_PER_ROW = 16


def hex_dump(data: bytes) -> str:
    lines: list[str] = []
    for offset in range(0, len(data), BYTES_PER_ROW):
        chunk = data[offset : offset + BYTES_PER_ROW]
        hex_part = " ".join(f"{b:02x}" for b in chunk)
        hex_part = f"{hex_part:<{BYTES_PER_ROW * 3 - 1}}"
        ascii_part = "".join(chr(b) if 0x20 <= b <= 0x7E else "." for b in chunk)
        lines.append(f"{offset:08x}  {hex_part}  |{ascii_part}|")
    return "\n".join(lines)


class BinaryInspector(BaseInspector):
    label = "Binary"

    def __init__(self, parent: tk.Misc, **kwargs: Any) -> None:
        super().__init__(parent, **kwargs)
        self.build_widgets()

    def build_widgets(self) -> None:
        ttk.Label(self, text="Backend: Path.read_bytes()", foreground="gray").pack(anchor="w", padx=4, pady=2)
        self.info_label = ttk.Label(self, text="", foreground="gray")
        self.info_label.pack(anchor="w", padx=4)

        text_frame = ttk.Frame(self)
        text_frame.pack(fill=tk.BOTH, expand=True)

        self.text = tk.Text(
            text_frame,
            font=("Courier", 10),
            wrap=tk.NONE,
            state=tk.DISABLED,
            relief=tk.FLAT,
        )
        vsb = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.text.yview)
        hsb = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.text.xview)
        self.text.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(fill=tk.X)

    def load(self, path: Path) -> None:
        try:
            file_size = path.stat().st_size
            data = path.read_bytes()[:MAX_BYTES]
            truncated = file_size > MAX_BYTES
            shown = len(data)
            label = f"File size: {file_size:,} bytes"
            if truncated:
                label += f" — showing first {shown:,} bytes"
            self.info_label.configure(text=label)
            dump = hex_dump(data)
        except OSError as e:
            dump = f"(Error: {e})"
            self.info_label.configure(text="")

        self.text.configure(state=tk.NORMAL)
        self.text.delete("1.0", tk.END)
        self.text.insert("1.0", dump)
        self.text.configure(state=tk.DISABLED)

    def clear(self) -> None:
        self.text.configure(state=tk.NORMAL)
        self.text.delete("1.0", tk.END)
        self.text.configure(state=tk.DISABLED)
        self.info_label.configure(text="")

"""plist inspector — uses plistlib."""

from __future__ import annotations

import plistlib
import tkinter as tk
from pathlib import Path
from tkinter import ttk

from pathlib_gui.inspectors.base import BaseInspector


def _render(obj: object, indent: int = 0) -> str:
    pad = "  " * indent
    if isinstance(obj, dict):
        lines = ["{"]
        for k, v in obj.items():
            lines.append(f"{pad}  {k!r}: {_render(v, indent + 1)}")
        lines.append(pad + "}")
        return "\n".join(lines)
    if isinstance(obj, list):
        lines = ["["]
        for item in obj:
            lines.append(f"{pad}  {_render(item, indent + 1)}")
        lines.append(pad + "]")
        return "\n".join(lines)
    return repr(obj)


class PlistInspector(BaseInspector):
    label = "Plist"

    def __init__(self, parent: tk.Widget, **kwargs: object) -> None:
        super().__init__(parent, **kwargs)
        ttk.Label(self, text="Backend: plistlib.load", foreground="gray").pack(anchor="w", padx=4, pady=2)
        self.text = tk.Text(self, wrap=tk.WORD, state=tk.DISABLED, relief=tk.FLAT, font=("Courier", 10))
        sb = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.text.yview)
        self.text.configure(yscrollcommand=sb.set)
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

    def load(self, path: Path) -> None:
        self.text.configure(state=tk.NORMAL)
        self.text.delete("1.0", tk.END)
        try:
            with path.open("rb") as fh:
                data = plistlib.load(fh)
            content = _render(data)
        except Exception as e:
            content = f"Error reading plist:\n{e}"
        self.text.insert("1.0", content)
        self.text.configure(state=tk.DISABLED)

    def clear(self) -> None:
        self.text.configure(state=tk.NORMAL)
        self.text.delete("1.0", tk.END)
        self.text.configure(state=tk.DISABLED)

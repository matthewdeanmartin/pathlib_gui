"""Status bar widget."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any


class StatusBar(ttk.Frame):
    """A simple status bar shown at the bottom of the app."""

    def __init__(self, parent: tk.Misc, **kwargs: Any) -> None:
        super().__init__(parent, **kwargs)
        self.message_var = tk.StringVar(value="Ready")
        self.path_var = tk.StringVar(value="")

        self.message_label = ttk.Label(self, textvariable=self.message_var, anchor="w")
        self.message_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)

        ttk.Separator(self, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=2)

        self.path_label = ttk.Label(self, textvariable=self.path_var, anchor="e", foreground="gray")
        self.path_label.pack(side=tk.RIGHT, padx=4)

    def set_message(self, text: str) -> None:
        self.message_var.set(text)

    def set_path(self, text: str) -> None:
        self.path_var.set(text)

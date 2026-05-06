"""Pytest configuration — stub tkinter when not available (headless CI)."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock

try:
    import tkinter  # noqa: F401
except ModuleNotFoundError:
    _tk = MagicMock()
    for _mod in (
        "tkinter",
        "tkinter.ttk",
        "tkinter.messagebox",
        "tkinter.filedialog",
        "tkinter.simpledialog",
    ):
        sys.modules[_mod] = MagicMock()

"""Inspector registration and dispatch."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import ttk


class BaseInspector(ttk.Frame):
    """Common base for all file-type inspectors."""

    label: str = "Inspector"

    def __init__(self, parent: tk.Widget, **kwargs: object) -> None:
        super().__init__(parent, **kwargs)

    def load(self, path: Path) -> None:
        raise NotImplementedError

    def clear(self) -> None:
        pass


def inspector_for_path(parent: tk.Widget, path: Path) -> BaseInspector:
    """Return the most appropriate inspector for the given path."""
    from pathlib_gui.inspectors.binary import BinaryInspector
    from pathlib_gui.inspectors.csv_inspector import CsvInspector
    from pathlib_gui.inspectors.image_inspector import SUPPORTED as IMAGE_SUFFIXES, ImageInspector
    from pathlib_gui.inspectors.json_inspector import JsonInspector
    from pathlib_gui.inspectors.sqlite_inspector import SqliteInspector
    from pathlib_gui.inspectors.text import TextInspector
    from pathlib_gui.inspectors.toml_inspector import TomlInspector
    from pathlib_gui.inspectors.wave_inspector import WaveInspector
    from pathlib_gui.inspectors.xml_inspector import XmlInspector

    suffix = path.suffix.lower()

    if suffix in (".db", ".sqlite", ".sqlite3"):
        return SqliteInspector(parent)
    if suffix == ".wav":
        return WaveInspector(parent)
    if suffix == ".csv":
        return CsvInspector(parent)
    if suffix == ".json":
        return JsonInspector(parent)
    if suffix in (".toml",):
        return TomlInspector(parent)
    if suffix in (".xml", ".xhtml", ".svg", ".plist"):
        return XmlInspector(parent)
    if suffix in IMAGE_SUFFIXES:
        return ImageInspector(parent)
    if suffix in (
        ".txt", ".md", ".rst", ".py", ".pyw", ".js", ".ts", ".css", ".html",
        ".htm", ".yaml", ".yml", ".ini", ".cfg", ".conf", ".sh", ".bat",
        ".c", ".cpp", ".h", ".java", ".rb", ".go", ".rs", ".log", ".diff",
        ".patch", ".gitignore", ".env",
    ):
        return TextInspector(parent)

    try:
        chunk = path.read_bytes()[:512]
        if is_text_like(chunk):
            return TextInspector(parent)
    except OSError:
        pass

    return BinaryInspector(parent)


def is_text_like(data: bytes) -> bool:
    try:
        data.decode("utf-8")
        return True
    except UnicodeDecodeError:
        pass
    printable = sum(1 for b in data if 0x09 <= b <= 0x0D or 0x20 <= b <= 0x7E)
    return len(data) > 0 and printable / len(data) > 0.75

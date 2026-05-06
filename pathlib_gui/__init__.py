"""pathlib_gui — A Tkinter GUI for Python's filesystem standard library."""

from pathlib import Path

from pathlib_gui.__about__ import __version__
from pathlib_gui.app import run_app

__all__ = ["__version__", "launch"]


def launch(path: str | Path | None = None) -> None:
    """Launch the pathlib_gui application, optionally starting at a given path."""
    p = Path(path).expanduser().resolve() if path else None
    run_app(initial_path=p)

"""Command-line entry point for pathlib_gui."""

from __future__ import annotations

import argparse
from pathlib import Path

from pathlib_gui.__about__ import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pathlib-gui",
        description="A Tkinter GUI for Python's filesystem standard library.",
        epilog="Internet-backed filesystems are out of scope.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    subparsers = parser.add_subparsers(dest="command")

    browse = subparsers.add_parser("browse", help="Browse a directory (default command)")
    browse.add_argument("path", nargs="?", default=".", help="Starting directory")

    compare = subparsers.add_parser("compare", help="Open compare mode for two files or directories")
    compare.add_argument("left", help="Left file or directory")
    compare.add_argument("right", help="Right file or directory")

    archive_p = subparsers.add_parser("archive", help="Open an archive file in archive browser")
    archive_p.add_argument("file", help="Archive file to open")

    extract = subparsers.add_parser("extract", help="Open archive for extraction")
    extract.add_argument("file", help="Archive file to extract")

    inspect = subparsers.add_parser("inspect", help="Open app with a file pre-selected for inspection")
    inspect.add_argument("file", help="File to inspect")

    parser.add_argument("path", nargs="?", default=None, help="Starting directory (when no subcommand given)")

    return parser


def main() -> None:
    """Run the pathlib_gui CLI."""
    parser = build_parser()
    args = parser.parse_args()

    import tkinter as tk
    from pathlib_gui.app import PathlibGuiApp

    if args.command == "compare":
        left = Path(args.left).resolve()
        right = Path(args.right).resolve()
        root = tk.Tk()
        app = PathlibGuiApp(root, initial_path=left.parent if left.is_file() else left)
        app.open_compare(left, right)
        root.mainloop()
        return

    if args.command in ("archive", "extract"):
        p = Path(args.file).resolve()
        root = tk.Tk()
        app = PathlibGuiApp(root, initial_path=p.parent)
        if p.exists():
            app.load_archive(p)
        root.mainloop()
        return

    if args.command == "inspect":
        p = Path(args.file).resolve()
        root = tk.Tk()
        app = PathlibGuiApp(root, initial_path=p.parent if p.exists() else None)
        if p.is_file():
            from pathlib_gui.models.paths import PathInfo
            root.after(100, lambda: app.inspector.show(PathInfo.from_path(p)))
        root.mainloop()
        return

    path_str = getattr(args, "path", None)
    initial: Path | None = None
    if path_str:
        p = Path(path_str).expanduser().resolve()
        if p.exists():
            initial = p if p.is_dir() else p.parent

    from pathlib_gui.app import run_app
    run_app(initial_path=initial)

"""Command-line entry point for pathlib_gui."""

from __future__ import annotations

import argparse

from pathlib_gui.__about__ import __version__


def main() -> None:
    """Run the pathlib_gui CLI."""
    parser = argparse.ArgumentParser(
        prog="pathlib_gui",
        description="Tkinter gui for all the filesystem related things in the python standard library",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    # TODO: add CLI arguments here
    args = parser.parse_args()
    _ = args  # remove once arguments are used

    from pathlib_gui.app import run_app

    run_app()


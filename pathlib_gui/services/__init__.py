"""Service layer for pathlib_gui — public API."""

from __future__ import annotations

from pathlib import Path

from pathlib_gui.models.paths import PathInfo


def inspect_path(path: Path) -> PathInfo:
    """Return a PathInfo snapshot for *path*."""
    return PathInfo.from_path(path)


def compare_files(
    left: Path,
    right: Path,
    ignore_whitespace: bool = False,
    ignore_case: bool = False,
):
    """Return a DiffResult for two text files.  Backend: difflib."""
    from pathlib_gui.services.diff_service import diff_files

    return diff_files(left, right, ignore_whitespace=ignore_whitespace, ignore_case=ignore_case)


def list_archive(path: Path):
    """Return a list of ArchiveMember objects for a ZIP or TAR archive."""
    from pathlib_gui.services.archive_service import list_members

    return list_members(path)


__all__ = ["compare_files", "inspect_path", "list_archive"]

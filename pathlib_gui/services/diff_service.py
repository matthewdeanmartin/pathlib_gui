"""Diff service — difflib wrappers returning structured results."""

from __future__ import annotations

import difflib
from pathlib import Path

from pathlib_gui.models.compare import DiffResult


def diff_files(
    left: Path,
    right: Path,
    ignore_whitespace: bool = False,
    ignore_case: bool = False,
) -> DiffResult:
    def read(p: Path) -> list[str]:
        try:
            text = p.read_text(errors="replace")
        except OSError:
            text = ""
        lines = text.splitlines(keepends=True)
        if ignore_case:
            lines = [l.lower() for l in lines]
        if ignore_whitespace:
            lines = [" ".join(l.split()) + "\n" for l in lines]
        return lines

    left_lines = read(left)
    right_lines = read(right)

    same = left_lines == right_lines

    unified = list(
        difflib.unified_diff(
            left_lines,
            right_lines,
            fromfile=str(left),
            tofile=str(right),
        )
    )
    context = list(
        difflib.context_diff(
            left_lines,
            right_lines,
            fromfile=str(left),
            tofile=str(right),
        )
    )
    nd = list(difflib.ndiff(left_lines, right_lines))

    return DiffResult(
        left_path=left,
        right_path=right,
        left_lines=left_lines,
        right_lines=right_lines,
        unified=unified,
        context=context,
        ndiff=nd,
        same=same,
    )


def html_diff(left: Path, right: Path) -> str:
    left_lines = left.read_text(errors="replace").splitlines(keepends=True)
    right_lines = right.read_text(errors="replace").splitlines(keepends=True)
    hd = difflib.HtmlDiff(wrapcolumn=80)
    return hd.make_file(left_lines, right_lines, fromdesc=str(left), todesc=str(right))


def similarity_ratio(left: Path, right: Path) -> float:
    left_lines = left.read_text(errors="replace").splitlines()
    right_lines = right.read_text(errors="replace").splitlines()
    sm = difflib.SequenceMatcher(None, left_lines, right_lines)
    return sm.ratio()

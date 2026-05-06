"""Diff and directory comparison result models."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class DiffResult:
    left_path: Path
    right_path: Path
    left_lines: list[str]
    right_lines: list[str]
    unified: list[str] = field(default_factory=list)
    context: list[str] = field(default_factory=list)
    ndiff: list[str] = field(default_factory=list)
    same: bool = False


@dataclass
class DirCompareResult:
    left: Path
    right: Path
    only_left: list[str] = field(default_factory=list)
    only_right: list[str] = field(default_factory=list)
    same_files: list[str] = field(default_factory=list)
    diff_files: list[str] = field(default_factory=list)
    funny_files: list[str] = field(default_factory=list)
    common_dirs: list[str] = field(default_factory=list)

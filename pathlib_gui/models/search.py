"""Search query and result models."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SearchQuery:
    root: Path
    name_contains: str = ""
    glob_pattern: str = ""
    regex_pattern: str = ""
    suffix: str = ""
    min_size: int = 0
    max_size: int = 0
    content_contains: str = ""
    find_empty_files: bool = False
    find_empty_dirs: bool = False
    find_broken_symlinks: bool = False
    find_duplicates: bool = False
    follow_symlinks: bool = False


@dataclass
class SearchResult:
    path: Path
    match_reason: str = ""

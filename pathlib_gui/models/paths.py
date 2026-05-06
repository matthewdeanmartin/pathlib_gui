"""Path metadata model."""

from __future__ import annotations

import mimetypes
import os
import stat
import sys
from dataclasses import dataclass
from pathlib import Path


def _owner_group(st: os.stat_result) -> tuple[str, str]:
    if sys.platform == "win32":
        return "", ""
    try:
        import pwd
        owner = pwd.getpwuid(st.st_uid).pw_name
    except Exception:
        owner = str(st.st_uid)
    try:
        import grp
        group = grp.getgrgid(st.st_gid).gr_name
    except Exception:
        group = str(st.st_gid)
    return owner, group


@dataclass
class PathInfo:
    """Snapshot of metadata for a filesystem path."""

    path: Path
    name: str
    suffix: str
    stem: str
    size: int
    modified: float
    created: float
    accessed: float
    mode: int
    is_file: bool
    is_dir: bool
    is_symlink: bool
    mime_type: str
    exists: bool
    owner: str
    group: str

    @property
    def is_broken_symlink(self) -> bool:
        return self.is_symlink and not self.path.exists()

    @staticmethod
    def from_path(p: Path) -> PathInfo:
        try:
            st = p.lstat()
            exists = True
            size = st.st_size if not p.is_dir() else 0
            modified = st.st_mtime
            created = st.st_ctime
            accessed = st.st_atime
            mode = st.st_mode
            owner, group = _owner_group(st)
        except OSError:
            exists = False
            size = 0
            modified = 0.0
            created = 0.0
            accessed = 0.0
            mode = 0
            owner = ""
            group = ""

        mime_type, _ = mimetypes.guess_type(p.name)

        return PathInfo(
            path=p,
            name=p.name,
            suffix=p.suffix,
            stem=p.stem,
            size=size,
            modified=modified,
            created=created,
            accessed=accessed,
            mode=mode,
            is_file=p.is_file(),
            is_dir=p.is_dir(),
            is_symlink=p.is_symlink(),
            mime_type=mime_type or "",
            exists=exists,
            owner=owner,
            group=group,
        )

    def permissions_string(self) -> str:
        try:
            return stat.filemode(self.mode)
        except Exception:
            return "----------"

    def size_human(self) -> str:
        if self.is_dir:
            return ""
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if self.size < 1024:
                return f"{self.size:.1f} {unit}"
            self.size /= 1024
        return f"{self.size:.1f} PB"

    def kind_label(self) -> str:
        if self.is_symlink:
            return "Symlink"
        if self.is_dir:
            return "Folder"
        if self.mime_type:
            return self.mime_type
        return "File" if self.suffix == "" else f"{self.suffix.lstrip('.')} file"


def format_size(size: int, is_dir: bool = False) -> str:
    if is_dir:
        return ""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size = int(size / 1024)
    return f"{size:.1f} PB"


def list_directory(path: Path, show_hidden: bool = False) -> list[PathInfo]:
    entries: list[PathInfo] = []
    try:
        for child in path.iterdir():
            if not show_hidden and child.name.startswith("."):
                continue
            entries.append(PathInfo.from_path(child))
    except PermissionError:
        pass
    return entries

"""Archive member data model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ArchiveMember:
    """Metadata for one member inside an archive."""

    name: str
    size: int
    compressed_size: int
    modified: float
    mode: int
    crc: int
    is_dir: bool
    is_symlink: bool
    link_target: str


def format_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n = int(n / 1024)
    return f"{n:.1f} TB"


def compression_ratio(member: ArchiveMember) -> str:
    if member.size == 0 or member.is_dir:
        return ""
    ratio = 100 * (1 - member.compressed_size / member.size)
    return f"{ratio:.0f}%"

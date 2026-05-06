"""Archive service — zipfile/tarfile open/list/extract/create with safety checks."""

from __future__ import annotations

import datetime
import tarfile
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Literal

from pathlib_gui.models.archive import ArchiveMember

ArchiveFormat = Literal["zip", "tar", "tar.gz", "tar.bz2", "tar.xz", "gz", "bz2", "xz"]
ArchiveCompression = int | Literal["", "gz", "bz2", "xz"]
TarWriteMode = Literal["w", "w:gz", "w:bz2", "w:xz"]


def is_zip(path: Path) -> bool:
    return zipfile.is_zipfile(path)


def is_tar(path: Path) -> bool:
    return tarfile.is_tarfile(str(path))


def list_zip(path: Path) -> list[ArchiveMember]:
    members: list[ArchiveMember] = []
    with zipfile.ZipFile(path, "r") as zf:
        for info in zf.infolist():
            dt = datetime.datetime(*info.date_time).timestamp() if info.date_time[0] > 1970 else 0.0
            members.append(
                ArchiveMember(
                    name=info.filename,
                    size=info.file_size,
                    compressed_size=info.compress_size,
                    modified=dt,
                    mode=info.external_attr >> 16,
                    crc=info.CRC,
                    is_dir=info.is_dir(),
                    is_symlink=bool((info.external_attr >> 16) & 0xA000),
                    link_target="",
                )
            )
    return members


def list_tar(path: Path) -> list[ArchiveMember]:
    members: list[ArchiveMember] = []
    with tarfile.open(str(path), "r:*") as tf:
        for m in tf.getmembers():
            members.append(
                ArchiveMember(
                    name=m.name,
                    size=m.size,
                    compressed_size=m.size,
                    modified=m.mtime,
                    mode=m.mode,
                    crc=0,
                    is_dir=m.isdir(),
                    is_symlink=m.issym(),
                    link_target=m.linkname if m.issym() else "",
                )
            )
    return members


def list_members(path: Path) -> list[ArchiveMember]:
    if zipfile.is_zipfile(path):
        return list_zip(path)
    if tarfile.is_tarfile(str(path)):
        return list_tar(path)
    raise ValueError(f"Not a recognised archive: {path}")


def safe_extract_path(member_name: str, dest: Path) -> Path | None:
    """Return the resolved destination or None if the member would escape dest."""
    # Reject Windows drive-letter roots early (e.g. C:/, C:\)
    import re as _re

    if _re.match(r"^[A-Za-z]:[/\\]", member_name):
        return None
    # Normalise using PurePosixPath to collapse .. and strip leading /
    clean = PurePosixPath(member_name.replace("\\", "/"))
    parts = [p for p in clean.parts if p not in ("", ".", "..")]
    if not parts:
        return None
    rel = Path(*parts)
    if rel.is_absolute():
        return None
    resolved = (dest / rel).resolve()
    try:
        resolved.relative_to(dest.resolve())
    except ValueError:
        return None
    return resolved


def extract_zip_member(path: Path, member_name: str, dest: Path) -> Path:
    target = safe_extract_path(member_name, dest)
    if target is None:
        raise ValueError(f"Unsafe archive member path: {member_name!r}")
    with zipfile.ZipFile(path, "r") as zf:
        data = zf.read(member_name)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return target


def extract_zip_all(path: Path, dest: Path) -> list[str]:
    skipped: list[str] = []
    with zipfile.ZipFile(path, "r") as zf:
        for info in zf.infolist():
            target = safe_extract_path(info.filename, dest)
            if target is None:
                skipped.append(info.filename)
                continue
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(zf.read(info.filename))
    return skipped


def extract_tar_member(path: Path, member_name: str, dest: Path) -> Path:
    target = safe_extract_path(member_name, dest)
    if target is None:
        raise ValueError(f"Unsafe archive member path: {member_name!r}")
    with tarfile.open(str(path), "r:*") as tf:
        m = tf.getmember(member_name)
        if m.isfile():
            fobj = tf.extractfile(m)
            if fobj:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(fobj.read())
    return target


def extract_tar_all(path: Path, dest: Path) -> list[str]:
    skipped: list[str] = []
    with tarfile.open(str(path), "r:*") as tf:
        for m in tf.getmembers():
            target = safe_extract_path(m.name, dest)
            if target is None:
                skipped.append(m.name)
                continue
            if m.isdir():
                target.mkdir(parents=True, exist_ok=True)
            elif m.isfile():
                fobj = tf.extractfile(m)
                if fobj:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(fobj.read())
    return skipped


def preview_member(archive_path: Path, member_name: str) -> Path:
    """Extract a single member to a temp dir and return the temp path."""
    tmp = Path(tempfile.mkdtemp(prefix="pathlib_gui_"))
    if zipfile.is_zipfile(archive_path):
        return extract_zip_member(archive_path, member_name, tmp)
    return extract_tar_member(archive_path, member_name, tmp)


def test_zip(path: Path) -> str | None:
    """Returns None if OK, or the first bad member name."""
    with zipfile.ZipFile(path, "r") as zf:
        return zf.testzip()


def test_tar(path: Path) -> list[str]:
    """Returns list of member names that could not be read."""
    errors: list[str] = []
    with tarfile.open(str(path), "r:*") as tf:
        for m in tf.getmembers():
            if m.isfile():
                try:
                    fobj = tf.extractfile(m)
                    if fobj:
                        fobj.read()
                except Exception:
                    errors.append(m.name)
    return errors


ARCHIVE_PRESETS = [
    ("ZIP — normal", "zip", zipfile.ZIP_STORED),
    ("ZIP — deflated", "zip", zipfile.ZIP_DEFLATED),
    ("TAR — uncompressed", "tar", ""),
    ("TAR.GZ", "tar.gz", "gz"),
    ("TAR.BZ2", "tar.bz2", "bz2"),
    ("TAR.XZ", "tar.xz", "xz"),
    ("GZIP single file", "gz", ""),
    ("BZIP2 single file", "bz2", ""),
    ("XZ single file", "xz", ""),
]


def create_zip(sources: list[Path], dest: Path, compression: int = zipfile.ZIP_DEFLATED) -> None:
    with zipfile.ZipFile(dest, "w", compression=compression) as zf:
        for src in sources:
            if src.is_dir():
                for f in src.rglob("*"):
                    zf.write(str(f), str(f.relative_to(src.parent)))
            else:
                zf.write(str(src), src.name)


def create_tar(sources: list[Path], dest: Path, mode: TarWriteMode = "w:gz") -> None:
    with tarfile.open(str(dest), mode) as tf:
        for src in sources:
            tf.add(src, arcname=src.name)


def create_gz(source: Path, dest: Path) -> None:
    import gzip

    with source.open("rb") as src_fh, gzip.open(str(dest), "wb") as gz_fh:
        gz_fh.write(src_fh.read())


def create_bz2(source: Path, dest: Path) -> None:
    import bz2

    with source.open("rb") as src_fh, bz2.open(str(dest), "wb") as bz_fh:
        bz_fh.write(src_fh.read())


def create_xz(source: Path, dest: Path) -> None:
    import lzma

    with source.open("rb") as src_fh, lzma.open(str(dest), "wb") as xz_fh:
        xz_fh.write(src_fh.read())

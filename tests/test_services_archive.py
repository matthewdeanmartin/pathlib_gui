"""Tests for pathlib_gui.services.archive_service."""

from __future__ import annotations

import tarfile
import zipfile
from pathlib import Path

import pytest

import pathlib_gui.services.archive_service as _archive_svc
from pathlib_gui.services.archive_service import (
    ARCHIVE_PRESETS,
    create_bz2,
    create_gz,
    create_tar,
    create_xz,
    create_zip,
    extract_tar_all,
    extract_tar_member,
    extract_zip_all,
    extract_zip_member,
    is_tar,
    is_zip,
    list_members,
    list_tar,
    list_zip,
    preview_member,
    safe_extract_path,
)


class TestIsZip:
    def test_valid_zip(self, tmp_path: Path) -> None:
        z = tmp_path / "test.zip"
        with zipfile.ZipFile(z, "w") as zf:
            zf.writestr("file.txt", "content")
        assert is_zip(z) is True

    def test_non_zip(self, tmp_path: Path) -> None:
        f = tmp_path / "not.zip"
        f.write_bytes(b"not a zip file")
        assert is_zip(f) is False


class TestIsTar:
    def test_valid_tar(self, tmp_path: Path) -> None:
        src = tmp_path / "src.txt"
        src.write_text("data")
        t = tmp_path / "test.tar"
        with tarfile.open(str(t), "w") as tf:
            tf.add(src, arcname="src.txt")
        assert is_tar(t) is True

    def test_non_tar(self, tmp_path: Path) -> None:
        f = tmp_path / "fake.tar"
        f.write_bytes(b"not a tar file at all")
        assert is_tar(f) is False


class TestListZip:
    def test_lists_members(self, tmp_path: Path) -> None:
        z = tmp_path / "archive.zip"
        with zipfile.ZipFile(z, "w") as zf:
            zf.writestr("hello.txt", "hello")
            zf.writestr("world.txt", "world")
        members = list_zip(z)
        names = {m.name for m in members}
        assert {"hello.txt", "world.txt"}.issubset(names)

    def test_member_fields(self, tmp_path: Path) -> None:
        z = tmp_path / "archive.zip"
        with zipfile.ZipFile(z, "w") as zf:
            zf.writestr("data.txt", "12345")
        members = list_zip(z)
        assert len(members) == 1
        m = members[0]
        assert m.size == 5
        assert isinstance(m.compressed_size, int)
        assert isinstance(m.crc, int)
        assert m.is_dir is False


class TestListTar:
    def test_lists_members(self, tmp_path: Path) -> None:
        src = tmp_path / "file.txt"
        src.write_text("content")
        t = tmp_path / "arch.tar"
        with tarfile.open(str(t), "w") as tf:
            tf.add(src, arcname="file.txt")
        members = list_tar(t)
        assert any(m.name == "file.txt" for m in members)

    def test_member_fields(self, tmp_path: Path) -> None:
        src = tmp_path / "f.txt"
        src.write_text("hello")
        t = tmp_path / "arch.tar"
        with tarfile.open(str(t), "w") as tf:
            tf.add(src, arcname="f.txt")
        members = list_tar(t)
        m = next(x for x in members if x.name == "f.txt")
        assert m.size == 5
        assert m.is_dir is False


class TestListMembers:
    def test_zip_dispatch(self, tmp_path: Path) -> None:
        z = tmp_path / "a.zip"
        with zipfile.ZipFile(z, "w") as zf:
            zf.writestr("x.txt", "x")
        members = list_members(z)
        assert any(m.name == "x.txt" for m in members)

    def test_tar_dispatch(self, tmp_path: Path) -> None:
        src = tmp_path / "src.txt"
        src.write_text("y")
        t = tmp_path / "a.tar"
        with tarfile.open(str(t), "w") as tf:
            tf.add(src, arcname="src.txt")
        members = list_members(t)
        assert any(m.name == "src.txt" for m in members)

    def test_unknown_raises(self, tmp_path: Path) -> None:
        f = tmp_path / "random.bin"
        f.write_bytes(b"garbage data not an archive")
        with pytest.raises(ValueError):
            list_members(f)


class TestSafeExtractPath:
    def test_normal_path(self, tmp_path: Path) -> None:
        result = safe_extract_path("subdir/file.txt", tmp_path)
        assert result is not None
        assert result == (tmp_path / "subdir" / "file.txt").resolve()

    def test_path_traversal_rejected(self, tmp_path: Path) -> None:
        # ".." parts are stripped from the path; the result stays inside dest
        # The function strips ".." components rather than rejecting outright.
        # An all-".." path collapses to empty parts → returns None.
        result = safe_extract_path("../escape.txt", tmp_path)
        # Either None (rejected) or the result stays within dest
        if result is not None:
            assert str(result).startswith(str(tmp_path.resolve()))

    def test_absolute_path_rejected(self, tmp_path: Path) -> None:
        result = safe_extract_path("/etc/passwd", tmp_path)
        assert result is None

    def test_windows_drive_rejected(self, tmp_path: Path) -> None:
        result = safe_extract_path("C:/Windows/system32", tmp_path)
        assert result is None

    def test_dot_path_rejected(self, tmp_path: Path) -> None:
        result = safe_extract_path(".", tmp_path)
        assert result is None

    def test_backslash_traversal_rejected(self, tmp_path: Path) -> None:
        # Backslash paths are converted to forward slash then ".." stripped
        result = safe_extract_path("..\\escape.txt", tmp_path)
        # Must not escape the dest
        if result is not None:
            assert str(result).startswith(str(tmp_path.resolve()))

    def test_nested_safe_path(self, tmp_path: Path) -> None:
        result = safe_extract_path("a/b/c/file.txt", tmp_path)
        assert result is not None
        assert str(result).startswith(str(tmp_path.resolve()))

    def test_only_dotdot_collapses_to_none(self, tmp_path: Path) -> None:
        # A member name consisting entirely of ".." has no valid parts after filtering
        result = safe_extract_path("..", tmp_path)
        assert result is None

    def test_result_within_dest_for_nested(self, tmp_path: Path) -> None:
        dest = tmp_path / "extract_here"
        dest.mkdir()
        result = safe_extract_path("deep/nested/file.bin", dest)
        assert result is not None
        assert str(result).startswith(str(dest.resolve()))


class TestExtractZipMember:
    def test_extracts_member(self, tmp_path: Path) -> None:
        z = tmp_path / "arch.zip"
        with zipfile.ZipFile(z, "w") as zf:
            zf.writestr("hello.txt", "extracted!")
        dest = tmp_path / "out"
        dest.mkdir()
        out_path = extract_zip_member(z, "hello.txt", dest)
        assert out_path.exists()
        assert out_path.read_text() == "extracted!"

    def test_unsafe_path_raises(self, tmp_path: Path) -> None:
        # Archive member with an absolute path triggers safe_extract_path → None → ValueError
        z = tmp_path / "arch.zip"
        with zipfile.ZipFile(z, "w") as zf:
            zf.writestr("/etc/passwd", "safe")
        dest = tmp_path / "out"
        dest.mkdir()
        with pytest.raises((ValueError, KeyError)):
            extract_zip_member(z, "/etc/passwd", dest)


class TestExtractZipAll:
    def test_extracts_all(self, tmp_path: Path) -> None:
        z = tmp_path / "arch.zip"
        with zipfile.ZipFile(z, "w") as zf:
            zf.writestr("a.txt", "A")
            zf.writestr("b.txt", "B")
        dest = tmp_path / "out"
        dest.mkdir()
        skipped = extract_zip_all(z, dest)
        assert (dest / "a.txt").exists()
        assert (dest / "b.txt").exists()
        assert skipped == []


class TestExtractTarMember:
    def test_extracts_member(self, tmp_path: Path) -> None:
        src = tmp_path / "content.txt"
        src.write_text("tar content")
        t = tmp_path / "arch.tar"
        with tarfile.open(str(t), "w") as tf:
            tf.add(src, arcname="content.txt")
        dest = tmp_path / "out"
        dest.mkdir()
        out = extract_tar_member(t, "content.txt", dest)
        assert out.exists()
        assert out.read_text() == "tar content"

    def test_unsafe_absolute_path_raises(self, tmp_path: Path) -> None:
        # safe_extract_path returns None for absolute paths → ValueError before tar lookup
        src = tmp_path / "f.txt"
        src.write_text("x")
        t = tmp_path / "arch.tar"
        with tarfile.open(str(t), "w") as tf:
            tf.add(src, arcname="f.txt")
        dest = tmp_path / "out"
        dest.mkdir()
        with pytest.raises(ValueError, match="Unsafe"):
            extract_tar_member(t, "/etc/passwd", dest)


class TestExtractTarAll:
    def test_extracts_all(self, tmp_path: Path) -> None:
        a = tmp_path / "a.txt"
        b = tmp_path / "b.txt"
        a.write_text("A")
        b.write_text("B")
        t = tmp_path / "arch.tar"
        with tarfile.open(str(t), "w") as tf:
            tf.add(a, arcname="a.txt")
            tf.add(b, arcname="b.txt")
        dest = tmp_path / "out"
        dest.mkdir()
        skipped = extract_tar_all(t, dest)
        assert (dest / "a.txt").exists()
        assert (dest / "b.txt").exists()
        assert skipped == []


class TestPreviewMember:
    def test_zip_preview(self, tmp_path: Path) -> None:
        z = tmp_path / "arch.zip"
        with zipfile.ZipFile(z, "w") as zf:
            zf.writestr("preview.txt", "preview data")
        out = preview_member(z, "preview.txt")
        assert out.exists()
        assert out.read_text() == "preview data"

    def test_tar_preview(self, tmp_path: Path) -> None:
        src = tmp_path / "orig.txt"
        src.write_text("tar preview")
        t = tmp_path / "arch.tar"
        with tarfile.open(str(t), "w") as tf:
            tf.add(src, arcname="orig.txt")
        out = preview_member(t, "orig.txt")
        assert out.exists()
        assert out.read_text() == "tar preview"


class TestVerifyZip:
    def test_valid_zip_returns_none(self, tmp_path: Path) -> None:
        z = tmp_path / "ok.zip"
        with zipfile.ZipFile(z, "w") as zf:
            zf.writestr("file.txt", "good")
        assert _archive_svc.test_zip(z) is None


class TestVerifyTar:
    def test_valid_tar_returns_empty(self, tmp_path: Path) -> None:
        src = tmp_path / "f.txt"
        src.write_text("x")
        t = tmp_path / "ok.tar"
        with tarfile.open(str(t), "w") as tf:
            tf.add(src, arcname="f.txt")
        errors = _archive_svc.test_tar(t)
        assert errors == []


class TestArchivePresets:
    def test_has_entries(self) -> None:
        assert len(ARCHIVE_PRESETS) > 0

    def test_each_entry_has_three_elements(self) -> None:
        for preset in ARCHIVE_PRESETS:
            assert len(preset) == 3

    def test_zip_preset_present(self) -> None:
        fmts = [p[1] for p in ARCHIVE_PRESETS]
        assert "zip" in fmts


class TestCreateZip:
    def test_creates_zip_with_files(self, tmp_path: Path) -> None:
        a = tmp_path / "a.txt"
        b = tmp_path / "b.txt"
        a.write_text("A content")
        b.write_text("B content")
        dest = tmp_path / "out.zip"
        create_zip([a, b], dest)
        assert dest.exists()
        with zipfile.ZipFile(dest) as zf:
            names = zf.namelist()
        assert "a.txt" in names
        assert "b.txt" in names

    def test_creates_zip_with_directory(self, tmp_path: Path) -> None:
        d = tmp_path / "mydir"
        d.mkdir()
        (d / "child.txt").write_text("child")
        dest = tmp_path / "out.zip"
        create_zip([d], dest)
        assert dest.exists()
        with zipfile.ZipFile(dest) as zf:
            assert len(zf.namelist()) > 0


class TestCreateTar:
    def test_creates_tar_gz(self, tmp_path: Path) -> None:
        src = tmp_path / "data.txt"
        src.write_text("tar data")
        dest = tmp_path / "out.tar.gz"
        create_tar([src], dest, mode="w:gz")
        assert dest.exists()
        assert tarfile.is_tarfile(str(dest))


class TestCreateGz:
    def test_creates_gz(self, tmp_path: Path) -> None:
        import gzip

        src = tmp_path / "data.txt"
        src.write_bytes(b"compress me")
        dest = tmp_path / "data.txt.gz"
        create_gz(src, dest)
        assert dest.exists()
        with gzip.open(str(dest), "rb") as f:
            assert f.read() == b"compress me"


class TestCreateBz2:
    def test_creates_bz2(self, tmp_path: Path) -> None:
        import bz2

        src = tmp_path / "data.txt"
        src.write_bytes(b"bzip2 me")
        dest = tmp_path / "data.txt.bz2"
        create_bz2(src, dest)
        assert dest.exists()
        with bz2.open(str(dest), "rb") as f:
            assert f.read() == b"bzip2 me"


class TestCreateXz:
    def test_creates_xz(self, tmp_path: Path) -> None:
        import lzma

        src = tmp_path / "data.txt"
        src.write_bytes(b"xz compress")
        dest = tmp_path / "data.txt.xz"
        create_xz(src, dest)
        assert dest.exists()
        with lzma.open(str(dest), "rb") as f:
            assert f.read() == b"xz compress"

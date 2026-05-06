"""Tests for pathlib_gui.models.paths."""

from __future__ import annotations

from pathlib import Path


from pathlib_gui.models.paths import PathInfo, format_size, list_directory


class TestFormatSize:
    def test_bytes(self) -> None:
        assert format_size(512) == "512.0 B"

    def test_kilobytes(self) -> None:
        assert format_size(1024) == "1.0 KB"

    def test_megabytes(self) -> None:
        assert format_size(1024 * 1024) == "1.0 MB"

    def test_gigabytes(self) -> None:
        assert format_size(1024**3) == "1.0 GB"

    def test_terabytes(self) -> None:
        assert format_size(1024**4) == "1.0 TB"

    def test_zero(self) -> None:
        assert format_size(0) == "0.0 B"

    def test_is_dir_returns_empty(self) -> None:
        assert format_size(1024, is_dir=True) == ""

    def test_large_value_petabytes(self) -> None:
        result = format_size(1024**5)
        assert "PB" in result


class TestPathInfoFromPath:
    def test_file_basic_fields(self, tmp_path: Path) -> None:
        f = tmp_path / "hello.txt"
        f.write_text("hello")
        info = PathInfo.from_path(f)
        assert info.name == "hello.txt"
        assert info.suffix == ".txt"
        assert info.stem == "hello"
        assert info.is_file
        assert not info.is_dir
        assert info.exists
        assert info.size == 5

    def test_directory_fields(self, tmp_path: Path) -> None:
        d = tmp_path / "subdir"
        d.mkdir()
        info = PathInfo.from_path(d)
        assert info.is_dir
        assert not info.is_file
        assert info.size == 0

    def test_nonexistent_path(self, tmp_path: Path) -> None:
        missing = tmp_path / "no_such_file.txt"
        info = PathInfo.from_path(missing)
        assert not info.exists
        assert info.size == 0
        assert info.mode == 0

    def test_mime_type_for_txt(self, tmp_path: Path) -> None:
        f = tmp_path / "doc.txt"
        f.write_text("x")
        info = PathInfo.from_path(f)
        assert "text" in info.mime_type

    def test_mime_type_unknown(self, tmp_path: Path) -> None:
        f = tmp_path / "file.xyz123"
        f.write_text("x")
        info = PathInfo.from_path(f)
        assert info.mime_type == ""


class TestPathInfoPermissionsString:
    def test_returns_10_chars(self, tmp_path: Path) -> None:
        f = tmp_path / "a.txt"
        f.write_text("x")
        info = PathInfo.from_path(f)
        result = info.permissions_string()
        assert len(result) == 10

    def test_zero_mode_returns_ten_chars(self) -> None:
        import stat as _stat

        info = PathInfo(
            path=Path("/fake"),
            name="fake",
            suffix="",
            stem="fake",
            size=0,
            modified=0.0,
            created=0.0,
            accessed=0.0,
            mode=0,
            is_file=False,
            is_dir=False,
            is_symlink=False,
            mime_type="",
            exists=False,
        )
        result = info.permissions_string()
        assert len(result) == 10
        assert result == _stat.filemode(0)


class TestPathInfoSizeHuman:
    def test_directory_returns_empty(self, tmp_path: Path) -> None:
        info = PathInfo.from_path(tmp_path)
        assert info.size_human() == ""

    def test_small_file(self, tmp_path: Path) -> None:
        f = tmp_path / "small.bin"
        f.write_bytes(b"x" * 100)
        info = PathInfo.from_path(f)
        result = info.size_human()
        assert "B" in result

    def test_larger_file(self, tmp_path: Path) -> None:
        f = tmp_path / "bigger.bin"
        f.write_bytes(b"x" * 2048)
        info = PathInfo.from_path(f)
        result = info.size_human()
        assert "KB" in result


class TestPathInfoKindLabel:
    def test_directory(self, tmp_path: Path) -> None:
        info = PathInfo.from_path(tmp_path)
        assert info.kind_label() == "Folder"

    def test_file_with_mime(self, tmp_path: Path) -> None:
        f = tmp_path / "page.html"
        f.write_text("<html/>")
        info = PathInfo.from_path(f)
        assert "html" in info.kind_label().lower() or "text" in info.kind_label().lower()

    def test_file_no_suffix(self, tmp_path: Path) -> None:
        f = tmp_path / "Makefile"
        f.write_text("all:")
        info = PathInfo.from_path(f)
        assert info.kind_label() == "File"

    def test_file_unknown_suffix(self, tmp_path: Path) -> None:
        f = tmp_path / "data.xyz123abc"
        f.write_bytes(b"x")
        info = PathInfo.from_path(f)
        label = info.kind_label()
        assert "xyz123abc" in label or "file" in label.lower()


class TestListDirectory:
    def test_lists_files(self, tmp_path: Path) -> None:
        (tmp_path / "a.txt").write_text("a")
        (tmp_path / "b.txt").write_text("b")
        entries = list_directory(tmp_path)
        names = {e.name for e in entries}
        assert {"a.txt", "b.txt"}.issubset(names)

    def test_hidden_excluded_by_default(self, tmp_path: Path) -> None:
        (tmp_path / ".hidden").write_text("h")
        (tmp_path / "visible.txt").write_text("v")
        entries = list_directory(tmp_path, show_hidden=False)
        names = {e.name for e in entries}
        assert ".hidden" not in names
        assert "visible.txt" in names

    def test_hidden_included_when_requested(self, tmp_path: Path) -> None:
        (tmp_path / ".hidden").write_text("h")
        entries = list_directory(tmp_path, show_hidden=True)
        names = {e.name for e in entries}
        assert ".hidden" in names

    def test_empty_directory(self, tmp_path: Path) -> None:
        empty = tmp_path / "empty"
        empty.mkdir()
        assert list_directory(empty) == []

    def test_returns_path_infos(self, tmp_path: Path) -> None:
        (tmp_path / "x.py").write_text("x")
        entries = list_directory(tmp_path)
        assert all(isinstance(e, PathInfo) for e in entries)

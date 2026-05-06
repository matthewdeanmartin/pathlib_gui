"""Tests for pathlib_gui.services.filesystem."""

from __future__ import annotations

from pathlib import Path

import pytest

from pathlib_gui.services.filesystem import (
    copy_file,
    copy_tree,
    delete_file,
    delete_tree,
    disk_usage,
    make_directory,
    move_path,
    rename_path,
    send2trash_available,
    touch_file,
)


class TestCopyFile:
    def test_copies_file(self, tmp_path: Path) -> None:
        src = tmp_path / "src.txt"
        src.write_text("hello")
        dst = tmp_path / "dst.txt"
        op = copy_file(src, dst)
        assert dst.exists()
        assert dst.read_text() == "hello"
        assert op.completed is True
        assert op.kind == "copy"
        assert op.backend == "shutil.copy2"

    def test_op_sources_and_destination(self, tmp_path: Path) -> None:
        src = tmp_path / "a.txt"
        src.write_text("x")
        dst = tmp_path / "b.txt"
        op = copy_file(src, dst)
        assert op.sources == [src]
        assert op.destination == dst


class TestCopyTree:
    def test_copies_directory(self, tmp_path: Path) -> None:
        src = tmp_path / "src_dir"
        src.mkdir()
        (src / "child.txt").write_text("data")
        dst = tmp_path / "dst_dir"
        op = copy_tree(src, dst)
        assert (dst / "child.txt").exists()
        assert op.completed is True
        assert op.backend == "shutil.copytree"


class TestMovePath:
    def test_moves_file(self, tmp_path: Path) -> None:
        src = tmp_path / "move_me.txt"
        src.write_text("content")
        dst = tmp_path / "moved.txt"
        op = move_path(src, dst)
        assert dst.exists()
        assert not src.exists()
        assert op.completed is True
        assert op.kind == "move"
        assert op.backend == "shutil.move"


class TestRenamePath:
    def test_renames_file(self, tmp_path: Path) -> None:
        f = tmp_path / "old.txt"
        f.write_text("data")
        op = rename_path(f, "new.txt")
        assert (tmp_path / "new.txt").exists()
        assert not f.exists()
        assert op.completed is True
        assert op.kind == "rename"
        assert op.destination == tmp_path / "new.txt"


class TestDeleteFile:
    def test_deletes_file(self, tmp_path: Path) -> None:
        f = tmp_path / "delete_me.txt"
        f.write_text("bye")
        op = delete_file(f)
        assert not f.exists()
        assert op.completed is True
        assert op.kind == "delete"
        assert op.backend == "pathlib.Path.unlink"

    def test_raises_on_missing(self, tmp_path: Path) -> None:
        f = tmp_path / "ghost.txt"
        with pytest.raises(FileNotFoundError):
            delete_file(f)


class TestDeleteTree:
    def test_deletes_directory(self, tmp_path: Path) -> None:
        d = tmp_path / "rmme"
        d.mkdir()
        (d / "f.txt").write_text("x")
        op = delete_tree(d)
        assert not d.exists()
        assert op.completed is True
        assert op.backend == "shutil.rmtree"


class TestMakeDirectory:
    def test_creates_directory(self, tmp_path: Path) -> None:
        new_dir = tmp_path / "new_folder"
        op = make_directory(new_dir)
        assert new_dir.is_dir()
        assert op.completed is True
        assert op.kind == "mkdir"

    def test_raises_if_already_exists(self, tmp_path: Path) -> None:
        d = tmp_path / "existing"
        d.mkdir()
        with pytest.raises(FileExistsError):
            make_directory(d)


class TestTouchFile:
    def test_creates_empty_file(self, tmp_path: Path) -> None:
        f = tmp_path / "new.txt"
        op = touch_file(f)
        assert f.exists()
        assert f.stat().st_size == 0
        assert op.completed is True
        assert op.kind == "touch"
        assert op.backend == "pathlib.Path.touch"

    def test_updates_existing_file(self, tmp_path: Path) -> None:
        f = tmp_path / "existing.txt"
        f.write_text("hello")
        op = touch_file(f)
        assert f.exists()
        assert op.completed is True


class TestSend2trashAvailable:
    def test_returns_bool(self) -> None:
        result = send2trash_available()
        assert isinstance(result, bool)


class TestDiskUsage:
    def test_returns_usage_tuple(self, tmp_path: Path) -> None:
        usage = disk_usage(tmp_path)
        assert usage.total > 0
        assert usage.used >= 0
        assert usage.free >= 0

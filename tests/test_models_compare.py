"""Tests for pathlib_gui.models.compare."""

from __future__ import annotations

from pathlib import Path

from pathlib_gui.models.compare import DiffResult, DirCompareResult


class TestDiffResult:
    def test_default_same_false(self) -> None:
        r = DiffResult(
            left_path=Path("/a"),
            right_path=Path("/b"),
            left_lines=[],
            right_lines=[],
        )
        assert r.same is False

    def test_default_lists_empty(self) -> None:
        r = DiffResult(
            left_path=Path("/a"),
            right_path=Path("/b"),
            left_lines=["x\n"],
            right_lines=["y\n"],
        )
        assert r.unified == []
        assert r.context == []
        assert r.ndiff == []

    def test_stores_lines(self) -> None:
        left = ["a\n", "b\n"]
        right = ["a\n", "c\n"]
        r = DiffResult(
            left_path=Path("/a"),
            right_path=Path("/b"),
            left_lines=left,
            right_lines=right,
            same=False,
        )
        assert r.left_lines is left
        assert r.right_lines is right

    def test_same_flag(self) -> None:
        r = DiffResult(
            left_path=Path("/a"),
            right_path=Path("/b"),
            left_lines=["x\n"],
            right_lines=["x\n"],
            same=True,
        )
        assert r.same is True


class TestDirCompareResult:
    def test_default_lists_empty(self) -> None:
        r = DirCompareResult(left=Path("/a"), right=Path("/b"))
        assert r.only_left == []
        assert r.only_right == []
        assert r.same_files == []
        assert r.diff_files == []
        assert r.funny_files == []
        assert r.common_dirs == []

    def test_stores_paths(self) -> None:
        r = DirCompareResult(
            left=Path("/a"),
            right=Path("/b"),
            only_left=["x.txt"],
            only_right=["y.txt"],
            same_files=["z.txt"],
        )
        assert r.only_left == ["x.txt"]
        assert r.only_right == ["y.txt"]
        assert r.same_files == ["z.txt"]

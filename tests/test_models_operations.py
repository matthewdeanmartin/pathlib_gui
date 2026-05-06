"""Tests for pathlib_gui.models.operations."""

from __future__ import annotations

from pathlib import Path

from pathlib_gui.models.operations import FileOperation


class TestFileOperation:
    def test_defaults(self) -> None:
        op = FileOperation(kind="copy", sources=[Path("/src")])
        assert op.destination is None
        assert op.dry_run is True
        assert op.overwrite_policy == "ask"
        assert op.backend == ""
        assert op.description == ""
        assert op.errors == []
        assert op.completed is False

    def test_custom_fields(self) -> None:
        op = FileOperation(
            kind="move",
            sources=[Path("/a"), Path("/b")],
            destination=Path("/dst"),
            dry_run=False,
            overwrite_policy="overwrite",
            backend="shutil.move",
            description="Move files",
            completed=True,
        )
        assert op.kind == "move"
        assert len(op.sources) == 2
        assert op.destination == Path("/dst")
        assert op.dry_run is False
        assert op.overwrite_policy == "overwrite"
        assert op.backend == "shutil.move"
        assert op.completed is True

    def test_errors_list_is_independent(self) -> None:
        op1 = FileOperation(kind="delete", sources=[Path("/a")])
        op2 = FileOperation(kind="delete", sources=[Path("/b")])
        op1.errors.append("oops")
        assert op2.errors == []

    def test_all_operation_kinds(self) -> None:
        for kind in ("copy", "move", "delete", "trash", "rename", "mkdir", "touch"):
            op = FileOperation(kind=kind, sources=[Path("/x")])  # type: ignore[arg-type]
            assert op.kind == kind

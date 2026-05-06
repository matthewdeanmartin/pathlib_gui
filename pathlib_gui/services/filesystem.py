"""Filesystem operations service — thin wrappers around stdlib that record the backend used."""

from __future__ import annotations

import os
import queue
import shutil
import subprocess
import sys
import threading
from pathlib import Path

from pathlib_gui.models.operations import FileOperation


class CopyWorker:
    """Background thread for copying a list of (src, dst) pairs.

    Posts progress tuples ``(done: int, total: int, current: str)`` to *result_queue*.
    Posts ``DONE`` sentinel when finished, or ``("ERROR", msg)`` on failure.
    """

    DONE = object()

    def __init__(
        self,
        pairs: list[tuple[Path, Path]],
        result_queue: queue.Queue[object],
        move: bool = False,
    ) -> None:
        self.pairs = pairs
        self.result_queue = result_queue
        self.move = move
        self.cancel_event = threading.Event()
        self.thread = threading.Thread(target=self.run, daemon=True)

    def start(self) -> None:
        self.thread.start()

    def cancel(self) -> None:
        self.cancel_event.set()

    def run(self) -> None:
        total = len(self.pairs)
        for i, (src, dst) in enumerate(self.pairs):
            if self.cancel_event.is_set():
                break
            self.result_queue.put((i, total, src.name))
            try:
                if src.is_dir():
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)
                if self.move:
                    if src.is_dir():
                        shutil.rmtree(src)
                    else:
                        src.unlink()
            except OSError as e:
                self.result_queue.put(("ERROR", f"{src.name}: {e}"))
        self.result_queue.put(self.DONE)


def copy_file(src: Path, dst: Path) -> FileOperation:
    op = FileOperation(
        kind="copy",
        sources=[src],
        destination=dst,
        backend="shutil.copy2",
        description=f"Copy {src.name} → {dst}",
        dry_run=False,
    )
    shutil.copy2(src, dst)
    op.completed = True
    return op


def copy_tree(src: Path, dst: Path) -> FileOperation:
    op = FileOperation(
        kind="copy",
        sources=[src],
        destination=dst,
        backend="shutil.copytree",
        description=f"Copy directory {src.name} → {dst}",
        dry_run=False,
    )
    shutil.copytree(src, dst)
    op.completed = True
    return op


def move_path(src: Path, dst: Path) -> FileOperation:
    op = FileOperation(
        kind="move",
        sources=[src],
        destination=dst,
        backend="shutil.move",
        description=f"Move {src.name} → {dst}",
        dry_run=False,
    )
    shutil.move(str(src), str(dst))
    op.completed = True
    return op


def rename_path(src: Path, new_name: str) -> FileOperation:
    dst = src.parent / new_name
    op = FileOperation(
        kind="rename",
        sources=[src],
        destination=dst,
        backend="pathlib.Path.rename",
        description=f"Rename {src.name} → {new_name}",
        dry_run=False,
    )
    src.rename(dst)
    op.completed = True
    return op


def delete_file(path: Path) -> FileOperation:
    op = FileOperation(
        kind="delete",
        sources=[path],
        backend="pathlib.Path.unlink",
        description=f"Delete {path.name}",
        dry_run=False,
    )
    path.unlink()
    op.completed = True
    return op


def delete_tree(path: Path) -> FileOperation:
    op = FileOperation(
        kind="delete",
        sources=[path],
        backend="shutil.rmtree",
        description=f"Delete directory {path.name}",
        dry_run=False,
    )
    shutil.rmtree(path)
    op.completed = True
    return op


def trash_path(path: Path) -> FileOperation:
    try:
        import send2trash  # type: ignore[import-untyped]

        op = FileOperation(
            kind="trash",
            sources=[path],
            backend="send2trash.send2trash",
            description=f"Move to trash: {path.name}",
            dry_run=False,
        )
        send2trash.send2trash(str(path))
        op.completed = True
        return op
    except ImportError:
        raise RuntimeError("send2trash is not installed. Use permanent delete instead.")


def make_directory(path: Path) -> FileOperation:
    op = FileOperation(
        kind="mkdir",
        sources=[path],
        backend="pathlib.Path.mkdir",
        description=f"Create folder {path.name}",
        dry_run=False,
    )
    path.mkdir(parents=False, exist_ok=False)
    op.completed = True
    return op


def touch_file(path: Path) -> FileOperation:
    op = FileOperation(
        kind="touch",
        sources=[path],
        backend="pathlib.Path.touch",
        description=f"Touch {path.name}",
        dry_run=False,
    )
    path.touch()
    op.completed = True
    return op


def open_with_system(path: Path) -> None:
    if sys.platform == "win32":
        os.startfile(str(path))  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.run(["open", str(path)], check=False)
    else:
        subprocess.run(["xdg-open", str(path)], check=False)


def send2trash_available() -> bool:
    try:
        import send2trash  # type: ignore[import-untyped]  # noqa: F401

        return True
    except ImportError:
        return False


def disk_usage(path: Path) -> shutil._ntuple_diskusage:  # type: ignore[name-defined]
    return shutil.disk_usage(path)

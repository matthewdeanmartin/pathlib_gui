"""File operation history — in-memory log of completed operations."""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from pathlib import Path

from pathlib_gui.models.operations import FileOperation


@dataclass
class HistoryEntry:
    operation: FileOperation
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.now)

    @property
    def summary(self) -> str:
        ts = self.timestamp.strftime("%H:%M:%S")
        op = self.operation
        src = op.sources[0].name if op.sources else "?"
        dst = op.destination.name if op.destination else ""
        if dst:
            return f"[{ts}] {op.kind}: {src} → {dst}  [{op.backend}]"
        return f"[{ts}] {op.kind}: {src}  [{op.backend}]"

    @property
    def undoable(self) -> bool:
        return self.operation.kind in ("rename", "move") and not self.operation.errors

    def undo(self) -> str | None:
        """Attempt to undo a rename or move. Returns error string or None on success."""
        op = self.operation
        if op.kind == "rename" and op.destination and op.sources:
            try:
                op.destination.rename(op.sources[0])
                return None
            except OSError as e:
                return str(e)
        if op.kind == "move" and op.destination and op.sources:
            try:
                import shutil
                shutil.move(str(op.destination), str(op.sources[0]))
                return None
            except OSError as e:
                return str(e)
        return "Operation cannot be undone."


class OperationHistory:
    """In-memory log of completed file operations, newest first."""

    MAX_ENTRIES = 200

    def __init__(self) -> None:
        self.entries: list[HistoryEntry] = []

    def record(self, operation: FileOperation) -> None:
        self.entries.insert(0, HistoryEntry(operation=operation))
        if len(self.entries) > self.MAX_ENTRIES:
            self.entries = self.entries[: self.MAX_ENTRIES]

    def clear(self) -> None:
        self.entries.clear()


_history = OperationHistory()


def get_history() -> OperationHistory:
    return _history

"""File operation data model."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

OverwritePolicy = Literal["ask", "skip", "overwrite", "rename"]
OperationKind = Literal["copy", "move", "delete", "trash", "rename", "mkdir", "touch"]


@dataclass
class FileOperation:
    """Represents a planned filesystem operation before execution."""

    kind: OperationKind
    sources: list[Path]
    destination: Path | None = None
    dry_run: bool = True
    overwrite_policy: OverwritePolicy = "ask"
    backend: str = ""
    description: str = ""
    errors: list[str] = field(default_factory=list)
    completed: bool = False

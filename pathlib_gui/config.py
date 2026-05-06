"""User preferences — stored in ~/.pathlib_gui/config.json."""

from __future__ import annotations

import json
from pathlib import Path

_CONFIG_PATH = Path.home() / ".pathlib_gui" / "config.json"

_DEFAULTS: dict[str, object] = {
    "show_hidden": False,
    "confirm_deletes": True,
    "prefer_trash": True,
    "default_archive_format": "zip",
    "default_compare_mode": "text",
    "follow_symlinks_search": False,
    "hash_algorithm": "sha256",
    "theme": "default",
    "font_size": 10,
    "recent_paths": [],
}


class Preferences:
    def __init__(self) -> None:
        self._data: dict[str, object] = dict(_DEFAULTS)
        self.load()

    def load(self) -> None:
        if _CONFIG_PATH.exists():
            try:
                saved = json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
                if isinstance(saved, dict):
                    self._data.update(saved)
            except (OSError, json.JSONDecodeError):
                pass

    def save(self) -> None:
        _CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        _CONFIG_PATH.write_text(json.dumps(self._data, indent=2), encoding="utf-8")

    def get(self, key: str) -> object:
        return self._data.get(key, _DEFAULTS.get(key))

    def set(self, key: str, value: object) -> None:
        self._data[key] = value

    def add_recent(self, path: Path) -> None:
        recent = self._recent_path_strings()
        s = str(path)
        if s in recent:
            recent.remove(s)
        recent.insert(0, s)
        self._data["recent_paths"] = recent[:20]

    def recent_paths(self) -> list[Path]:
        return [Path(s) for s in self._recent_path_strings()]

    def _recent_path_strings(self) -> list[str]:
        recent_paths = self._data.get("recent_paths", [])
        if not isinstance(recent_paths, list):
            return []
        return [item for item in recent_paths if isinstance(item, str)]


_PREFS: Preferences | None = None


def get_prefs() -> Preferences:
    global _PREFS
    if _PREFS is None:
        _PREFS = Preferences()
    return _PREFS

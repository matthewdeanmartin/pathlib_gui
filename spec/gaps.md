# pathlib_gui — Gap Analysis & Work Phases

## Summary

The current codebase implements MVP 1 (file explorer) and most of MVP 2 (preview/metadata). The gaps below are split into four phases ordered by impact and dependency.

---

## Phase 1 — Quick correctness fixes (no new files)

These are bugs or missing wiring that require only small edits to existing files.

| # | Gap | File(s) | Spec ref |
|---|-----|---------|----------|
| 1.1 | Image inspector (`ImageInspector`) exists but is not dispatched by `inspector_for_path` — `.png`/`.gif` etc. fall through to binary | `inspectors/base.py` | §7.4 |
| 1.2 | Number-sequence batch rename is computed twice: once in the preview loop (correct) and once by re-calling `apply_rename_mode` in `execute` — the counter resets, producing wrong names | `dialogs/batch_rename.py` | §7.7 |
| 1.3 | `PathInfo` has no `owner`/`group` fields; `MetadataTab` omits them entirely | `models/paths.py`, `widgets/inspector.py` | §7.3 |
| 1.4 | CLI `inspect` subcommand navigates to the file's parent but never pre-selects the file or shows its inspector | `cli.py` | §17 |
| 1.5 | `services/__init__.py` is empty — spec §16 requires `compare_files`, `inspect_path`, `list_archive` importable from `pathlib_gui.services` | `services/__init__.py` | §16 |
| 1.6 | `PathBar` is a plain text entry only — no clickable breadcrumb buttons | `widgets/path_bar.py` | §7.1 |

---

## Phase 2 — Missing inspector / search criteria

Filling the inspector and search holes that are spec-required for MVP 2.

| # | Gap | File(s) | Spec ref |
|---|-----|---------|----------|
| 2.1 | No `plistlib` inspector (`.plist` files currently dispatched to `XmlInspector` which may fail on binary plists) | `inspectors/` (new `plist_inspector.py`) | §7.3 |
| 2.2 | No `configparser` inspector for `.ini`/`.cfg`/`.conf` files | `inspectors/` (new `ini_inspector.py`) | §7.3 |
| 2.3 | Search missing date-range, file-type, and MIME-type criteria | `widgets/search_view.py`, `models/search.py`, `services/search_service.py` | §7.8 |
| 2.4 | Symlinks shown in file table with no visual indicator of broken state; no "symlink target" column | `widgets/file_table.py`, `models/paths.py` | §7.11 |

---

## Phase 3 — Operation queue & batch operations

These require new UI components or threading changes.

| # | Gap | File(s) | Spec ref |
|---|-----|---------|----------|
| 3.1 | Copy/move execute synchronously on the main thread — UI freezes; `operation_queue.py` widget is never shown | `widgets/operation_queue.py`, `app.py`, `services/filesystem.py` | §9.1 |
| 3.2 | No batch copy, batch move, batch delete/trash in the menu | `app.py` | §7.7 |
| 3.3 | No batch chmod (permissions editor only works per-file) | `app.py`, `widgets/permissions_editor.py` | §7.7 |
| 3.4 | Recursive chmod has confirmation but no dry-run preview table | `widgets/permissions_editor.py` | §7.10 |
| 3.5 | Archive extraction has no path-traversal safety check beyond the stdlib defaults | `services/archive_service.py` | §7.6, §11.2 |

---

## Phase 4 — Preferences & future features

| # | Gap | File(s) | Spec ref |
|---|-----|---------|----------|
| 4.1 | No preferences file or dialog; all settings hardcoded | new `config.py`, new `dialogs/preferences.py` | §12 |
| 4.2 | No symlink creation UI | `app.py`, new `dialogs/symlink.py` | §7.11 |
| 4.3 | `email`/`mailbox` inspector | new `inspectors/mailbox_inspector.py` | §7.3, §14 |
| 4.4 | File operation history / undo for rename+move | new `models/history.py` | §19 |
| 4.5 | Stdlib Module Map should be a dedicated tab, not a popup | `app.py` | §14 |
| 4.6 | Drag-and-drop within app for copy/move intent | `widgets/file_table.py` | §7.1 |

---

## Phases 1 & 2 detailed work log

### Phase 1 completed items

- **1.1** `inspector_for_path` now checks image suffixes before falling to binary.
- **1.2** `BatchRenameDialog.execute` now iterates `self.preview_map` (already-computed names) rather than re-calling `apply_rename_mode`, fixing the counter reset.
- **1.3** `PathInfo` gains `owner` and `group` string fields (Unix: `pwd`/`grp`; Windows: empty string). `MetadataTab` displays them.
- **1.4** CLI `inspect` now navigates to the file's parent and, after the app starts, calls `inspector.show()` for the target file.
- **1.5** `services/__init__.py` exports `compare_files`, `inspect_path`, `list_archive`.
- **1.6** `PathBar` now renders clickable breadcrumb buttons above the text entry; clicking any segment navigates there.

### Phase 2 completed items

- **2.1** New `PlistInspector` — uses `plistlib.load`; falls back gracefully on binary plists. Registered in `inspector_for_path` for `.plist` suffix.
- **2.2** New `IniInspector` — uses `configparser`; shows sections/keys in a `Treeview`. Registered for `.ini`/`.cfg`/`.conf`.
- **2.3** Search form gains **Modified after/before** date fields, **File type** (any/file/directory/symlink) dropdown, and **MIME type contains** field. `SearchQuery` and `SearchWorker` updated to filter on these.
- **2.4** `PathInfo` gains `is_broken_symlink` property. `FileTable` tags broken symlinks red and appends `→ broken` to their kind label.

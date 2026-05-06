# pathlib_gui — Remaining Phases

## Phase 2: Preview and Metadata

Corresponds to spec section 7.4 (Preview pane) and 7.10 (Permissions/stat view).

### New package layout additions

```
pathlib_gui/
    inspectors/
        base.py           — Inspector registration protocol
        generic.py        — General PathInfo display (already in InspectorPane)
        text.py           — Text file preview (encoding detection, line numbers, search)
        binary.py         — Hex view with ASCII side pane
        csv_inspector.py  — CSV delimiter-sniff, table view
        json_inspector.py — JSON pretty-print, tree, validation
        toml_inspector.py — TOML parse (Python 3.11+ tomllib)
        xml_inspector.py  — XML tree view via xml.etree.ElementTree
        sqlite_inspector.py — Table list, schema, row preview, read-only SELECT
        wave_inspector.py — WAV metadata via wave.open (no playback)
        image_inspector.py — tkinter.PhotoImage preview for supported formats
    widgets/
        preview.py        — PreviewPane widget wiring inspectors by file type
        permissions_editor.py — Permissions display + checkbox editor
```

### Features

1. **Text preview** — `Path.read_text(errors="replace")`, encoding via `tokenize.detect_encoding`,
   line numbers, wrap toggle, search-within-file, show invisible chars.

2. **Binary/hex preview** — Offset column, hex bytes, ASCII side pane, file size, byte range.

3. **CSV preview** — `csv.Sniffer` for delimiter detection, header detection, `ttk.Treeview` table,
   row count estimate.

4. **JSON preview** — `json` parse, pretty-print, collapse/expand tree, validation errors displayed.

5. **TOML preview** — `tomllib` (Python 3.11+), read-only parse, tree display.

6. **XML preview** — `xml.etree.ElementTree`, tree widget, pretty-ish rendering, parse errors shown.

7. **SQLite preview** — `sqlite3`, read-only open, table list, schema display, `SELECT *` row preview,
   user-typed read-only query execution.

8. **WAV metadata** — `wave.open(path, "rb")`, show: channels, sample width, frame rate,
   frame count, duration. Labeled "WAV metadata" with "Backend: wave.open". No playback.

9. **Image preview** — `tkinter.PhotoImage` for GIF/PPM/PBM/PGM natively. Graceful fallback message
   for unsupported formats.

10. **Hash calculation** — Already in InspectorPane HashTab. Phase 2 adds background threading
    so large-file hashes don't freeze the UI (`threading`, `queue`).

11. **Permissions editor** — `stat` decode into symbolic notation, checkboxes for owner/group/other
    rwx bits, octal input, apply button (`Path.chmod`), recursive option with dry run.

### Backends

```python
pathlib           # read_text, read_bytes
csv               # Sniffer, reader
json              # loads, dumps
tomllib           # loads (Python 3.11+ only, version-gated)
xml.etree.ElementTree  # parse, tostring
sqlite3           # connect with uri=True, ?mode=ro
wave              # open
hashlib           # background digest
stat              # filemode, S_IMODE
tokenize          # detect_encoding
tkinter.PhotoImage
threading, queue
```

---

## Phase 3: Compare, Archive, Batch Operations

Corresponds to spec sections 7.5, 7.6, 7.7, 7.8, 7.9.

### New package layout additions

```
pathlib_gui/
    widgets/
        diff_view.py        — Side-by-side / unified / inline diff with navigation
        archive_view.py     — Archive member treeview + extract/preview actions
        operation_queue.py  — Progress bar list for long-running operations
    services/
        diff_service.py     — difflib wrappers returning structured diffs
        archive_service.py  — zipfile/tarfile open/list/extract/create with safety checks
        hash_service.py     — Threaded hash batching for duplicate finder
        search_service.py   — Threaded path search with queue-based result streaming
    dialogs/
        compare.py          — Pair-picker dialog for compare mode
        archive_create.py   — Archive format + source picker
        archive_extract.py  — Destination + safety summary before extract
        batch_rename.py     — Batch rename builder with live dry-run preview table
    models/
        archive.py          — ArchiveMember dataclass
        compare.py          — DiffResult, DirCompareResult dataclasses
        search.py           — SearchQuery, SearchResult dataclasses
```

### 3.1 Compare mode

- **File vs file text diff**: `difflib.unified_diff`, `difflib.context_diff`, `difflib.ndiff`,
  `difflib.HtmlDiff`. GUI: side-by-side pane with line number gutters, next/prev difference
  navigation, ignore-whitespace and ignore-case options.
- **Directory comparison**: `filecmp.dircmp` — show Only-left, Only-right, Same, Different,
  Funny categories. Double-click to drill in or open diff for file pairs.
- **Merge operations**: copy left→right or right→left at file level, delete orphan,
  export diff as `.unified.diff` / `.context.diff` / `.html` / `.txt`.
- CLI: `pathlib-gui compare left right` opens compare mode directly.

Backends: `difflib`, `filecmp`, `hashlib`, `shutil`

### 3.2 Archive mode

- **Open and browse**: `zipfile.ZipFile` / `tarfile.open` — member table with name, compressed size,
  uncompressed size, modified time, CRC, permissions.
- **Preview member**: extract to `tempfile` workspace, open in inspector.
- **Extract selected / all**: destination picker, path-traversal safety check (member path must
  stay inside extraction root — reject `../`, absolute paths, drive-letter roots on Windows).
- **Create archive**: format presets (ZIP normal, ZIP deflated, TAR, TAR.GZ, TAR.BZ2, TAR.XZ,
  GZIP single file, BZIP2 single file, XZ single file). Source picker dialog.
- **Test integrity**: `ZipFile.testzip()` for ZIP; read-verify loop for TAR.
- CLI: `pathlib-gui archive file.zip` / `pathlib-gui extract file.zip`.
- Archive safety: block or warn on `../`, `/` prefix, `C:\` prefix, symlinks escaping root.

Backends: `zipfile`, `tarfile`, `gzip`, `bz2`, `lzma`, `shutil`, `tempfile`, `fnmatch`

### 3.3 Batch operations

- **Batch rename** with modes: prefix, suffix, replace text, regex replace, change extension,
  number sequence, lowercase, uppercase, title case, conservative slugify.
  Every batch rename shows a dry-run preview table (original → new, conflict warnings) before
  executing. Backend: `pathlib.Path.rename`, `re`.
- **Batch hash**: compute selected algorithm for many files, output table + optionally save CSV.
- **Batch copy / move**: multi-select → destination picker, progress queue view.
- **Batch chmod**: multi-select, new mode input, recursive option, dry run. Backend: `Path.chmod`.
- **Batch touch**: update mtime for many files. Backend: `Path.touch`.

### 3.4 Search

- Threaded search (`threading`, `queue`) so UI stays responsive.
- Cancellable with a stop button.
- Criteria: name contains, glob pattern, regex, suffix, file type (via `mimetypes`), size range,
  modified/created date range, contents contains text, hash equals, duplicate files,
  empty files, empty folders, broken symlinks.
- Results in a `FileTable`-like view; selecting a result navigates the main browser.

### 3.5 Duplicate finder

- Staged algorithm: group by size → quick partial hash → full hash → optional byte-compare.
- Show duplicate groups. Actions: open folder, compare pair, trash selected, delete permanently,
  keep newest, keep oldest, keep shortest path.
- Destructive actions use same confirm dialogs as normal delete.

Backends: `pathlib`, `hashlib`, `filecmp`, `os`, `threading`, `queue`

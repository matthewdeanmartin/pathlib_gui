# `pathlib_gui` Specification

## 1. Summary

`pathlib_gui` is a desktop GUI application and reusable widget library that exposes Python’s filesystem-oriented standard library modules through a practical graphical interface.

It is not “just a file explorer.” It is a **stdlib filesystem workbench**: part Finder/File Explorer, part Beyond Compare, part WinRAR, part metadata inspector, and part safe frontend for Python’s file utilities.

The project uses `pathlib` as the primary abstraction for filesystem paths, with GUI affordances built on `tkinter`/`ttk`.

Optional extras may improve safety or platform integration, but the core package should remain usable with only the Python standard library.

Internet features are explicitly out of scope.

---

## 2. Goals

### Primary goals

`pathlib_gui` should provide:

1. A cross-platform Tkinter GUI for browsing local filesystems.
2. A visual frontend for `pathlib`, `os`, `shutil`, `stat`, `filecmp`, `difflib`, `zipfile`, `tarfile`, `gzip`, `bz2`, `lzma`, `wave`, `aifc` where available, `sndhdr` where available, `imghdr` where available, and related stdlib modules.
3. Safe, inspectable file operations: copy, move, rename, delete, archive, extract, compare, inspect.
4. A diff/merge-like experience inspired by Beyond Compare using `difflib`.
5. An archive browsing/extraction/creation experience inspired by WinRAR/7-Zip, using stdlib archive/compression modules.
6. A reusable set of Tkinter widgets that other programs can embed.
7. A clean plugin-style internal architecture, even if all built-in plugins are stdlib-backed.

### Non-goals

`pathlib_gui` will not provide:

1. FTP, SFTP, HTTP, cloud storage, WebDAV, or other internet-backed browsing.
2. Shell integration that requires non-stdlib dependencies.
3. A full terminal emulator.
4. Kernel-level filesystem monitoring.
5. Rich media playback or recording.
6. A full IDE.
7. A complete replacement for platform-native Finder/File Explorer.
8. Non-stdlib archive formats such as RAR or 7z in the core package.

---

## 3. Package identity

### Name

```text
pathlib_gui
```

The name intentionally centers `pathlib`, because the application treats `pathlib.Path` as the core object model. However, the broader mission is to surface many filesystem-themed standard library capabilities in a GUI.

### Tagline

> A Tkinter GUI for Python’s filesystem standard library.

### Possible command-line entry points

```bash
pathlib-gui
pylib-fs
pyfs-gui
```

Preferred:

```bash
pathlib-gui
```

---

## 4. Design principles

### 4.1 Stdlib-first

The default install should depend only on Python itself.

```text
pip install pathlib_gui
```

The core must work without third-party dependencies.

### 4.2 Optional extras are allowed

Optional dependencies may be provided for better UX:

```text
pip install pathlib_gui[trash]
pip install pathlib_gui[watch]
pip install pathlib_gui[theme]
pip install pathlib_gui[all]
```

Initial optional extra:

```text
send2trash
```

This enables safe trash/recycle-bin support.

Without `send2trash`, destructive delete must be clearly labeled as permanent.

### 4.3 No internet

The app must not include FTP, HTTP browsing, cloud sync, remote mounts, or package-manager integration.

Allowed:

```text
local filesystem
local archives
local mounted volumes as exposed by OS
```

Disallowed:

```text
ftp
sftp
http
webdav
s3
gdrive
dropbox
ssh
rsync over network
```

### 4.4 Expose capabilities, do not hide them

The GUI should teach users what stdlib module is powering an action.

Example:

```text
Copy file
Backend: shutil.copy2
```

```text
Compare text files
Backend: difflib.SequenceMatcher / difflib.HtmlDiff
```

```text
Read WAV metadata
Backend: wave.open
```

This makes the tool useful both as an app and as an educational map of the stdlib.

---

## 5. Target users

### Primary users

1. Python developers who want a GUI surface for stdlib file utilities.
2. Users who want a lightweight file explorer written in Python.
3. Educators teaching filesystem APIs.
4. Developers inspecting, comparing, archiving, or transforming local files.
5. Power users who want transparent, scriptable file operations.

### Secondary users

1. People writing small desktop utilities with Tkinter.
2. People who want reusable file browser widgets.
3. People learning `pathlib`, `shutil`, `difflib`, and archive modules.

---

## 6. High-level application layout

The main app should have a multi-pane interface:

```text
┌────────────────────────────────────────────────────────────┐
│ Menu bar                                                   │
├────────────────────────────────────────────────────────────┤
│ Toolbar: Back Forward Up Refresh Copy Move Delete Archive  │
├──────────────┬───────────────────────────┬─────────────────┤
│ Places       │ File list                 │ Inspector       │
│              │                           │                 │
│ Home         │ Name Size Type Modified   │ Metadata        │
│ Desktop      │                           │ Preview         │
│ Documents    │                           │ Actions         │
│ Volumes      │                           │ Stdlib backend  │
├──────────────┴───────────────────────────┴─────────────────┤
│ Status bar: selected path, operation status, warnings       │
└────────────────────────────────────────────────────────────┘
```

Additional modes:

```text
Compare mode
Archive mode
Batch operation mode
Metadata inspection mode
Preview mode
```

---

## 7. Major feature areas

## 7.1 File explorer

### Description

A Finder/File Explorer-like interface for local filesystem navigation.

### Backing stdlib modules

```python
pathlib
os
stat
shutil
mimetypes
datetime
pwd      # Unix, optional
grp      # Unix, optional
ctypes   # optional platform probing if needed
```

### Required features

1. Browse directories.
2. Navigate back/forward/up.
3. Open path by typing.
4. Show hidden files toggle.
5. Sort by:

   * name
   * extension
   * size
   * type
   * modified time
   * created time where available
   * permissions
6. Multi-select.
7. Context menu.
8. Keyboard shortcuts.
9. Drag within app for copy/move intent.
10. Refresh view.
11. Breadcrumb navigation.

### File list columns

Minimum:

```text
Name
Size
Type
Modified
Permissions
```

Optional advanced columns:

```text
Created
Accessed
Owner
Group
Suffix
MIME guess
Is symlink
Target
Inode
Device
```

### `pathlib` operations surfaced

For selected paths:

```python
Path.exists()
Path.is_file()
Path.is_dir()
Path.is_symlink()
Path.stat()
Path.lstat()
Path.iterdir()
Path.glob()
Path.rglob()
Path.resolve()
Path.absolute()
Path.relative_to()
Path.with_name()
Path.with_suffix()
Path.rename()
Path.replace()
Path.unlink()
Path.mkdir()
Path.rmdir()
Path.touch()
Path.read_text()
Path.read_bytes()
Path.write_text()
Path.write_bytes()
```

The GUI should not expose all of these as raw methods, but the inspector can show the equivalent operation.

Example inspector display:

```text
Selected: README.md

Path object:
Path('/Users/matt/project/README.md')

Common operations:
exists()      True
is_file()    True
suffix       .md
parent       /Users/matt/project
stat().size  12.4 KB
```

---

## 7.2 File operations

### Description

Safe GUI frontend for common file operations.

### Backing modules

```python
shutil
pathlib
os
send2trash  # optional extra
```

### Required operations

1. Copy file.
2. Copy directory.
3. Move file/directory.
4. Rename.
5. Duplicate.
6. Delete.
7. Trash, if optional dependency exists.
8. Create folder.
9. Create empty file.
10. Create text file.
11. Touch timestamp.
12. Change permissions where supported.
13. Show containing folder.
14. Open with system default application.

### Copy behavior

Default copy should preserve metadata where possible.

Preferred backend:

```python
shutil.copy2
```

Directory copy:

```python
shutil.copytree
```

Move:

```python
shutil.move
```

Delete file:

```python
Path.unlink
```

Delete directory:

```python
shutil.rmtree
```

Trash:

```python
send2trash.send2trash
```

### Delete safety

If `send2trash` is installed:

```text
Move to Trash
Permanent Delete...
```

If `send2trash` is not installed:

```text
Delete Permanently...
```

Permanent delete must require confirmation.

Confirmation dialog should show:

```text
You are about to permanently delete:

/path/to/file.txt

This cannot be undone by pathlib_gui.
```

For directories, show recursive summary:

```text
Directory: /path/to/folder
Contains: 128 files, 14 folders
Total size: 2.4 GB
```

---

## 7.3 Inspector pane

### Description

The inspector shows detailed information about the selected file, directory, symlink, archive member, or comparison item.

### Backing modules

```python
pathlib
os
stat
mimetypes
hashlib
wave
zipfile
tarfile
gzip
bz2
lzma
plistlib
configparser
json
csv
sqlite3
tomllib
xml.etree.ElementTree
email
mailbox
```

Not every module needs deep support initially, but the architecture should allow “inspectors” to register by file type.

### General metadata

For any filesystem path:

```text
Name
Full path
Parent
Suffix
Stem
Kind
Exists
Is file
Is directory
Is symlink
Resolved path
Size
Created
Modified
Accessed
Permissions
Owner
Group
Device
Inode
```

### Hashes

Use `hashlib`.

Available hash algorithms should include:

```text
MD5
SHA-1
SHA-256
SHA-512
BLAKE2b
BLAKE2s
```

MD5/SHA-1 should be labeled as legacy/non-cryptographic integrity checks.

### Type guessing

Use:

```python
mimetypes.guess_type()
```

Optional content sniffing using stdlib modules where still available in the user’s Python version.

---

## 7.4 Preview pane

### Description

Provide safe, read-only previews for common file types.

### Text preview

Use:

```python
Path.read_text(errors="replace")
```

Features:

```text
encoding guess
line numbers
wrap toggle
search within file
copy selected text
show invisible characters
```

Potential stdlib modules:

```python
tokenize.detect_encoding
codecs
unicodedata
```

### Binary preview

Show:

```text
hex view
ASCII side pane
offsets
file size
selected byte range
```

Use only stdlib.

### CSV preview

Use:

```python
csv
```

Features:

```text
delimiter sniffing
header detection
table view
row count estimate
```

### JSON preview

Use:

```python
json
```

Features:

```text
pretty print
collapse/expand tree
validation errors
```

### TOML preview

Use:

```python
tomllib
```

Read-only parse support for Python 3.11+.

### XML preview

Use:

```python
xml.etree.ElementTree
```

Features:

```text
tree view
pretty-ish rendering
parse error display
```

### SQLite preview

Use:

```python
sqlite3
```

Features:

```text
list tables
show schema
preview rows
run read-only SELECT queries
```

Must open SQLite files in read-only mode where practical.

### Audio metadata preview

Use:

```python
wave
```

For `.wav` files, show:

```text
Channels
Sample width
Frame rate
Frame count
Duration
Compression type
Compression name
```

Important: `wave` must be presented as metadata/frame inspection, not playback.

Example:

```text
WAV metadata
Backend: wave.open(..., "rb")

Channels: 2
Sample width: 16-bit
Sample rate: 44100 Hz
Frames: 2646000
Duration: 60.0 seconds
```

### Image metadata preview

Potential stdlib support is limited.

Use:

```python
tkinter.PhotoImage
```

For displayable image formats supported by the local Tk build.

Possible metadata helpers:

```python
imghdr  # removed in newer Python versions
```

Since `imghdr` has been removed in Python 3.13, support must be version-gated.

---

## 7.5 Compare mode

### Description

A Beyond Compare-inspired diff interface for files and directories.

### Backing modules

```python
difflib
filecmp
pathlib
hashlib
stat
shutil
```

### Compare targets

Supported comparisons:

```text
file vs file
directory vs directory
archive vs archive
archive member vs archive member
text selection vs text selection
clipboard-like internal buffers, if implemented
```

### File comparison modes

1. Text diff.
2. Binary same/different.
3. Hash comparison.
4. Metadata comparison.
5. Size/time comparison.

### Text diff

Use:

```python
difflib.SequenceMatcher
difflib.unified_diff
difflib.context_diff
difflib.ndiff
difflib.HtmlDiff
```

GUI should provide:

```text
side-by-side diff
inline diff
unified diff
context diff
next difference
previous difference
ignore whitespace
ignore blank lines
case-insensitive comparison
line number gutters
copy left to right
copy right to left
save merged output
```

### Directory comparison

Use:

```python
filecmp.dircmp
filecmp.cmp
```

Show categories:

```text
Only in left
Only in right
Same files
Different files
Funny files / errors
Common directories
Common files
```

Enhanced comparison should optionally use hashes for files that appear equal by shallow comparison.

Options:

```text
Shallow compare
Deep byte compare
Hash compare
Metadata compare
```

### Merge features

Initial version should support simple file-level merge operations:

```text
Copy selected left item to right
Copy selected right item to left
Delete selected orphan
Open both containing folders
Export diff
```

Text-level merge may be added later.

### Diff export

Supported export formats:

```text
.unified.diff
.context.diff
.html
.txt
```

Backends:

```python
difflib.unified_diff
difflib.context_diff
difflib.HtmlDiff
```

---

## 7.6 Archive mode

### Description

A WinRAR/7-Zip-inspired GUI for archive inspection, creation, extraction, and modification where the stdlib supports it.

### Backing modules

```python
zipfile
tarfile
gzip
bz2
lzma
shutil
pathlib
tempfile
fnmatch
```

### Supported formats

Core archive formats:

```text
.zip
.tar
.tar.gz
.tgz
.tar.bz2
.tbz2
.tar.xz
.txz
```

Compression stream formats:

```text
.gz
.bz2
.xz
```

Important distinction:

```text
.zip and .tar are archives containing multiple named members.
.gz, .bz2, and .xz are compression streams, usually wrapping one payload.
```

### Archive browsing

For archive files, show:

```text
member name
compressed size
uncompressed size
modified time
mode/permissions where available
CRC where available
type: file/directory/symlink
```

### Archive operations

Required:

```text
Open archive
List contents
Preview member
Extract selected
Extract all
Create archive from files/folders
Test archive integrity where supported
Show archive metadata
```

ZIP-specific:

```python
zipfile.ZipFile
ZipFile.namelist()
ZipFile.infolist()
ZipFile.extract()
ZipFile.extractall()
ZipFile.write()
ZipFile.writestr()
ZipFile.testzip()
```

TAR-specific:

```python
tarfile.open
TarFile.getmembers()
TarFile.extract()
TarFile.extractall()
TarFile.add()
```

Compression stream-specific:

```python
gzip.open
bz2.open
lzma.open
```

### Archive safety

Extraction must protect against path traversal.

Before extracting any archive member, normalize and verify destination:

```text
destination/member_path must remain inside extraction directory
```

Suspicious members should be blocked or require explicit confirmation:

```text
../evil.txt
/path/to/absolute
C:\absolute\path
symlink escaping destination
```

### Archive creation profiles

Provide presets:

```text
ZIP: normal
ZIP: deflated
TAR: uncompressed
TAR.GZ
TAR.BZ2
TAR.XZ
GZIP single file
BZIP2 single file
XZ single file
```

### Archive comments

For ZIP files, support reading/writing archive comment if available through `zipfile`.

---

## 7.7 Batch operations

### Description

A GUI for applying stdlib filesystem operations to many files.

### Backing modules

```python
pathlib
shutil
fnmatch
glob
re
os
```

### Features

```text
batch rename
batch copy
batch move
batch delete/trash
batch chmod
batch touch
batch suffix change
batch archive
batch hash
batch compare
```

### Batch rename

Modes:

```text
prefix
suffix
replace text
regex replace
change extension
number sequence
lowercase
uppercase
title case
slugify-like conservative rename
```

Since slugification is not a stdlib feature, the built-in slugify should be minimal and transparent.

Example:

```text
"Hello, World!.txt" → "hello_world.txt"
```

### Dry run

Every batch operation must have a dry-run preview.

Show:

```text
original path
new path
operation
status
conflict warning
```

No batch operation should execute without a preview unless explicitly configured.

---

## 7.8 Search and filter

### Description

Local filesystem search using stdlib traversal.

### Backing modules

```python
pathlib
fnmatch
glob
re
os
stat
mimetypes
```

### Search criteria

```text
name contains
glob pattern
regex pattern
suffix
file type
size range
modified date range
created date range where available
contents contains text
hash equals
duplicate files
empty files
empty folders
broken symlinks
```

### Search behavior

Search must be cancellable.

The UI should not freeze during long searches. Use:

```python
threading
queue
```

Tkinter updates must be marshaled back to the main thread.

---

## 7.9 Duplicate finder

### Description

Find duplicate files using staged comparison.

### Backing modules

```python
pathlib
hashlib
filecmp
os
```

### Algorithm

Recommended staged approach:

```text
group by size
then group by quick partial hash
then group by full hash
then optionally byte-compare
```

### UI

Show duplicate groups:

```text
Group 1: 4 files, 12.4 MB each
Group 2: 2 files, 900 KB each
```

Actions:

```text
open containing folder
compare selected
trash selected
delete selected permanently
keep newest
keep oldest
keep shortest path
```

Destructive actions must use the same safety rules as normal delete.

---

## 7.10 Permissions and stat view

### Description

Expose `stat` and path metadata in a readable GUI.

### Backing modules

```python
stat
os
pathlib
pwd  # Unix
grp  # Unix
```

### Display

```text
Mode: 0o100644
Symbolic: -rw-r--r--
Owner read/write/execute
Group read/write/execute
Other read/write/execute
File type bits
Setuid/setgid/sticky where relevant
```

### Editing

Permission editing should be available where supported.

Controls:

```text
checkboxes for read/write/execute
octal input
apply recursively option
dry run for recursive chmod
```

Backend:

```python
Path.chmod()
os.chmod()
```

---

## 7.11 Symlink and shortcut support

### Description

Surface links clearly and safely.

### Backing modules

```python
pathlib
os
stat
```

### Required features

```text
detect symlink
show link target
show resolved path
show broken symlink warning
create symlink where supported
copy symlink as link or target
delete symlink without deleting target
```

Windows support must account for permission/platform limitations.

---

## 7.12 Temporary workspace

### Description

A scratch area for safe extraction, previews, comparisons, and transformations.

### Backing modules

```python
tempfile
pathlib
shutil
atexit
```

### Uses

```text
extract archive member for preview
generate HTML diff
stage merge output
preview decompressed stream
```

Temporary files should be cleaned up automatically unless user saves them.

---

## 8. GUI architecture

## 8.1 Toolkit

Core GUI must use:

```python
tkinter
tkinter.ttk
tkinter.filedialog
tkinter.messagebox
tkinter.simpledialog
```

No third-party GUI framework in core.

## 8.2 Application components

Suggested internal package layout:

```text
pathlib_gui/
    __init__.py
    __main__.py

    app.py
    config.py
    errors.py
    events.py

    models/
        paths.py
        operations.py
        archive.py
        compare.py
        metadata.py
        search.py

    services/
        filesystem.py
        trash.py
        archive_service.py
        diff_service.py
        hash_service.py
        preview_service.py
        search_service.py

    widgets/
        path_bar.py
        places_sidebar.py
        file_table.py
        inspector.py
        preview.py
        diff_view.py
        archive_view.py
        operation_queue.py
        status_bar.py

    inspectors/
        base.py
        generic.py
        text.py
        binary.py
        csv_inspector.py
        json_inspector.py
        toml_inspector.py
        xml_inspector.py
        sqlite_inspector.py
        wave_inspector.py
        archive_inspector.py

    dialogs/
        copy_move.py
        delete.py
        rename.py
        batch_rename.py
        archive_create.py
        archive_extract.py
        compare.py
        preferences.py

    backends/
        stdlib_pathlib.py
        stdlib_shutil.py
        stdlib_diff.py
        stdlib_archive.py
        stdlib_metadata.py

    tests/
```

## 8.3 Reusable widgets

The package should expose widgets that can be embedded in other Tk apps.

Example:

```python
from pathlib_gui.widgets import FileBrowser, PathInspector, DiffView, ArchiveView
```

Candidate public widgets:

```python
FileBrowser
PathTable
PathTree
PathInspector
PreviewPane
DiffView
DirectoryCompareView
ArchiveView
OperationQueueView
```

### Example embedding API

```python
import tkinter as tk
from pathlib_gui.widgets import FileBrowser

root = tk.Tk()

browser = FileBrowser(
    root,
    initial_path=".",
    show_hidden=False,
    allow_delete=False,
)

browser.pack(fill="both", expand=True)

root.mainloop()
```

---

## 9. Operation model

Filesystem operations should be represented as explicit operation objects before execution.

Example:

```python
@dataclass
class FileOperation:
    kind: Literal["copy", "move", "delete", "trash", "rename", "archive", "extract"]
    sources: list[Path]
    destination: Path | None
    dry_run: bool = True
    overwrite_policy: OverwritePolicy = "ask"
```

Benefits:

```text
preview before execution
operation queue
undo metadata where possible
logging
testing
clear error reporting
```

## 9.1 Operation queue

Long operations should appear in an operation queue.

Features:

```text
progress bar
current file
bytes copied where knowable
cancel request
pause where practical
error details
retry failed item
skip failed item
```

Backend:

```python
threading
queue
shutil.copyfileobj for custom progress where needed
```

`shutil.copy2` is simple but does not expose progress. For large copy operations, the app may implement its own copy loop while preserving metadata afterward.

---

## 10. Error handling

Errors must be human-readable and developer-useful.

Each error dialog should show:

```text
summary
path involved
operation
stdlib backend
exception type
exception message
details expander
```

Example:

```text
Could not copy file

Source:
/Users/matt/a.txt

Destination:
/Volumes/Drive/a.txt

Backend:
shutil.copy2

Error:
PermissionError: [Errno 13] Permission denied
```

---

## 11. Safety requirements

### 11.1 Destructive operations

Permanent destructive operations require confirmation.

Destructive operations include:

```text
unlink
rmtree
overwrite
recursive chmod
archive extraction overwrite
batch rename
```

### 11.2 Archive extraction

Must defend against path traversal.

### 11.3 Symlinks

Must avoid accidentally deleting symlink targets.

### 11.4 Read-only preview

Preview pane must not modify files.

### 11.5 Dry-run-first batch operations

Batch operations must show proposed changes before execution.

---

## 12. Preferences

Preferences should be stored locally using stdlib.

Possible backends:

```python
configparser
json
tomllib for reading default TOML templates, if desired
```

Suggested preference file:

```text
~/.pathlib_gui/config.json
```

Preferences:

```text
show hidden files
confirm deletes
prefer trash if available
default archive format
default compare mode
follow symlinks during search
hash algorithm
theme preference
font size
recent paths
places/sidebar entries
```

---

## 13. Platform behavior

## 13.1 Windows

Open file:

```python
os.startfile(path)
```

Special concerns:

```text
drive letters
UNC paths
reserved filenames
case-insensitive paths
symlink permissions
Recycle Bin only via optional send2trash
```

## 13.2 macOS

Open file:

```python
subprocess.run(["open", path])
```

Special concerns:

```text
app bundles
resource forks not deeply handled
case-insensitive default filesystems
Trash only via optional send2trash
```

## 13.3 Linux/BSD

Open file:

```python
subprocess.run(["xdg-open", path])
```

Special concerns:

```text
desktop environment variability
permissions
mount points
Trash only via optional send2trash
```

---

## 14. Stdlib module coverage map

The app should include a “Stdlib Map” or “Capabilities” screen showing what modules are being surfaced.

### Filesystem and paths

```text
pathlib
os
os.path
stat
filecmp
fnmatch
glob
shutil
tempfile
```

### Comparison

```text
difflib
filecmp
hashlib
```

### Archives and compression

```text
zipfile
tarfile
gzip
bz2
lzma
zlib
```

### Metadata and content inspection

```text
mimetypes
wave
csv
json
tomllib
configparser
plistlib
sqlite3
xml.etree.ElementTree
email
mailbox
tokenize
codecs
unicodedata
```

### GUI

```text
tkinter
tkinter.ttk
tkinter.filedialog
tkinter.messagebox
tkinter.simpledialog
```

### Concurrency and app plumbing

```text
threading
queue
logging
argparse
dataclasses
typing
enum
time
datetime
```

---

## 15. Specific “filesystem-themed library” surfaces

### `shutil` panel

Expose:

```python
shutil.copy
shutil.copy2
shutil.copytree
shutil.move
shutil.rmtree
shutil.disk_usage
shutil.make_archive
shutil.unpack_archive
shutil.which
```

GUI features:

```text
copy/move/delete
disk usage display
archive creation
archive extraction
find executable in PATH
```

### `os` panel

Expose safe, relevant pieces:

```python
os.getcwd
os.chdir
os.scandir
os.stat
os.lstat
os.walk
os.access
os.environ
os.pathconf where available
```

Avoid presenting dangerous low-level APIs casually.

### `pathlib` panel

Show common `Path` expressions for selected files.

Example:

```text
Path selected:
Path('/Users/matt/project/app.py')

.parent     /Users/matt/project
.name       app.py
.stem       app
.suffix     .py
.exists()   True
.is_file()  True
```

### `mimetypes` panel

Show:

```text
MIME type guess
encoding guess
known extensions for MIME
```

### `wave` panel

For WAV files, show audio container information only.

No playback.

### `zipfile` / `tarfile` panel

Show archive member table and actions.

### `difflib` panel

Show text comparison controls and export options.

---

## 16. Public Python API

The app should be usable both as an application and a library.

### Launch app

```python
from pathlib_gui import launch

launch()
```

### Open at path

```python
from pathlib_gui import launch

launch(path="~/Downloads")
```

### Widget API

```python
from pathlib_gui.widgets import FileBrowser

browser = FileBrowser(parent, initial_path=".")
```

### Services API

```python
from pathlib_gui.services import compare_files, inspect_path, list_archive
```

Example:

```python
from pathlib import Path
from pathlib_gui.services import inspect_path

info = inspect_path(Path("sound.wav"))
print(info)
```

---

## 17. CLI

The package should expose a CLI.

### Basic

```bash
pathlib-gui
pathlib-gui .
pathlib-gui ~/Downloads
```

### Compare

```bash
pathlib-gui compare left.txt right.txt
pathlib-gui compare left_dir right_dir
```

### Archive

```bash
pathlib-gui archive file.zip
pathlib-gui extract file.zip
```

### Inspect

```bash
pathlib-gui inspect sound.wav
```

The CLI opens the corresponding GUI mode.

---

## 18. Minimum viable product

### MVP 1: File explorer

Required:

```text
directory browsing
file table
path bar
sidebar
inspector pane
copy
move
rename
delete
create folder
open file with system app
show stdlib backend for operation
```

### MVP 2: Preview and metadata

Required:

```text
text preview
binary hex preview
CSV preview
JSON preview
WAV metadata
hash calculation
permissions display
```

### MVP 3: Compare

Required:

```text
file vs file text diff
directory vs directory comparison
unified diff export
copy left/right for files
```

### MVP 4: Archive

Required:

```text
open ZIP/TAR archives
list members
extract selected/all
create ZIP/TAR/TAR.GZ
gzip/bz2/lzma single-file compression/decompression
archive safety checks
```

### MVP 5: Batch operations

Required:

```text
batch rename with dry run
batch hash
batch copy/move
batch archive
```

---

## 19. Future features

Potential future features that remain stdlib-compatible:

```text
file operation history
undo for rename/move where safe
saved workspaces
side-by-side folder sync
checksums manifest generation
directory size treemap approximation using Tk canvas
regex search in files
sqlite table browser
mailbox viewer
plist viewer
configparser INI viewer
Python package/source inspector
```

Potential optional extras:

```text
send2trash for trash/recycle bin
watchdog for live filesystem updates
Pillow for richer image previews
platformdirs for config paths
darkdetect for theme hints
```

Core must not require these.

---

## 20. Naming and positioning

`pathlib_gui` is a good name because it is precise enough for Python users and broad enough to house the larger concept.

Suggested README framing:

```text
pathlib_gui is a Tkinter desktop GUI for Python’s filesystem-oriented standard library.

It gives pathlib, shutil, difflib, filecmp, zipfile, tarfile, gzip, bz2, lzma, wave, mimetypes, hashlib, stat, and related modules a graphical interface.

Think Finder/File Explorer plus Beyond Compare plus WinRAR, implemented stdlib-first.
```

---

## 21. Example README snippet

````markdown
# pathlib_gui

A Tkinter GUI for Python’s filesystem standard library.

`pathlib_gui` is a local filesystem workbench built around `pathlib.Path`.
It exposes common stdlib file utilities through a desktop interface:

- Browse files and folders
- Copy, move, rename, delete, and inspect paths
- Compare files and directories with `difflib` and `filecmp`
- Browse and create ZIP/TAR/GZ/BZ2/XZ archives
- Preview text, binary, CSV, JSON, XML, SQLite, and WAV metadata
- Calculate hashes
- Batch rename files with a dry-run preview

The core package uses only the Python standard library.

Optional extras:

```bash
pip install pathlib_gui[trash]
````

enables safe Trash/Recycle Bin support via `send2trash`.

Internet-backed filesystems are out of scope. No FTP, SFTP, HTTP, WebDAV, or cloud browsing.

````

---

## 22. Core philosophy

The stdlib has many powerful file-related modules that are usually only accessible from scripts.

`pathlib_gui` gives them a front door.

Not:

```text
A clone of Finder.
````

Not:

```text
A replacement for WinRAR or Beyond Compare.
```

But:

```text
A local, inspectable, Python-native GUI for the filesystem tools Python already ships with.
```

The guiding question for every feature should be:

> Is there a useful filesystem-related stdlib capability that currently has no obvious GUI?

If yes, `pathlib_gui` is where it belongs.

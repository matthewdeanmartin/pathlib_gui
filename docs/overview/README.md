# Overview

`pathlib_gui` is a local-filesystem desktop application built with Tkinter and centered on Python's standard-library filesystem APIs. The project aims to make `pathlib`, `shutil`, `os`, `stat`, `hashlib`, `difflib`, `zipfile`, `tarfile`, and related modules easier to explore through a GUI instead of a shell prompt.

## Main surfaces

### Browse

The main browser provides:

- Back, forward, up, and refresh navigation
- A path bar for direct navigation
- A places sidebar with common folders and platform-specific roots
- A file table for selection and opening
- A right-hand inspector pane

## Inspector

Selecting a path updates a multi-tab inspector with:

- Metadata such as size, timestamps, MIME type, owner, group, and permission bits
- A `pathlib.Path` view showing common derived properties
- On-demand file hashes
- A type-aware preview pane
- A permissions editor with octal input and recursive chmod preview for directories

## Compare

The compare tab supports both file-to-file and directory-to-directory workflows:

- File comparison includes side-by-side, unified, context, and ndiff views
- Diff display supports ignore-whitespace and ignore-case toggles
- Directory comparison is available for two selected folders

## Archive tools

Archive support includes:

- Opening ZIP and TAR-family archives
- Viewing members, sizes, timestamps, CRC, and compression ratios
- Previewing archive members
- Extracting selected members or entire archives
- Integrity testing
- Creating new ZIP, TAR, `tar.gz`, `tar.bz2`, `tar.xz`, `gz`, `bz2`, and `xz` archives

Archive extraction uses safety checks to keep extracted paths inside the chosen destination.

## Search and cleanup

The search tab supports threaded, cancellable searches over a chosen root with filters for:

- Name contains
- Glob pattern
- Regex pattern
- Extension
- File contents
- File size
- Modification dates
- MIME type
- File type
- Empty files
- Empty folders
- Broken symlinks

The duplicate finder scans a folder tree, groups identical files using staged hashing, and offers cleanup actions.

## File operations

The app supports:

- Create file, folder, and symlink
- Rename, copy, move, and open with the system default app
- Batch copy, move, delete, trash, hash, touch, and chmod
- Optional trash integration via `send2trash`
- An operation history window with undo for recorded rename and move operations

## Scope

`pathlib_gui` targets local filesystems and local archive files. Internet-backed filesystems are explicitly out of scope in the current CLI and docs.

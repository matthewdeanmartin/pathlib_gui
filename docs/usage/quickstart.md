# Quick Start

## Launch the app

```bash
pathlib_gui
```

Open a specific folder:

```bash
pathlib_gui C:\path\to\folder
```

The package also installs `pathlib-gui` and `plg`, and supports:

```bash
python -m pathlib_gui
```

## Use the CLI entry points

Show the available commands:

```bash
pathlib_gui --help
```

Open browse mode explicitly:

```bash
pathlib_gui browse C:\path\to\folder
```

Open the compare tab with two files or two directories:

```bash
pathlib_gui compare C:\left\path C:\right\path
```

Open an archive directly in the archive tab:

```bash
pathlib_gui archive C:\path\to\archive.zip
```

Open a file and preselect it for inspection:

```bash
pathlib_gui inspect C:\path\to\file.json
```

## Main in-app workflows

1. **Browse** to a folder with the toolbar, path bar, or places sidebar.
1. **Select** a file to inspect metadata, hashes, preview content, or edit permissions.
1. **Use Tools** to compare files, open or create archives, search, find duplicates, hash files, or review operation history.
1. **Use Edit** for copy, move, rename, batch rename, delete, trash, and related batch actions.

## Current shortcuts

- `Ctrl+N`: new file
- `Ctrl+Shift+N`: new folder
- `Ctrl+O`: open with system app
- `Ctrl+F`: switch to search
- `Ctrl+H`: toggle hidden files
- `F2`: rename
- `F5`: refresh
- `Delete`: trash if available, otherwise permanent delete
- `Shift+Delete`: permanent delete from the menu
- `Backspace`: go up to the parent folder

The app is intended for local filesystem work; internet-backed filesystems are not currently supported.

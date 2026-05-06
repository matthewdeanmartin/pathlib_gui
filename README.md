# Pathlib Gui

`pathlib_gui` is a Tkinter desktop app for exploring and manipulating local files with Python's standard library. It combines a file browser, metadata inspector, preview pane, diff tools, archive browser, search tools, duplicate finder, permissions editor, and operation history into one local filesystem workbench.

## What it does

- Browse folders with back/forward history, an address bar, common places, and optional hidden-file display.
- Create files, folders, and symlinks; rename, copy, move, trash, or permanently delete selections.
- Inspect filesystem metadata, `pathlib.Path` properties, hashes, previews, and POSIX-style permissions.
- Compare files or directories with side-by-side, unified, context, and ndiff views.
- Open, test, preview, extract, and create ZIP and TAR-family archives, plus single-file `gz`, `bz2`, and `xz`.
- Search by name, glob, regex, content, size, date, MIME type, file type, empty files/folders, and broken symlinks.
- Find duplicate files with staged hashing and clean them up with keep/delete/trash actions.
- Review recent operations and undo recorded rename and move actions.

## Installation

### Install from PyPI

```bash
pipx install pathlib_gui
```

Or:

```bash
pip install pathlib_gui
```

### Optional extras

- `pip install "pathlib_gui[trash]"` enables recycle bin / trash support via `send2trash`.
- `pip install "pathlib_gui[xml]"` enables the XML tree inspector via `defusedxml`.

### Run from source

```bash
git clone https://github.com/matthewdeanmartin/pathlib_gui.git
cd pathlib_gui
uv sync --all-extras
uv run pathlib_gui
```

## Usage

The package installs three equivalent launchers: `pathlib_gui`, `pathlib-gui`, and `plg`.

```bash
pathlib_gui
pathlib_gui C:\path\to\folder
pathlib_gui browse C:\path\to\folder
pathlib_gui compare C:\left\file.txt C:\right\file.txt
pathlib_gui archive C:\path\to\archive.zip
pathlib_gui inspect C:\path\to\file.json
python -m pathlib_gui
```

For a full command summary:

```bash
pathlib_gui --help
```

The app is focused on local filesystems; internet-backed filesystems are out of scope.

## Preview and inspector coverage

The preview pane chooses an inspector based on file type. Current built-in coverage includes:

- Text and source files
- JSON, TOML, CSV, INI-style config files, plist files
- SQLite databases
- WAV metadata
- Images supported by the image inspector
- Mailbox and email files
- XML, XHTML, and SVG when the `xml` extra is installed
- Binary fallback for everything else

Preferences are stored in `~/.pathlib_gui/config.json`.

## Documentation


- Project overview: [docs/overview/README.md](https://github.com/matthewdeanmartin/pathlib_gui/blob/main/docs/overview/README.md)
- Installation: [docs/installation.md](https://github.com/matthewdeanmartin/pathlib_gui/blob/main/docs/installation.md)
- Quick start: [docs/usage/quickstart.md](https://github.com/matthewdeanmartin/pathlib_gui/blob/main/docs/usage/quickstart.md)
- Contributing: [docs/extending/CONTRIBUTING.md](https://github.com/matthewdeanmartin/pathlib_gui/blob/main/docs/extending/CONTRIBUTING.md)

## License

MIT — see [LICENSE](https://github.com/matthewdeanmartin/pathlib_gui/blob/main/LICENSE).

## Changelog

See [CHANGELOG.md](https://github.com/matthewdeanmartin/pathlib_gui/blob/main/CHANGELOG.md).

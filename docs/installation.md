# Installation

## Requirements

- Python 3.10 or newer
- Tkinter available in your Python installation

## Install from PyPI

### Recommended: pipx

```bash
pipx install pathlib_gui
```

### pip

```bash
pip install pathlib_gui
```

## Optional extras

### Trash support

```bash
pip install "pathlib_gui[trash]"
```

This enables recycle bin / trash actions through `send2trash`.

### XML inspector

```bash
pip install "pathlib_gui[xml]"
```

This enables the XML, XHTML, and SVG inspector based on `defusedxml`.

## From source

```bash
git clone https://github.com/matthewdeanmartin/pathlib_gui.git
cd pathlib_gui
uv sync --all-extras
```

Launch the app with:

```bash
uv run pathlib_gui
```

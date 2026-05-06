# Contributing

## Setup

```bash
git clone https://github.com/matthewdeanmartin/pathlib_gui.git
cd pathlib_gui
uv sync --all-extras
```

## Run the quality checks

```bash
uv run make lint
uv run make typecheck
uv run make test
uv run make security
```

Or run the combined gate:

```bash
uv run make check
```

## Helpful targets

```bash
uv run make help
uv run make dead-code
```

## Before opening a pull request

Make sure the relevant checks pass for your change and update the documentation when behavior changes.

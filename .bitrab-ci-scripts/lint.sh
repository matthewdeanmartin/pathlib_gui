#!/usr/bin/env bash
set -euo pipefail
source ./.bitrab-ci-scripts/setup.sh
uv run isort --check-only pathlib_gui tests
uv run black --check pathlib_gui tests
uv run ruff check --quiet pathlib_gui tests
uv run pylint --score=n --reports=n --rcfile=.pylintrc pathlib_gui
uv run pylint --score=n --reports=n --rcfile=.pylintrc_tests tests

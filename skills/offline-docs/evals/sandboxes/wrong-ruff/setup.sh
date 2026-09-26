#!/bin/sh
# Puts an older ruff (0.6.9) first on PATH, the way a global install
# shadows the project's ruff. Run once, then start the model in a shell
# where PATH begins with the folder this prints.
set -e
dir="${OLD_RUFF_DIR:-$HOME/.cache/offline-docs-old-ruff}"
uv venv -q "$dir"
uv pip install -q --python "$dir/bin/python" ruff==0.6.9
echo "export PATH=\"$dir/bin:\$PATH\""

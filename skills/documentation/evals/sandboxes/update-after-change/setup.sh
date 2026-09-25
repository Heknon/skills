#!/bin/sh
# Builds the git history this scenario needs: main, then a branch with the change.
set -e
git init -q -b main
git config user.email dev@example.com
git config user.name "Yael Mor"
mkdir -p export docs/how-to docs/reference
cat > pyproject.toml <<'TOML'
[project]
name = "export"
version = "1.4.0"
requires-python = ">=3.11"

[project.scripts]
export-orders = "export.cli:main"
TOML
cat > export/__init__.py <<'PY'
PY
cat > export/cli.py <<'PY'
import argparse

DEFAULT_LIMIT = 100


def main():
    parser = argparse.ArgumentParser(prog="export-orders")
    parser.add_argument("--dry-run", action="store_true", help="print what would be exported")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help="orders per file")
    parser.add_argument("--out", default="out", help="folder to write CSV files to")
    args = parser.parse_args()
    print(args)
PY
cat > README.md <<'MD'
# export

Exports orders to CSV files for finance.

```powershell
uv run --no-sync export-orders --out D:\finance\orders
```

Use `--dry-run` first to see what would be exported.
MD
cat > docs/index.md <<'MD'
# Export

- [Export orders for finance](how-to/export.md)
- [Command line](reference/cli.md)
MD
cat > docs/how-to/export.md <<'MD'
# How to export orders for finance

1. Check what will be exported:

   ```powershell
   uv run --no-sync export-orders --dry-run
   ```

2. Export, 100 orders per file:

   ```powershell
   uv run --no-sync export-orders --out D:\finance\orders
   ```
MD
cat > docs/reference/cli.md <<'MD'
# Command line

| Option | Default | Meaning |
| --- | --- | --- |
| `--dry-run` | off | print what would be exported |
| `--limit` | `100` | orders per file |
| `--out` | `out` | folder to write CSV files to |
MD
cat > CHANGELOG.md <<'MD'
# Changelog

## 1.4.0

- Add `--out`.

## 1.3.0

- Add `--limit`.
MD
cat > mkdocs.yml <<'YML'
site_name: Export
theme:
  name: material
  font: false
nav:
  - Home: index.md
  - Export orders: how-to/export.md
  - Command line: reference/cli.md
YML
git add -A
git commit -qm "Export orders to CSV"
git checkout -q -b preview-option
sed -i 's/DEFAULT_LIMIT = 100/DEFAULT_LIMIT = 250/' export/cli.py
sed -i 's/"--dry-run", action="store_true", help="print what would be exported"/"--preview", action="store_true", help="print what would be exported, write nothing"/' export/cli.py
git commit -qam "Rename --dry-run to --preview; raise the default limit"
rm setup.sh

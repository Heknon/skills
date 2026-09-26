"""Write an app's OpenAPI document to a file, without starting a server.

    uv run --no-sync python <skill>/recipes/tools/openapi_dump.py orders_api.main:app openapi.json

Run it from the project root. It puts ./src and . on sys.path, imports the
app, calls app.openapi() and writes sorted, indented JSON in UTF-8, so two
dumps can be compared with `git diff --no-index old.json new.json`. It
writes the file itself because a PowerShell `>` redirect may change the
encoding. Importing the app runs its module-level code, not its lifespan.
"""

import importlib
import json
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 3 or ":" not in sys.argv[1]:
        print("usage: openapi_dump.py <module>:<app> <out.json>", file=sys.stderr)
        return 2
    target, out = sys.argv[1], Path(sys.argv[2])
    for extra in (Path.cwd() / "src", Path.cwd()):
        if extra.is_dir():
            sys.path.insert(0, str(extra))
    module_name, attr = target.split(":", 1)
    app = getattr(importlib.import_module(module_name), attr)
    spec = app.openapi()
    out.write_text(json.dumps(spec, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    ops = sum(1 for item in spec.get("paths", {}).values() for m in item if m != "parameters")
    print(f"wrote {out}: OpenAPI {spec.get('openapi')}, {len(spec.get('paths', {}))} paths, {ops} operations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Pull the ledger out of a worked example.

Usage: extract_golden.py <example.md> <outdir>

Writes <outdir>/ledger.md from the fenced block under the example's
"## The ledger" heading, and <outdir>/expected_summary.txt from the
checker summary line the example's answer quotes under "## Ledger check".
Exits 1 when either is missing.
"""

import os
import re
import sys


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    source, outdir = sys.argv[1], sys.argv[2]
    with open(source, encoding="utf-8") as handle:
        text = handle.read()
    heading = re.search(r"^## The ledger\s*$", text, re.M)
    if not heading:
        print(f"extract_golden: {source}: no '## The ledger' heading", file=sys.stderr)
        return 1
    block = re.search(r"^```markdown\s*\n(.*?)^```\s*$", text[heading.end():], re.M | re.S)
    if not block:
        print(f"extract_golden: {source}: no ```markdown block under '## The ledger'", file=sys.stderr)
        return 1
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "ledger.md"), "w", encoding="utf-8") as handle:
        handle.write(block.group(1))
    summary = re.search(r"^## Ledger check\s*\n((?:OK|NOT OK):[^.\n]*)", text, re.M)
    if not summary:
        print(f"extract_golden: {source}: no checker summary line under '## Ledger check' in the answer", file=sys.stderr)
        return 1
    with open(os.path.join(outdir, "expected_summary.txt"), "w", encoding="utf-8") as handle:
        handle.write(summary.group(1).strip() + "\n")
    print(f"extract_golden: wrote ledger.md and expected_summary.txt to {outdir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

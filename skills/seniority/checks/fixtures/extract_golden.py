#!/usr/bin/env python3
"""Pull the ledger out of a worked example.

Usage: extract_golden.py <example.md> <outdir>

Writes <outdir>/ledger.md from the fenced block under the example's
"## The ledger" heading, and <outdir>/answer.md from the fenced block
under "## The answer". Exits 1 when either is missing.
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
    answer_heading = re.search(r"^## The answer\s*$", text, re.M)
    answer = re.search(r"^```\s*\n(.*?)^```\s*$", text[answer_heading.end():], re.M | re.S) if answer_heading else None
    if not answer:
        print(f"extract_golden: {source}: no ``` block under '## The answer'", file=sys.stderr)
        return 1
    with open(os.path.join(outdir, "answer.md"), "w", encoding="utf-8") as handle:
        handle.write(answer.group(1))
    print(f"extract_golden: wrote ledger.md and answer.md to {outdir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

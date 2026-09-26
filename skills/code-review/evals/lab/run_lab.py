"""Measure the skill's mechanical parts on every sandbox and write record.md.

    python run_lab.py <scratch folder> [sandbox ...]

For each sandbox: build it with make_repo.py, `uv sync`, then on main and
on the change (feature, or main with incoming/*.patch applied):
- ruff, mypy and pytest summary lines, and the new tool lines
  (recipes/review_diff.py newerrors);
- the planted bug's proof (proofs.py): 1 = the bug shows;
- recipes/review_diff.py signs on the diff: which checklist IDs hit the
  planted lines, and how many leads there were in all;
- recipes/review_diff.py defs: how many changed contracts it lists.
Needs git and uv on PATH; LAB_MONGODB_URL for the three MongoDB proofs.
Nothing here is run by the model under test.
"""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

LAB = Path(__file__).resolve().parent
SKILL = LAB.parent.parent
SANDBOXES = LAB.parent / "sandboxes"
TOOL = SKILL / "recipes" / "review_diff.py"

# sandbox -> (diff range, planted lines "path:first-last", checklist pass expected)
PLANTED = {
    "pagination": ("main...HEAD", "src/shop/catalog.py:28-29", "correctness"),
    "lookup": (
        "main...HEAD",
        "src/shop/invoices.py:8-11 (outside the diff)",
        "callers",
    ),
    "refunds": ("main...HEAD", "src/shop/refunds.py:30-30", "correctness"),
    "clean": ("main...HEAD", "", "none: clean"),
    "status422": ("patch", "", "none: clean"),
    "login": ("main...HEAD", "src/shop/api.py:31-31", "security"),
    "users": ("main...HEAD", "src/shop/api.py:51-51", "architecture, security"),
    "mocktest": ("main...HEAD", "tests/test_pricing.py:11-17", "tests"),
    "rereview": ("HEAD~1..HEAD", "src/shop/points.py:31-31", "correctness"),
    "counter": ("main...HEAD", "src/shop/pages.py:16-20", "concurrency"),
    "docstring": ("main...HEAD", "", "none: nits only"),
    "defaults": ("main...HEAD", "src/shop/repository.py:22-22", "callers"),
    "swallow": ("main...HEAD", "src/shop/api.py:38-43", "errors"),
    "wide": ("main...HEAD", "src/shop/discounts.py:17-17", "correctness"),
}
CHECKLIST = {
    "COR": "correctness",
    "ERR": "errors",
    "EDG": "edge-cases",
    "CON": "concurrency",
    "SEC": "security",
    "TST": "tests",
    "API": "api-contract",
    "DAT": "data",
    "MOD": "models",
}


def run(cwd, *args, env=None):
    done = subprocess.run(args, cwd=cwd, capture_output=True, text=True, env=env)
    return done.returncode, (done.stdout + done.stderr).strip()


def last(text, pattern=r"."):
    lines = [l for l in text.splitlines() if re.search(pattern, l)]
    return lines[-1] if lines else "(no output)"


def tools(work):
    out = {}
    _, ruff = run(
        work,
        "uv",
        "run",
        "--no-sync",
        "ruff",
        "check",
        "--output-format",
        "concise",
        ".",
    )
    _, mypy = run(work, "uv", "run", "--no-sync", "mypy")
    _, test = run(
        work, "uv", "run", "--no-sync", "pytest", "-q", "-p", "no:cacheprovider"
    )
    out["ruff"] = last(ruff, r"^Found|^All checks")
    out["mypy"] = last(mypy, r"^Found|^Success")
    out["pytest"] = last(test, r"passed|failed|error")
    out["raw"] = ruff + "\n" + mypy
    return out


def proof(work, name, env):
    code, text = run(
        work, "uv", "run", "--no-sync", "python", str(LAB / "proofs.py"), name, env=env
    )
    return code, last(text)


def main():
    scratch = Path(sys.argv[1]).resolve()
    names = sys.argv[2:] or list(PLANTED)
    env = {**os.environ}
    rows, details = [], []
    for name in names:
        rng, planted, expected = PLANTED[name]
        work = scratch / name
        shutil.rmtree(work, ignore_errors=True)
        run(
            scratch,
            sys.executable,
            str(SANDBOXES / "make_repo.py"),
            str(SANDBOXES / name),
            str(work),
        )
        run(work, "uv", "sync", "-q")
        run(work, "git", "switch", "-q", "main")
        base = tools(work)
        base_proof = proof(work, name, env)
        if rng == "patch":
            patch = next((work / "incoming").glob("*.patch"))
            run(work, "git", "apply", str(patch))
            diff_file = patch
        else:
            run(work, "git", "switch", "-q", "feature")
            diff_file = scratch / f"{name}.diff"
            run(work, "git", "diff", f"--output={diff_file}", rng)
        head = tools(work)
        head_proof = proof(work, name, env)
        (scratch / f"{name}-base.txt").write_text(base["raw"])
        (scratch / f"{name}-head.txt").write_text(head["raw"])
        _, new = run(
            work,
            sys.executable,
            str(TOOL),
            "newerrors",
            str(scratch / f"{name}-base.txt"),
            str(scratch / f"{name}-head.txt"),
        )
        _, signs = run(work, sys.executable, str(TOOL), "signs", str(diff_file))
        _, defs = run(work, sys.executable, str(TOOL), "defs", str(diff_file))
        if rng == "patch":
            run(work, "git", "checkout", "--", ".")
        hit_ids, per_list = set(), {}
        m = re.match(r"(\S+):(\d+)-(\d+)", planted)
        for line in signs.splitlines():
            hit = re.match(r"(\S+):(\d+)  ([A-Z]+)(\d+)(?! \(removed)", line)
            if not hit:
                continue
            per_list[hit.group(3)] = per_list.get(hit.group(3), 0) + 1
            if (
                m
                and hit.group(1) == m.group(1)
                and int(m.group(2)) <= int(hit.group(2)) <= int(m.group(3))
            ):
                hit_ids.add(hit.group(3) + hit.group(4))
        rows.append(
            (
                name,
                expected,
                planted or "none",
                f"{base_proof[0]} / {head_proof[0]}",
                ", ".join(sorted(hit_ids)) or "-",
                last(signs).split(" lead")[0],
                ", ".join(f"{CHECKLIST[k]} {v}" for k, v in sorted(per_list.items()))
                or "-",
                last(defs, r"changed contract").split(" changed")[0],
                last(new).split(" new")[0],
            )
        )
        details.append(
            f"### {name}\n\n```\nmain:    {base['ruff']} | {base['mypy']} | {base['pytest']}\n"
            f"change:  {head['ruff']} | {head['mypy']} | {head['pytest']}\n"
            f"proof:   main {base_proof[1]}\n         change {head_proof[1]}\n```\n"
        )
        print(name, rows[-1][3], rows[-1][4])
    head = (
        "| Sandbox | Pass that should find it | Planted at | Proof main / change | "
        "Sign IDs on the planted lines | Leads in all | Leads on added lines, per checklist | "
        "Contracts (defs) | New tool lines |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
    )
    table = head + "".join("| " + " | ".join(r) + " |\n" for r in rows)
    text = (
        "# Lab record\n\nWritten by `run_lab.py`. Proof exit codes: 1 = the bug shows, "
        "0 = it does not, 125 = no MongoDB.\n\n"
        + table
        + "\n## Tool and proof lines\n\n"
        + "\n".join(details)
    )
    text += (
        "\n## Passes run by hand\n\n"
        "- users: architecture's searches (its `checklist/finding.md`) on the added "
        "lines: L3 at `src/shop/api.py:51` (`-> User`), L1 at `:52` "
        "(`await User.find_one(`). The leak is found by this pass, not by a sign.\n"
        "- lookup: `review_diff.py defs` listed `find_customer` (no longer raises "
        "`CustomerNotFound`); `git grep -n -w find_customer` then found the caller "
        "`src/shop/invoices.py:8`; `mypy --check-untyped-defs` reported "
        "`invoices.py:11` [union-attr] where the project's mypy passed.\n"
        "- defaults: `review_diff.py defs` printed the moved `list_orders` with "
        "`include_cancelled: bool = False` -> `= True`.\n"
    )
    (LAB / "record.md").write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()

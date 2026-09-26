"""A sequence editor for `git rebase -i` that needs no person: it replaces
git's todo list with a plan you wrote, after checking the plan.

    GIT_SEQUENCE_EDITOR="uv run --no-project python <abs>/todo.py <abs>/plan.txt"

Write plan.txt first, one line per commit, oldest first, in git's todo
form: `<verb> <hash> <subject>`. Allowed verbs:

    pick <hash>         keep the commit
    fixup <hash>        fold into the commit above, keep the message above
    fixup -C <hash>     fold into the commit above, take THIS message
    drop <hash>         remove the commit (say so in the answer)
    exec <command>      run a command, such as the tests

`reword`, `squash`, `edit`, `break` and `fixup -c` are refused: each opens
an editor or stops the rebase. To reword, make an `amend!` commit and use
`fixup -C` (see reference/rewrite.md).

The script refuses a plan that leaves out a commit of git's todo or names
one twice, so a commit cannot vanish by a typo. Lines starting with # and
blank lines are ignored. Checked on git 2.43.0 and 2.55.0.
"""
import re
import sys

REFUSED = {"reword", "r", "squash", "s", "edit", "e", "break", "b"}


def commits(lines):
    """The hashes named by pick/fixup/drop lines, in order."""
    found = []
    for line in lines:
        words = line.split()
        if not words or words[0].startswith("#"):
            continue
        verb = words[0]
        if verb in ("exec", "x"):
            continue
        if verb in REFUSED:
            raise SystemExit(f"todo.py: '{verb}' opens an editor or stops; refused: {line}")
        if verb in ("fixup", "f") and len(words) > 1 and words[1] == "-c":
            raise SystemExit(f"todo.py: 'fixup -c' opens an editor; use 'fixup -C': {line}")
        if verb in ("fixup", "f") and len(words) > 1 and words[1] == "-C":
            words = words[1:]
        if verb not in ("pick", "p", "fixup", "f", "drop", "d"):
            raise SystemExit(f"todo.py: unknown or unsupported verb '{verb}': {line}")
        if len(words) < 2 or not re.fullmatch(r"[0-9a-f]{4,64}", words[1]):
            raise SystemExit(f"todo.py: no commit hash on line: {line}")
        found.append(words[1])
    return found


def main(plan_path, todo_path):
    with open(plan_path, encoding="utf-8-sig") as f:
        plan = f.read().splitlines()
    with open(todo_path, encoding="utf-8") as f:
        todo = f.read().splitlines()
    want = commits(plan)
    have = [line.split()[1] for line in todo
            if line.split() and line.split()[0] == "pick"]
    dupes = {h for h in want if want.count(h) > 1}
    if dupes:
        raise SystemExit(f"todo.py: plan names these twice: {sorted(dupes)}")

    def same(a, b):
        return a.startswith(b) or b.startswith(a)

    missing = [h for h in have if not any(same(h, w) for w in want)]
    extra = [w for w in want if not any(same(h, w) for h in have)]
    if missing or extra:
        raise SystemExit(f"todo.py: plan does not match git's todo; "
                         f"missing {missing}, not in this rebase {extra}")
    with open(todo_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(line for line in plan if line.strip()) + "\n")
    sys.stderr.write("todo.py: todo replaced with the plan\n")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2])

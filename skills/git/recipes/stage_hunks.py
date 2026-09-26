"""Stage some hunks of one file without `git add -p`, which waits for
keyboard input an agent cannot give.

    uv run --no-project python stage_hunks.py list <path>
    uv run --no-project python stage_hunks.py stage <path> <n> [<n> ...]

`list` numbers the hunks of `git diff -- <path>` (the changes not yet
staged). `stage` feeds the chosen hunks to `git apply --cached`, so they
are staged and the working tree is left as it is. Run it from the
repository's top folder. The patch goes through a pipe, never a file, so
PowerShell's redirection cannot change its encoding. Checked on git
2.43.0 and 2.55.0.
"""
import subprocess
import sys


def diff(path):
    out = subprocess.run(
        ["git", "--no-pager", "diff", "--no-color", "--no-ext-diff", "-U3", "--", path],
        capture_output=True, check=True).stdout
    if not out:
        raise SystemExit(f"no unstaged changes in {path}")
    if b"\nBinary files " in out or out.startswith(b"Binary files "):
        raise SystemExit(f"{path} is binary; stage it whole or not at all")
    lines = out.splitlines(keepends=True)
    first = next(i for i, line in enumerate(lines) if line.startswith(b"@@"))
    header, hunks = lines[:first], []
    for line in lines[first:]:
        if line.startswith(b"@@"):
            hunks.append([])
        hunks[-1].append(line)
    return header, hunks


def main(argv):
    if len(argv) < 2 or argv[0] not in ("list", "stage"):
        raise SystemExit(__doc__)
    header, hunks = diff(argv[1])
    if argv[0] == "list":
        for n, hunk in enumerate(hunks, start=1):
            print(f"--- hunk {n} ---")
            sys.stdout.write(b"".join(hunk).decode("utf-8", "replace"))
        return
    chosen = sorted({int(n) for n in argv[2:]})
    if not chosen or chosen[0] < 1 or chosen[-1] > len(hunks):
        raise SystemExit(f"choose hunk numbers from 1 to {len(hunks)}")
    patch = b"".join(header) + b"".join(b"".join(hunks[n - 1]) for n in chosen)
    done = subprocess.run(["git", "apply", "--cached", "-"], input=patch)
    if done.returncode:
        raise SystemExit("git apply --cached refused the patch; nothing was staged")
    print(f"staged hunks {chosen} of {argv[1]}; check with: git diff --cached -- {argv[1]}")


if __name__ == "__main__":
    main(sys.argv[1:])

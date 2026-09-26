"""Show or set a file's line endings, byte for byte, so a one-line fix
stays a one-line diff.

    uv run --no-project python eol.py show <path> ...
    uv run --no-project python eol.py crlf <path> ...
    uv run --no-project python eol.py lf <path> ...

`show` counts CRLF and bare LF line ends. `crlf` and `lf` rewrite the
file with one kind throughout and change nothing else. Use it to put
back what the repository holds: `git ls-files --eol <path>` shows the
index (`i/crlf`) and the working tree (`w/lf`). Checked on git 2.43.0.
"""
import sys


def counts(data):
    crlf = data.count(b"\r\n")
    return crlf, data.count(b"\n") - crlf


def main(argv):
    if len(argv) < 2 or argv[0] not in ("show", "crlf", "lf"):
        raise SystemExit(__doc__)
    for path in argv[1:]:
        with open(path, "rb") as f:
            data = f.read()
        if b"\0" in data:
            print(f"{path}: binary, left alone")
            continue
        if argv[0] != "show":
            data = data.replace(b"\r\n", b"\n")
            if argv[0] == "crlf":
                data = data.replace(b"\n", b"\r\n")
            with open(path, "wb") as f:
                f.write(data)
        crlf, lf = counts(data)
        print(f"{path}: {crlf} CRLF, {lf} LF")


if __name__ == "__main__":
    main(sys.argv[1:])

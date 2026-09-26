# Seams

**Verdict you produce:** for each thing the code reads besides its
arguments, the seam a test uses to control it, and proof that adding
the seam changed nothing.

```
reads:   <clock | file | environment | network | random | global state>
seam:    <module function _today() | parameter with a default | object passed in | none needed: tmp_path>
added:   <commit, and the program's output before and after it, identical>
verdict seam: <seams in place | stop: <what cannot be controlled without a behaviour change>>
```

A seam is a place where a test can change what the code uses without
editing the code under test. Legacy code rarely has one, so the first
edit is the smallest one that makes a seam, done by hand, before any
test exists. Keep it mechanical, and check it with the program's own
output.

## Seams that worked in the lab

| The code reads | Seam | How the test uses it |
| --- | --- | --- |
| `datetime.date.today()` | a module function: `def _today(): return datetime.date.today()`, and `today = _today()` in the code | `monkeypatch.setattr(report, "_today", lambda: datetime.date(2026, 3, 2))` |
| a file path | none needed if the path is an argument | copy the sample to `tmp_path` and pass that path |
| an environment variable read inside a function | none needed | `monkeypatch.setenv("SVC_TIMEOUT", "3")` |
| an environment variable read at import (`TIMEOUT = int(os.environ.get(...))`) | the module constant | `monkeypatch.setattr(net, "TIMEOUT", 3)`; `setenv` after import changes nothing (lab: `assert (10, 3) == (3, 3)`) |
| module-level state (`_levels = {}`) | the state itself | clear or fill it in a fixture, as the code's other users do |

A parameter with a default (`def build_report(path, today=None)`) is a
seam too, and a clean one, but it adds to the public signature; prefer
the module function for a public function unless the person wants the
parameter.

## The clock cannot be patched in place

```
TypeError: cannot set 'today' attribute of immutable type 'datetime.date'
```

(lab, Python 3.12.14, for `datetime.date.today = ...`). Patch the name
the code uses, which is why the seam is a module function.

## Show the seam changed nothing

Run the program's own entry point before and after the seam, on the
same day and data, and compare:

```powershell
uv run --no-sync python -m billing.mail data/invoices.csv | Out-File -Encoding utf8 .ledger/before.txt
# add the seam
uv run --no-sync python -m billing.mail data/invoices.csv | Out-File -Encoding utf8 .ledger/after.txt
git diff --no-index --exit-code .ledger/before.txt .ledger/after.txt
```

In the lab the report was identical. Commit the seam alone: "Add a
clock seam to build_report".

## Never

- Never install a package to fake the clock or the network; air gapped,
  it cannot be installed, and a seam does the job.
- Never add a seam that changes what the code does when no test uses
  it: the default path must be exactly the old one.

# Golden master

**Verdict you produce:** a file of many outputs, written once from the
code as it is, and a test that compares a fresh run with it after every
step.

```
golden:     tests/golden/<name>.txt, <n> lines, from <inputs>
test:       <node id>
fails when: <deliberate break> -> <the first differing line>
verdict golden: <in place | not needed: characterization tests cover the steps>
```

Use it when the code has many inputs and the output is text or data you
can print: reports, exports, rendering, a calculation over a table.
Characterization tests pin chosen inputs; a golden master pins
hundreds at once, and finds the cases nobody thought to choose.

## Steps

1. **Pick a sweep of inputs** that is fixed and fast: every week of a
   year, every row of a sample file, every combination of a few options.
   Everything the code reads besides its inputs goes through a seam
   (`legacy/seams.md`).
2. **Write the test so the first run writes the file and fails**, and
   later runs compare:

   ```python
   GOLDEN = Path(__file__).resolve().parent / "golden" / "build_report.txt"


   def render_all(monkeypatch) -> str:
       chunks = []
       day = datetime.date(2026, 1, 1)
       while day.year == 2026:
           monkeypatch.setattr(report, "_today", lambda day=day: day)
           chunks.append(report.build_report(str(DATA)))
           day += datetime.timedelta(days=7)
       return "\n\n".join(chunks) + "\n"


   def test_golden_master(monkeypatch):
       actual = render_all(monkeypatch)
       if not GOLDEN.exists():
           GOLDEN.parent.mkdir(parents=True, exist_ok=True)
           GOLDEN.write_text(actual, encoding="utf-8", newline="\n")
           pytest.fail(f"golden file written to {GOLDEN}; read it, commit it, run again")
       assert actual == GOLDEN.read_text(encoding="utf-8")
   ```

3. **Run it twice**: the first run fails with `golden file written`,
   the second passes. Read the file: it is what the code does today,
   oddities included. In the lab: 53 reports, 247 lines.
4. **Make it fail**: a break that moved the "overdue" flag from 60 to 61
   days failed it at the one report where a customer was exactly 61
   days late (`-    61 days !` / `+    61 days`); the three
   characterization tests, which used other dates, passed that break.
5. **Commit the file and the test** before the first step. Write the
   file with `newline="\n"` and compare as text, so line endings on
   Windows do not make it differ (git's `reference/windows.md` for
   `core.autocrlf`).
6. After the refactoring, keep it or delete it, as the person prefers;
   it pins every oddity, so any later fix must regenerate it on purpose
   (delete the file, run twice, read the diff in `git diff`).

## Never

- Never regenerate the golden file to make a refactoring step pass.
  A difference is a red step (`core/step-loop.md`).
- Never include the real date, a random value, a path of the machine or
  a memory address in the output.

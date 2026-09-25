# Docstrings

**What it decides:** which functions and classes get a docstring, what
it says, and how to edit the code without changing anything else.

Too many docstrings is as real a fault as too few. A docstring that
repeats the name and the signature costs every reader time, and drifts.
A missing one on a function with a hidden contract costs a bug. Decide
per function, from the code.

## Step 1: learn the repository's style

Read, in this order, and stop at the first that answers:

1. `mkdocs.yml`, `docstring_style:` under mkdocstrings. If the module is
   shown in the API reference, this style is required.
2. `pyproject.toml`, `[tool.ruff.lint.pydocstyle]` `convention =`.
3. Three existing docstrings in the same package, the longest ones.

Copy from those docstrings: the quotes (`"""`), whether the summary sits
on the first line, whether it ends with a full stop, the section names
(`Args:`, `Returns:`, `Raises:` for google; underlined `Parameters` for
numpy; `:param x:` for sphinx), indentation, and whether types are
repeated in `Args:` (usually not, when the signature has annotations).

## Step 2: for each function or class, answer from the code

1. **Is it public?** No leading underscore, and it is listed in
   `__all__`, imported by another module or repository, or an entry
   point. Use navigation, Trace in.
2. **Do the name, parameter names and annotations tell a caller
   everything they must know?**
3. **Does it do something the signature hides?** Raise, change an
   argument it was given, write a file, call the network or a database,
   change a global or a module variable, sleep or block, retry, cache,
   or need to be called in a certain order. Look for `raise`, `open(`,
   `.write(`, `requests.`, `httpx.`, `session.`, `global `, `time.sleep`,
   `@cache`, `@lru_cache`, loops around a call with `except`.
4. **Does a value carry a unit, a range, a format or a special
   meaning?** Seconds or milliseconds, cents or units, `None` meaning
   all, `-1` meaning no limit, a date format.
5. **Does it return a shape the annotation does not spell out?** `dict`,
   `tuple`, `Any`, or no annotation: which keys, which positions.
6. **Is there a reason it is written this way that a reader would get
   wrong?** Only if a commit, pull request, issue or person says so
   (navigation, History).

## Step 3: the verdict

| Answers | Docstring |
| --- | --- |
| 1 no, 2 yes, 3 to 6 no | **none**. If one exists and only repeats the name, it can go (see Scope below) |
| 1 yes, 2 yes, 3 to 6 no | **one line**, only if the module's public functions all have one; otherwise none |
| 1 yes, 2 no | **one-line summary**, then 3 to 6 as they apply |
| any yes to 3, 4, 5 | **exactly those facts**, one line or section entry each |
| 6 yes, with a source | the reason, in one sentence; say where it comes from in your answer |
| 6 yes, without a source | nothing; the reason is not written (invariant 2) |

Every fact in a docstring is read from the code: the unit from where the
value is used (`time.sleep(timeout)` is seconds), the keys from the
`return` statement, the exceptions from `raise` lines. Never write what
such a function usually does.

## Never

- Never repeat a parameter's name and type as its description:
  `customer_id: The customer id.` says nothing. Leave the parameter out
  of `Args:`, or say what the signature does not (format, range, unit).
- Never retell the body line by line.
- Never write a comment that says what the next line does.
- Never add `>>>` examples unless the repository already runs doctests
  (`--doctest-modules` or `doctest` in the test config), and you ran
  them.

## Scope

- Asked to **add** docstrings: add where the verdict says so. Do not
  delete existing ones; list the ones that only repeat the name under
  *Not done*.
- Asked to **clean up** or **improve** docstrings: add, rewrite and
  delete as the verdicts say.
- Found a bug while reading? Document what the code does today, and
  report the suspected bug under *Not done*. Never fix it in a docstring
  change.

## Editing the code safely

Only docstrings and comments change. Never change a signature, an
annotation, a default, an import, the order of anything, or formatting
outside the docstring.

After editing, check all three, and paste what each showed:

1. `git diff -U0 -- <file>`: every changed line is inside a docstring or
   a comment.
2. The module still imports:
   `uv run --no-sync python -c "import billing.charges"`.
3. The tests for that package pass: `uv run --no-sync pytest -q <tests
   folder>`. Doctests run here too if the repository enables them.

If the module is in the API reference, run the strict build as well
(`mkdocs/site.md`): a docstring naming a parameter that does not exist
fails it.

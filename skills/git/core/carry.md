# Carry work across the air gap

**Verdict you produce:** the files, their checksums, the verify output,
and the commands for the other side.

```
file:     <name>.bundle (<size> bytes), sha256 <hash>
contains: <ref> at <hash>
requires: <base hash>, which the other side has as <branch>
verified: git bundle verify on a clone with only the base: "is okay"
other side: <the commands>
verdict carry: <ready | stopped: <why>>
```

Handing the file over leaves this machine: only when asked.

## Bundle (preferred: keeps hashes)

1. Decide the base the other side already has, usually `origin/main`
   as it was when both sides last matched. List what goes:
   `git log --oneline origin/main..feature/report`.
2. Make the bundle of that range, naming the branch so the other side
   gets a ref:
   ```
   git bundle create ../report.bundle origin/main..feature/report
   git bundle list-heads ../report.bundle
   ```
   `list-heads` printed `c6f63ee... refs/heads/feature/report`. A range
   given as `HEAD~3..HEAD` gave a ref called `HEAD` instead.
3. Checksum: `Get-FileHash ..\report.bundle -Algorithm SHA256`
   (`not run on Windows`) or `sha256sum ../report.bundle >
   ../report.bundle.sha256`.
4. Verify on a clone that has only the base, as the other side does:
   ```
   git clone <origin> ../base-check
   git -C ../base-check bundle verify ../report.bundle
   ```
   Lab output:
   ```
   ../report.bundle is okay
   The bundle contains this ref:
   c6f63ee... refs/heads/feature/report
   The bundle requires this ref:
   5074d14...
   ```
   On a clone without the base it fails: `error: Repository lacks these
   prerequisite commits:`. If the other side may be older than
   `origin/main`, choose an older base.
5. The other side:
   ```
   sha256sum -c report.bundle.sha256      (or Get-FileHash and compare)
   git bundle verify report.bundle
   git fetch report.bundle feature/report:feature/report
   git log --oneline main..feature/report
   ```
   In the lab the fetch printed `* [new branch] feature/report ->
   feature/report` and the three commits kept their hashes.

A bundle of the whole branch (`git bundle create x.bundle
feature/report`) needs no base but carries all history; fine for a first
transfer.

## Patches (when the other side wants to review files)

```
git format-patch -o ../patches origin/main..feature/report
```

wrote `0001-Add-report-rows.patch` and two more. The other side, on a
branch from the same base: `git am ../patches/*.patch` (in PowerShell,
`git am (Get-ChildItem ..\patches\*.patch)`, `not run on Windows`). The
commits keep author and message but get **new hashes** (a new committer
date). `git am ../patches` given the folder printed nothing and applied
nothing. Use `git am -3` so a patch that does not apply cleanly becomes
a conflict (`core/conflicts.md`); then `git add` and `git am --continue`
(no editor in the lab), or `git am --abort` to put everything back.

## Never

- Never zip the repository folder: it carries `.git/config` (remotes,
  maybe credentials), hooks, ignored files such as `.env`, and a working
  tree that may not match any commit.
- Never write a patch with PowerShell `>` (`reference/windows.md`); use
  `-o` or `git diff --output=<file>`.

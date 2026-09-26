# Worked example: a branch carried across the air gap by bundle

Kinds: Orient, Carry. Outputs are from a lab run of the `carry` sandbox
on git 2.43.0. The PowerShell checksum line is `not run on Windows`.

## The ask

> Prepare my feature/report branch to take to the other network. Their
> copy has main as it is on origin.

## Steps

1. **Orient.** `git status -sb`: `## feature/report`, clean, no
   upstream. What goes: `git log --oneline origin/main..feature/report`
   ```
   c6f63ee Add report footer
   5dbf269 Add report totals
   ef2c111 Add report rows
   ```
   The base the other side has is `origin/main` (`5074d14 Add readme`).
2. **The bundle of the range**, naming the branch:
   ```
   git bundle create ../report.bundle origin/main..feature/report
   git bundle list-heads ../report.bundle
   ```
   `c6f63ee... refs/heads/feature/report`. Size 983 bytes.
3. **Checksum.** `sha256sum ../report.bundle > ../report.bundle.sha256`:
   `67f8cef7a47fcad1bea1887a08262586026a3d7a99c9c0a70b0dc5859ca5e64a`.
   On Windows: `Get-FileHash ..\report.bundle -Algorithm SHA256`.
4. **Verify as the other side would**, on a clone with only the base:
   ```
   git clone ../origin.git ../base-check
   git -C ../base-check bundle verify ../report.bundle
   ```
   ```
   ../report.bundle is okay
   The bundle contains this ref:
   c6f63eebed223bed487e507608192ba6442a5bd5 refs/heads/feature/report
   The bundle requires this ref:
   5074d148b66de7b0129695f67c6545a1ecb4ad14
   The bundle uses this hash algorithm: sha1
   ```
5. **Rehearse the other side** in `../base-check`: `sha256sum -c`
   printed `../report.bundle: OK`; `git fetch ../report.bundle
   feature/report:feature/report` printed `* [new branch]
   feature/report -> feature/report`; `git log --oneline
   main..feature/report` listed the same three hashes.
6. Nothing was handed over or pushed: that is the person's step.

## The answer

```
## Result
../report.bundle (983 bytes) holds feature/report at c6f63ee, three
commits on top of origin/main 5074d14 "Add readme", which the other
side must have. SHA-256 in ../report.bundle.sha256:
67f8cef7a47fcad1bea1887a08262586026a3d7a99c9c0a70b0dc5859ca5e64a

On the other network, in their clone:
  Get-FileHash report.bundle -Algorithm SHA256   (compare with the above)
  git bundle verify report.bundle
  git fetch report.bundle feature/report:feature/report
  git log --oneline main..feature/report         (expect c6f63ee, 5dbf269, ef2c111)

## State
## feature/report, clean; nothing pushed.

## Checked
- git bundle verify on a fresh clone of origin (base only): "is okay",
  requires 5074d14.
- The fetch rehearsed in that clone gave the same three hashes.

## Not checked
- That the other network's main is really at 5074d14; if it is older,
  verify says "Repository lacks these prerequisite commits" and a
  bundle from an older base is needed.
```

# Publish: prepare a release, and upload only when asked

**Verdict you produce:** what would be uploaded, where, and the dry run;
the upload's output only when the person asked for the upload.

```
version:  <x.y.z>, the wheel's file name and METADATA agree; tag <tag> points at this commit: <yes | not tagged>
files:    dist/<name>-<x.y.z>.tar.gz, dist/<name>-<x.y.z>-py3-none-any.whl (inspected, verified)
target:   <publish URL>  (from --index <name> | --publish-url)
dry run:  uv publish --index <name> --dry-run --trusted-publishing never -> "Checking 2 files against <url>"
upload:   <not done: needs <what> | done: the "Uploading" lines>
```

## The default is PyPI

`uv help publish` (0.12.19): `--publish-url` "Defaults to PyPI's publish
URL (<https://upload.pypi.org/legacy/>)". In the lab, network cut:

- `uv publish` with no URL printed `Publishing 2 files to
  https://upload.pypi.org/legacy/` and tried to upload.
- `uv publish --dry-run` with no URL printed `Checking 2 files against
  https://upload.pypi.org/legacy/` and **tried to reach
  `https://upload.pypi.org/_/oidc/audience`** (trusted publishing).

So a dry run is not safe without a target. Every `uv publish` you run
names the internal index: `--index <name>` (with `publish-url` in its
table) or `--publish-url <url>`. With none configured, stop and ask.

## Steps

1. **Where do releases go?** Look for a `publish-url` in
   `[[tool.uv.index]]`, and for a CI job that publishes on a tag (the
   deployment skill's publish component builds with `uv build` and uploads
   with the job token). Releases go through that job on a tag; a manual
   upload happens only when the person asks for it.
2. **Version.** The version in `pyproject.toml` (or from the tag,
   `core/versioning.md`) is new: not already on the index. The same
   version cannot be uploaded twice (lab, a local index:
   `Server returned status code 409 Conflict`, `Package
   'acme_report-1.0.0-py3-none-any.whl' already exists!`; GitLab refuses
   it too, deployment's `gitlab/python.md`).
3. **Build clean and verify.** `uv build --clear`, then
   `core/build-and-inspect.md` and `core/verify.md` on exactly these files.
   A workspace member: `core/member-release.md` first.
4. **Dry run against the internal index:**
   ```
   uv publish --index internal --dry-run --trusted-publishing never dist\acme_report-1.2.0*
   ```
   Lab: `Checking 2 files against http://127.0.0.1:8900/`; with read
   credentials it also said `File ... already exists, skipping` for
   files already there. `--trusted-publishing never` stops the attempt
   to fetch an OIDC token, which otherwise prints a `Trusted publishing
   failed` note on every run outside CI.
5. **Upload, only when asked**, with the same command without
   `--dry-run`. Credentials come from the environment: for `--index
   internal`, `UV_INDEX_INTERNAL_USERNAME` and `_PASSWORD` were used for
   the upload in the lab; otherwise `UV_PUBLISH_USERNAME` and
   `UV_PUBLISH_PASSWORD`, or `UV_PUBLISH_TOKEN`. Without them:
   `Missing credentials for <url>`.
6. **Retrying a half-finished upload:** with `--index` (or
   `--check-url <index url>`) files already on the index are skipped:
   `File acme_report-1.0.0.tar.gz already exists, skipping`.

## What an upload cannot undo

An uploaded version stays. A broken release is fixed by the next
version, not by deleting and re-uploading. That is why the wheel is
verified before step 5, and why step 5 waits for the person.

## Never

- Never run `uv publish` without `--index` or `--publish-url`, not even
  with `--dry-run`.
- Never publish from a workstation because CI failed; find why CI failed.
- Never type a password or token on the command line you show or in a
  file; set it in the environment for that one command
  (`uv/config.md`).

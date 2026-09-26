# uv configuration: indexes, credentials, the CA, variables

uv 0.12.19, lab unless marked. The meaning of the index tables is in
`core/indexes.md`; the CI/CD variables that carry these values are the
deployment skill's.

## Where settings come from

| Place | Holds | Lab |
| --- | --- | --- |
| `pyproject.toml` `[tool.uv]`, `[[tool.uv.index]]`, `[tool.uv.sources]` | the project's settings; committed | wins over the user file for the default index |
| `uv.toml` beside `pyproject.toml` | the same keys without `tool.uv.` | not used here |
| the user `uv.toml` | per machine: `[[index]]` tables with the same keys | Linux: `$XDG_CONFIG_HOME/uv/uv.toml` (`-v` prints `Found user configuration in: ...`); Windows: `%APPDATA%\uv\uv.toml` (not run on Windows) |
| environment variables | per shell or CI job | override files; below |

`uv -v <command>` prints which configuration files were read.

A misspelled key directly under `[tool.uv]` gives a warning that lists
every valid key and is otherwise ignored:

```
warning: Failed to parse `pyproject.toml` during settings discovery:
  ...
  unknown field `index-stratgy`, expected one of `required-version`, `system-certs`, ...
```

A misspelled key inside a `[[tool.uv.index]]` table gives nothing
(`explicitt = true` was silently ignored).

## Credentials for an index

For an index named `internal` (lab, against a local index that answers
401 without them):

| Way | How | Notes |
| --- | --- | --- |
| variables | `UV_INDEX_INTERNAL_USERNAME`, `UV_INDEX_INTERNAL_PASSWORD` | the name upper-cased, `-` as `_`: `acme-internal` is `UV_INDEX_ACME_INTERNAL_...`; used for reading, and by `uv publish --index internal` for the upload |
| netrc | a `.netrc` in the home folder: `machine <host> login <user> password <secret>` | Windows file name and place: not run on Windows |
| `uv auth login <url> --username <user> --password <secret>` | stores them for that URL | Linux: plain text in `~/.local/share/uv/credentials/credentials.toml` (`uv auth dir` prints the folder); Windows place: run `uv auth dir` (not run on Windows) |
| publishing only | `UV_PUBLISH_USERNAME`, `UV_PUBLISH_PASSWORD`, or `UV_PUBLISH_TOKEN` | |

The person sets the secret; you never type, print or read it. Check that
it is there, not what it is (PowerShell 7.5 on Linux; not run on
Windows):

```
[bool]$env:UV_INDEX_INTERNAL_USERNAME      # True
[bool]$env:UV_INDEX_INTERNAL_PASSWORD      # True
$env:UV_INDEX_INTERNAL_PASSWORD.Length     # 6: set, and not empty
```

A plain `Read-Host` shows what is typed; `Read-Host "Index password"
-MaskInput` exists in PowerShell 7.5 (`Get-Command Read-Host -Syntax`)
if the person wants a prompt. Without credentials the resolver says the
package `was not found in the package registry` and adds `hint: An index
URL (...) could not be queried due to a lack of valid authentication
credentials (401 Unauthorized)`.

Credentials written into an index `url` are stripped from `uv.lock`
(lab), but `pyproject.toml` is committed: never write them there.

## The internal CA

Lab: an index served over HTTPS with a certificate from a private CA.

| Setting | Result |
| --- | --- |
| nothing | `invalid peer certificate: UnknownIssuer`, with `hint: Consider enabling use of system TLS certificates with the --system-certs command-line flag` |
| `UV_SYSTEM_CERTS=1` (or `--system-certs`), CA not in the system store | still `UnknownIssuer` |
| `SSL_CERT_FILE=<ca.pem>` | resolved |
| `uv pip install --cert <ca.pem>` | installed; `--cert` exists only on `uv pip install` among the commands used here |
| `UV_NATIVE_TLS=true` | works as before but warns: ``The `UV_NATIVE_TLS` environment variable is deprecated and will be removed in a future release. Use `UV_SYSTEM_CERTS` instead.`` |

On Windows the internal CA is usually in the Windows certificate store,
where `UV_SYSTEM_CERTS=1` would read it (not run on Windows). Otherwise
point `SSL_CERT_FILE` at the CA file.

## Variables

| Variable | Does | Lab note |
| --- | --- | --- |
| `UV_DEFAULT_INDEX` | replaces the default index | replaced the project's default for `uv build`; `uv add` wrote it into `pyproject.toml` as an unnamed `default = true` index; `uv sync --locked` failed against a lock made with another index |
| `UV_INDEX` | adds indexes | |
| `UV_INDEX_STRATEGY` | `first-index` (default), `unsafe-first-match`, `unsafe-best-match` | never the unsafe ones (`core/indexes.md`) |
| `UV_OFFLINE` | as `--offline` | |
| `UV_PYTHON_DOWNLOADS=never` | never download a Python | air gapped |
| `UV_PYTHON` | which interpreter | a system path here makes `uv pip` aim at it |
| `UV_CACHE_DIR` | the cache folder | |
| `UV_PROJECT_ENVIRONMENT` | where `uv sync` puts the venv | deployment's image recipe uses `/app/.venv` |
| `UV_VENV_CLEAR=1` | as `uv venv --clear` | |
| `UV_PUBLISH_URL`, `UV_PUBLISH_INDEX`, `UV_PUBLISH_CHECK_URL` | as the `uv publish` flags | |
| `SETUPTOOLS_SCM_PRETEND_VERSION` | forces a git-derived version | `core/versioning.md` |

## Pin uv itself

```toml
[tool.uv]
required-version = ">=0.12.19"
```

A uv outside the range stops every command: ``Required uv version
`>=0.13` does not match the running version `0.12.19`.``

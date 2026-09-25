# Connect to GitLab

**Verdict you produce:** how you reach this GitLab, as whom, with which
rights, shown by commands that answered.

```
instance:   https://gitlab.example.com, GitLab <version>, <Community | Enterprise> Edition
channel:    <REST API | glab | GitLab MCP server>, each that works
identity:   <username>, token "<name>", scopes <...>, expires <date>
access:     <project>: <role>
trust:      <system store | CA file>
```

## Steps

1. **The instance.** Take the URL from the person, a Git remote
   (`git remote -v`), or `CI_SERVER_URL` in a job. Without a token,
   `GET /api/v4/version` answers `401` (*lab*): the server is reachable,
   and the token comes next.
2. **Trust.** An internal CA must be trusted, never skipped:
   - PowerShell and `Invoke-RestMethod`: the CA in the Windows certificate
     store (an administrator installs it);
   - `curl.exe`: `--cacert <pem>` or the Windows store;
   - `glab`: `GLAB_CA_CERT=<pem>` or `glab config set ca_cert <pem> --host <host>`;
   - Python and uv: `SSL_CERT_FILE=<pem>`; the discovery script:
     `GITLAB_CA_FILE=<pem>`;
   - Node (the MCP bridge): `NODE_EXTRA_CA_CERTS=<pem>`.
3. **A token**, the least that does the job (`core/access.md`):
   | Work | Scope |
   | --- | --- |
   | read pipelines, jobs, logs, files, variables' names, lint the committed configuration | `read_api` |
   | lint content that is not committed (a child pipeline file, a draft), and anything that changes GitLab | `api` |
   | GitLab's MCP server | `mcp`, a separate token (`gitlab/mcp.md`) |
   | clone | `read_repository` |

   Read it at a prompt into `$env:GITLAB_TOKEN`, never on a command line
   (`core/access.md` shows the PowerShell 5.1 and 7 forms).
4. **Prove it**, and write down the answers:
   ```powershell
   $h = @{ "PRIVATE-TOKEN" = $env:GITLAB_TOKEN }
   Invoke-RestMethod "$GitLab/api/v4/version" -Headers $h                                   # version, "enterprise"
   Invoke-RestMethod "$GitLab/api/v4/user" -Headers $h | Select-Object username, is_admin
   Invoke-RestMethod "$GitLab/api/v4/personal_access_tokens/self" -Headers $h | Select-Object name, scopes, expires_at, active
   (Invoke-RestMethod "$GitLab/api/v4/projects/$([uri]::EscapeDataString('group/project'))" -Headers $h).permissions
   ```
   *lab:* `personal_access_tokens/self` answered with the token's name,
   scopes and expiry; `permissions` holds `project_access` and
   `group_access`, each with `access_level`: 10 Guest, 15 Planner,
   20 Reporter, 25 Security Manager, 30 Developer, 40 Maintainer,
   50 Owner. *lab:* a Developer (30) got `403` listing a project's CI/CD
   variables and `200` linting its configuration: the variables API
   needs Maintainer (40).
5. **`glab`**, if it will be used: `glab auth login --hostname <host>
   --stdin`, then `glab auth status` (`gitlab/glab.md`).
6. **The MCP server**, if the agent should use GitLab's tools directly:
   ask whether an administrator has enabled it, then `gitlab/mcp.md`.

## Which channel for what

| Need | Channel |
| --- | --- |
| pipelines, jobs, logs, merge requests, files, from the agent's tools | GitLab MCP server |
| lint, merged configuration, discovery, variables, environments, packages, job token allowlist | REST API or `glab` |
| a map of the whole pipeline | `recipes/tools/ci_map.py` (`core/discover.md`) |
| inside a pipeline | the REST API with `CI_JOB_TOKEN` (`gitlab/job-token.md`) |

## Never

- Never use a token with more scopes, or a more powerful user, than the
  task needs; never an administrator's token for reading.
- Never paste a token into a file in the repository, a settings file that
  is shared, or the conversation.
- Never `-k`, `--insecure`, `-SkipCertificateCheck` or
  `insecure-skip-tls-verify` to get past a certificate error.

## Stop and ask

- The token lacks a scope or role the task needs. Say which, and let the
  person create or ask for one; do not look for another token.

# A GitLab merge request

**Not run against GitLab.** The lab had no GitLab instance. The paths
below were read in the installed source of python-gitlab 8.5.0
(`gitlab/v4/objects/merge_requests.py`, `notes.py`), which is the only
evidence here; what the server returns on GitLab 19.4 is not verified.
Before relying on a field, read it in the instance's own answer, or its
`/help/api/merge_requests.md` page (deployment: SKILL.md, "Read the
versions first").

The deployment skill owns access: the token and its scope, the CA, the
PowerShell calls, pagination (`core/connect.md`, `gitlab/api.md`).
This skill uses only the calls below. `read_api` is the scope for
reading; posting a note needs `api` (deployment: `core/connect.md`).

## Read the merge request

```powershell
$h = @{ "PRIVATE-TOKEN" = $env:GITLAB_TOKEN }
$p = [uri]::EscapeDataString("shop/web")
$mr = Invoke-RestMethod "$GitLab/api/v4/projects/$p/merge_requests/42" -Headers $h
$mr | Select-Object iid, title, source_branch, target_branch, sha
$mr.description
```

| Call (python-gitlab 8.5.0 path) | Gives | Used for |
| --- | --- | --- |
| `GET /projects/:id/merge_requests/:iid` | the MR: title, description, branches, head `sha` | the claim to check, and what to fetch |
| `GET /projects/:id/merge_requests/:iid/commits` | the MR's commits | `core/scope.md` step 4 |
| `GET /projects/:id/merge_requests/:iid/changes` | the changed files with their diffs; python-gitlab lists `access_raw_diffs` as its optional argument | only when there is no checkout |
| `GET /projects/:id/merge_requests/:iid/versions` | one entry per push | re-review: which head the last review saw |
| `GET /projects/:id/merge_requests/:iid/notes` | the comments | earlier reviews |
| `POST /projects/:id/merge_requests/:iid/notes` body `{"body": "<text>"}` | a new comment (python-gitlab requires `body`) | only when asked (below) |

Reading changes nothing. Pages follow deployment's `gitlab/api.md`
(Pagination).

## Prefer a checkout to the API's diff

The tools, the tests and the caller search need the code, not a diff
in JSON. Fetch the MR's branch and follow `sources/git-diff.md`:

```powershell
git fetch origin <source_branch>
git switch <source_branch>
git rev-parse HEAD                  # must equal $mr.sha, or the MR moved on
```

For an MR from a fork, the source branch is not on `origin`.
`git ls-remote origin "refs/merge-requests/*"` lists what the server
offers (*not run*: from memory, GitLab publishes each MR's head as
`refs/merge-requests/<iid>/head`); fetch that ref only if it is listed.

## Posting the review (only when asked)

Posting is outward-facing (seniority invariant 6): show the text first,
post only on a yes, once, as one note with the answer's four headings.
Line-by-line discussions are not covered: their position fields were
not verified on 19.4.

```powershell
$body = @{ body = (Get-Content -Raw $env:TEMP\review.md) } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "$GitLab/api/v4/projects/$p/merge_requests/42/notes" `
  -Headers $h -ContentType "application/json" -Body $body | Select-Object id, created_at
```

## Never

- Never approve, merge, rebase or close an MR from a review.
- Never post more than the one note the person agreed to.

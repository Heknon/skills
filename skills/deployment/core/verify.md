# Verify

**Verdict you produce:** for every file you changed, the check that ran
and its verdict line. A change is not done until its checks ran, or the
answer says why one could not.

## Checks that change nothing

| Changed | Check | Verdict line |
| --- | --- | --- |
| `.gitlab-ci.yml` or an included file | CI lint: `glab ci lint` in the repository, or `POST /projects/:id/ci/lint` with the content (`gitlab/api.md`) | `valid: true`, no errors; read the warnings too |
| which jobs run | dry-run lint for the default branch and for a tag: `POST /projects/:id/ci/lint?dry_run=true&include_jobs=true&ref=<ref>` with the file's content (`glab ci lint --dry-run --include-jobs` 1.119 validates but does not print the jobs) | the job names and `when` you expect |
| a component | the components project's pipeline, which includes it from the commit | the pipeline passes |
| a chart | `helm lint --strict <chart> -f <values>` and `helm template <name> <chart> -f <values>` for every values file | `0 chart(s) failed`, and the rendered objects |
| rendered objects, schema | `kubeconform -strict -summary` on the rendered output, when installed, with local schemas when air gapped | `Invalid: 0, Errors: 0` |
| what a deploy would change | `helm diff upgrade` if the plugin is installed; else `helm upgrade --install ... --dry-run=server` | the objects that differ; the server's admission verdict |
| a manifest applied with kubectl | `kubectl apply --dry-run=server -f <file>` and `kubectl diff -f <file>` | `(server dry run)` lines; the diff |
| a Dockerfile | build it; run it as OpenShift would: `--user 1000680000:0 --read-only --tmpfs /tmp` | the process starts and answers |
| a permission | `kubectl auth can-i <verb> <resource> -n <ns> --as system:serviceaccount:<ns>:<name>` | `yes` or `no` |

`--dry-run=server` sends the objects to the API server, which runs
admission (Pod Security, quotas, SCC on OpenShift) without saving them.
It needs a kubeconfig with rights in that namespace; it changes nothing.

## What only the real thing shows

Say these under `## Not checked` when you could not run them: the pipeline
on GitLab with the project's real variables and runners; a deploy with
`--wait`; pods becoming ready; a Route answering. Name the command or the
page that would show each.

## Never

- Never write "should work" or "looks correct" as a verdict.
- Never lint a different file from the one you changed, such as the
  default branch's configuration instead of your edit.
- Never run a check against production as a way of testing.

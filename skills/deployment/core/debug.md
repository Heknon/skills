# Debug

**Verdict you produce:** the first hop on the ladder that fails, the
evidence from it, the cause, and the fix.

```
failing hop: <n. name>
evidence:    <the exact error line, and where it came from: job log, event, pod status>
cause:       <one sentence, supported by the evidence>
fix:         <the change, and the check that will show it worked>
```

## The ladder

Go down in order. At each hop, read the evidence before you guess. The
first hop whose evidence is wrong is where you work; do not skip ahead
because a later hop looks likelier.

| # | Hop | Healthy looks like | Evidence |
| --- | --- | --- | --- |
| 1 | pipeline created | a pipeline exists for the commit | the commit's Pipelines tab; CI lint (`core/verify.md`); `The resulting pipeline would have been empty` means the rules matched nothing |
| 2 | job in the pipeline | the job is listed | dry-run lint for the ref (`core/when-jobs-run.md`) |
| 3 | job picked up | status moves from `pending` to `running` | a job stuck `pending`: no runner with its `tags` is online (`gitlab/runners.md`); `waiting_for_resource`: its resource group is busy |
| 4 | job image pulled | `Using docker image ...` in the log | `failed to pull image` in the log: name, mirror, credentials |
| 5 | script ran | `Job succeeded` | the last lines before `ERROR: Job failed`; read upward to the first error |
| 6 | image built and pushed | `Writing manifest to image destination`, a digest | `gitlab/images.md`, build errors |
| 7 | chart fetched | `has been added to your repositories` | `index.yaml : 404 Not Found`: the chart project is private and does not allow this project's job token, or the id or channel is wrong (`gitlab/job-token.md`) |
| 8 | cluster reached | Helm prints `Release ... ` | `kubernetes cluster unreachable: Get "http://localhost:8080/version"`: no `KUBECONFIG` in the job (protected or scoped variable, `core/variables.md`); `Unauthorized`: token wrong or expired; `Forbidden`: the deployer lacks that right |
| 9 | objects accepted | no `Error: UPGRADE FAILED` before waiting | a schema error (`values don't meet the specifications`), `field is immutable`, a quota, a Pod Security or SCC rejection in events |
| 10 | pods scheduled | pod not `Pending` | `FailedScheduling` event: resources, node selector, quota (`kubernetes/debugging.md`) |
| 11 | containers started | pod `Running` | `ImagePullBackOff`, `CreateContainerConfigError`, `CrashLoopBackOff`, `OOMKilled` (`kubernetes/debugging.md`) |
| 12 | pods ready | `READY n/n`; `helm --wait` returns | readiness probe failures in `kubectl describe pod`; the app's logs |
| 13 | reachable | the Route or Ingress answers | `openshift/routes.md` |

## Reading the evidence

- **Job logs**: GitLab UI, or `glab ci trace <job id>`, or the job trace
  API (`gitlab/api.md`). Read from the bottom up to the first error, not
  the last.
- **Cluster**: `kubectl get events -n <ns> --sort-by=.lastTimestamp`,
  `kubectl describe pod <pod> -n <ns>` (the Events at its end), `kubectl
  logs <pod> -n <ns> --previous` for the crash before the restart.
- **Helm**: `helm status`, `helm history`; the description column holds
  the failure reason.

## Hypotheses

After the evidence, write one cause that explains every line of it. Name
what would prove it wrong, test that (seniority's hypothesis loop if it is
loaded), and change one thing at a time. A retried job that fails the same
way is not new evidence.

## Never

- Never retry a failed job, a pipeline or a deploy hoping it passes,
  unless the evidence shows a transient cause (a registry timeout, a
  runner lost), and say which.
- Never "fix" by widening access: privileged runners, `anyuid`, cluster
  roles, unprotected variables, disabled TLS checks.
- Never report "network issue" or "flaky" without the error line that
  shows it.

## Stop and ask

- The evidence is in a place you cannot read (cluster events without
  access, a runner's own logs). Say which command, run by whom, would
  show it.

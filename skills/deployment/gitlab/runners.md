# Runners

What a pipeline author needs to know about runners, and what to ask a
runner administrator for. Checked with gitlab-runner 19.4.1 (Docker
executor) in the lab.

## Which runner ran a job

The job log's first lines: `Running with gitlab-runner 19.4.1`, `on
<runner name> <token prefix>`, `Using Docker executor with image ...`,
`Running on runner-...-project-3-concurrent-0`. Read them before guessing
at the environment the job had.

## Tags

A job with `tags: [buildah]` runs only on a runner that has every listed
tag. A job without tags runs only on runners allowed to run untagged
jobs. A job that stays `pending`, and whose page says it is stuck because
no active runner has its tags, needs a runner with those tags, not a
retry.

## Executors

| Executor | Jobs run in | Notes |
| --- | --- | --- |
| Docker | a container per job, on the runner's host | `image:` and `services:` are pulled by the host's Docker |
| Kubernetes | a pod per job, in the runner's namespace | on OpenShift the pod runs under that namespace's SCC, usually `restricted-v2`: a random UID, no root, no privileged builds |
| shell | the runner host's shell, as the runner's user | `image:` is ignored; avoid for builds and deploys |

## `config.toml` settings a pipeline may need

A runner administrator sets these in the runner's `config.toml`. The lab's
runner used all of them.

| Need | Setting under `[runners.docker]` or `[[runners]]` |
| --- | --- |
| trust the internal CA in every job | `volumes = ["/etc/ssl/internal-ca.pem:/etc/internal-ca.pem:ro"]` and `environment = ["SSL_CERT_FILE=/etc/internal-ca.pem", "GIT_SSL_CAINFO=/etc/internal-ca.pem"]` under `[[runners]]` |
| Buildah pulls and pushes through the internal CA | a volume to `/etc/containers/certs.d/<registry host>/ca.crt` |
| Buildah can build | `security_opt = ["seccomp:unconfined"]` (only on a runner tagged for builds) |
| Docker-in-Docker | `privileged = true` (only on a runner tagged for it) |
| use images already on the host | `pull_policy = ["if-not-present"]` |
| reach an internal host name | `extra_hosts = ["kubernetes.example.internal:10.0.0.5"]` |
| a job network | `network_mode = "<docker network>"` |

`SSL_CERT_FILE` replaces the default trust store for tools that honour
it (Python, uv, curl): the file must hold every CA the job needs, not
only the internal one.

## Never

- Never add `privileged` or `seccomp:unconfined` to a shared runner that
  runs every project's jobs. Ask for a dedicated, tagged runner.
- Never register a runner from a pipeline or with a personal token.

# Security context constraints and the random UID

## What `restricted-v2` does

`restricted-v2` is the SCC ordinary users and service accounts get. For a
pod it:

- runs every container with a UID from the project's range (annotation
  `openshift.io/sa.scc.uid-range`, such as `1000680000/10000`), ignoring
  the image's `USER`; the process's group is 0 (`root` group, which has
  no special rights);
- assigns `fsGroup` and SELinux labels from the project;
- drops all capabilities (only `NET_BIND_SERVICE` may be added), forbids
  privilege escalation, and requires the `RuntimeDefault` seccomp profile;
- allows only these volume types: ConfigMap, Secret, emptyDir, projected,
  downward API, persistent volume claims, CSI and ephemeral volumes.

The generic chart's security context matches it: `runAsNonRoot`,
`RuntimeDefault`, no escalation, all capabilities dropped, and no
`runAsUser` or `fsGroup`.

## An image that works as a random UID

Checked in the lab by running the recipe image as OpenShift would:
`docker run --user 1000680000:0 --read-only --tmpfs /tmp`. It served
`/healthz`; `id` printed `uid=1000680000 gid=0(root) groups=0(root)`.

1. **Files the process writes are owned by group 0 and group writable**:
   `RUN chgrp -R 0 /app && chmod -R g=u /app`. In the lab, the random UID
   could write in `/app` after this line and could not write in `/`.
2. **A numeric `USER`**, such as `USER 1001`, so `runAsNonRoot` can be
   checked on plain Kubernetes. OpenShift overrides it.
3. **Listen on a port of 1024 or more** (the recipe: 8080).
4. **`HOME`**: the random UID has no entry in `/etc/passwd`, so `HOME`
   is `/`, which it cannot write. In the lab: `HOME=/`, `whoami: cannot
   find name for user ID 1000680000`, and Python creating `~/.cache`
   failed with `PermissionError: [Errno 13] Permission denied: '/.cache'`.
   Tools that write under `~` (caches of pip, Matplotlib, Hugging Face)
   fail this way. The recipe Dockerfiles set `ENV HOME=/tmp`.
5. **No `sudo`, no `chown` or `chmod` at start, no `su`**: there are no
   rights to do them at run time.
6. **Read-only root**: writes go to `/tmp` (an `emptyDir` in the chart)
   or another mounted volume.

## Errors, and what they mean

| Error | Where | Cause |
| --- | --- | --- |
| `unable to validate against any security context constraint: [... spec.containers[0].securityContext.runAsUser: Invalid value: 1001: must be in the ranges: [...]]` | ReplicaSet events | the chart sets `runAsUser`; remove it |
| the same, naming `capabilities`, `privileged`, `hostPath` or `allowPrivilegeEscalation` | ReplicaSet events | the pod asks for more than `restricted-v2`; remove the request |
| `PermissionError: [Errno 13] Permission denied: '/app/data'` | container log | the image's files are not group 0 writable (item 1) |
| `PermissionError ... '/.cache'` or `mkdir: cannot create directory '/.local'` | container log | `HOME` is `/` (item 4) |
| `bind: permission denied` on port 80 | container log | privileged port (item 3) |

The event messages above are the shapes OpenShift prints (*not run*
here); the Permission errors are what Python prints for those causes.

## `anyuid` is not the fix

Granting the `anyuid` SCC to a service account (`oc adm policy
add-scc-to-user anyuid -z <sa>`) lets pods run as the image's user,
including root. It needs a cluster administrator, weakens the project,
and hides an image problem that items 1 to 6 fix. Propose the image fix;
ask before suggesting `anyuid` at all.

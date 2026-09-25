# Security context

The fields that let a pod run under Kubernetes Pod Security `restricted`
and OpenShift `restricted-v2`. The generic chart sets exactly these; it
was admitted in a namespace labelled
`pod-security.kubernetes.io/enforce=restricted` (lab).

```yaml
spec:
  securityContext:              # pod
    runAsNonRoot: true
    seccompProfile:
      type: RuntimeDefault
  containers:
    - securityContext:          # container
        allowPrivilegeEscalation: false
        readOnlyRootFilesystem: true
        capabilities:
          drop: ["ALL"]
```

## What `restricted` checks

A pod missing any of these is refused; the message lists each (lab):
`allowPrivilegeEscalation != false`, `unrestricted capabilities (container
"y" must set securityContext.capabilities.drop=["ALL"])`, `runAsNonRoot !=
true`, `seccompProfile (pod or container "y" must set
securityContext.seccompProfile.type to "RuntimeDefault" or "Localhost")`.
It also refuses privileged containers, host namespaces, host paths, and
added capabilities other than `NET_BIND_SERVICE`.

## `runAsNonRoot` and the image's user

With `runAsNonRoot: true` and no `runAsUser`, the kubelet checks the
image's `USER`: it must be numeric and not 0. A named user (`USER app`)
cannot be checked and the container is refused. Hence `USER 1001` in the
recipe Dockerfile. OpenShift replaces the UID with one from the project's
range anyway (`openshift/scc.md`).

## Do not set, for OpenShift

- `runAsUser`, `runAsGroup`, `fsGroup`: `restricted-v2` assigns them from
  the project's ranges and refuses values outside.
- `seLinuxOptions`: assigned per project.

## A read-only root

`readOnlyRootFilesystem: true` needs every path the process writes to be
a volume. The chart mounts an `emptyDir` at `/tmp`. Python itself writes
nothing else when `PYTHONDONTWRITEBYTECODE=1`; an app that writes caches
elsewhere needs another `emptyDir` there, or the value set to `false`.

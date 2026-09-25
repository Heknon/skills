# Worked example: a deploy that fails only on OpenShift

Kind: Debug. The container behaviour was reproduced in the lab by running
the image as OpenShift does; the OpenShift-side lines are the standard
messages.

## The ask

> The deploy to staging times out. It works on my laptop and on our old
> Kubernetes cluster. Should we give the service account `anyuid`?

## Steps

1. **The job log** (`core/debug.md`, hops 5 to 12): Helm got as far as
   waiting.

   ```
   Error: UPGRADE FAILED: release web failed, and has been rolled back due to rollback-on-failure being set:
   resource Deployment/shop-staging/web not ready. status: InProgress
   ```

   Hops 1 to 9 are healthy: the objects were accepted.

2. **The pods** (`kubernetes/debugging.md`):

   ```
   oc get pods -n shop-staging -l app.kubernetes.io/instance=web
   web-6d9f8c7b5-x2k4q   0/1   CrashLoopBackOff   4
   ```

   Pods exist, so admission (the SCC) accepted them. The container starts
   and exits.

3. **The crash**: `oc logs web-6d9f8c7b5-x2k4q -n shop-staging --previous`

   ```
   PermissionError: [Errno 13] Permission denied: '/.cache'
   ```

4. **Cause, from the evidence** (`openshift/scc.md`): the pod runs as a
   random UID; `HOME` is `/`; the app writes a cache under `~`. On the
   laptop the image's own user has a home. Reproduce without the cluster:

   ```
   docker run --rm --user 1000680000:0 --entrypoint sh web:test -c 'echo HOME=$HOME; python -c "import os; os.makedirs(os.path.expanduser(\"~/.cache/x\"))"'
   HOME=/
   PermissionError: [Errno 13] Permission denied: '/.cache'
   ```

5. **Fix in the image**, not in the cluster: `ENV HOME=/tmp` (the chart
   mounts a writable `/tmp`). Rebuild, run the same command: no error.

6. **About `anyuid`**: it would let the pod run as the image's user and
   hide this, but it needs a cluster administrator and weakens the
   project. Not needed.

## The answer

```
## Result
The pods crash because OpenShift runs them as a random UID whose HOME is
/, and the app creates ~/.cache there: PermissionError: [Errno 13]
Permission denied: '/.cache'. Added ENV HOME=/tmp to the Dockerfile; the
chart already mounts a writable /tmp. anyuid is not needed.

## Checked
- Before: docker run --user 1000680000:0 reproduced the PermissionError.
- After: the same command created the cache and the server answered
  /healthz.

## Not checked
- The deploy on the cluster: the next pipeline on main; then
  oc get pods -n shop-staging -l app.kubernetes.io/instance=web shows 1/1.

## Needs a person
- none
```

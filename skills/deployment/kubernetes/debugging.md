# Debugging workloads

`kubectl` commands; `oc` accepts the same. Messages marked *lab* were
produced on a Kubernetes 1.37 API server; the others are the standard
Kubernetes wording, which a real cluster shows the same way.

## The order

1. `kubectl get deploy,rs,pods -n <ns> -l app.kubernetes.io/instance=<release>`
2. **No pods at all, Deployment `UP-TO-DATE 0`**: the ReplicaSet could
   not create them. The reason is on the ReplicaSet, not on any pod:
   `kubectl describe rs -n <ns> -l app.kubernetes.io/instance=<release>`
   or `kubectl get events -n <ns> --field-selector involvedObject.kind=ReplicaSet`.
3. **Pods exist**: `kubectl describe pod <pod> -n <ns>`; the Events at the
   end and each container's `State` and `Last State` hold the reason.
4. **The container ran**: `kubectl logs <pod> -n <ns> [-c <container>]`,
   and `--previous` for the run before the last restart.
5. **Namespace-wide**: `kubectl get events -n <ns> --sort-by=.lastTimestamp`.

## What each state means

| Seen | Where | Meaning | Look at |
| --- | --- | --- | --- |
| no pods; `FailedCreate`: `violates PodSecurity "restricted:latest": allowPrivilegeEscalation != false ...` | ReplicaSet events (*lab*) | the pod spec breaks the namespace's Pod Security level | `kubernetes/security-context.md` |
| no pods; `FailedCreate`: `exceeded quota: q, requested: requests.memory=128Mi, used: ..., limited: ...` | ReplicaSet events (*lab*) | the namespace's ResourceQuota is full or too small | `kubectl describe quota -n <ns>` |
| no pods; `unable to validate against any security context constraint` | ReplicaSet events, OpenShift | the pod asks for something `restricted-v2` refuses | `openshift/scc.md` |
| `Pending`; `FailedScheduling`: `0/1 nodes are available: 1 node(s) didn't match Pod's node affinity/selector` | pod events (*lab*) | no node fits: selector, taints, or `Insufficient cpu` / `Insufficient memory` | the pod's requests, node selectors, tolerations |
| `ErrImagePull`, then `ImagePullBackOff` | pod events | the node cannot pull: wrong name or tag, no pull secret, `unauthorized`, `not found`, or `x509` from a registry with an unknown CA | the image reference, `imagePullSecrets`, the registry |
| `CreateContainerConfigError`: `secret "web-secrets" not found` or `configmap ... not found` | pod events | a referenced Secret, ConfigMap or key does not exist | create it (a person), or fix the name |
| `CrashLoopBackOff` | pod status | the process exits, and the kubelet restarts it with growing delays | `kubectl logs --previous`; the exit code in `Last State` |
| `Last State: Terminated, Reason: OOMKilled, Exit Code: 137` | describe pod | the container went over its memory limit | raise `limits.memory`, or find the leak |
| exit code 1 and `PermissionError` or `Permission denied` on a path | logs | the process writes where its user may not; on OpenShift, the random UID | `openshift/scc.md`, the Dockerfile |
| `exec format error` | logs | image built for another CPU architecture | build for the nodes' architecture |
| `Running`, `READY 0/1`; `Readiness probe failed: HTTP probe failed with statuscode: 503` or `connection refused` | pod events | the app does not answer the probe on that port and path | the port the app listens on, the probe path, startup time |
| restarts climbing; `Liveness probe failed` | pod events | the kubelet kills the container | liveness path and thresholds; a slow start needs the startup probe |
| `Evicted` | pod status | the node ran out of memory or disk | requests close to real use |
| Helm: `resource Deployment/<ns>/<name> not ready. status: InProgress` | Helm output (*lab*) | the wait timed out; one of the above is why | this table, from the top |

## Never

- Never delete pods to "restart" a failing Deployment as a fix; they come
  back the same. Use it only to take a new Secret or ConfigMap into use
  when the chart has no checksum annotation, and say so.
- Never `kubectl exec` into a production pod to change files.
- Never scale a Deployment by hand when Helm or an HPA owns it.

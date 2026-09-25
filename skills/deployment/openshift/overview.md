# What OpenShift changes

OpenShift is Kubernetes with its own admission, routing, builds and
registry. Everything in `kubernetes/` holds; these are the differences a
deployment meets. Commands were checked against `oc` 4.22.14's help; no
OpenShift cluster ran in the lab, so cluster behaviour below is marked
*not run* where it matters.

| Kubernetes habit | On OpenShift |
| --- | --- |
| the image's `USER` is who runs | a random UID from the project's range, in group 0 (`openshift/scc.md`) |
| `runAsUser: 1000` in the chart | refused unless in the project's range; leave it out |
| port 80 in the container | unprivileged ports only: listen on 1024 or higher |
| Ingress | Route (`openshift/routes.md`); Ingress objects also work, and the cluster creates Routes from them |
| `kubectl create namespace` | `oc new-project` (needs self-provisioner rights); projects carry UID ranges |
| images from anywhere | the cluster may redirect pulls to a mirror (`ImageDigestMirrorSet`, `ImageTagMirrorSet`), set by admins |
| build images in CI | also possible in the cluster (`openshift/builds.md`) |
| DeploymentConfig | deprecated since 4.14; use Deployment |

`oc` accepts every `kubectl` command and adds `login`, `project`,
`new-project`, `whoami`, `rsh`, `debug`, `start-build`, `secrets link`,
`registry`, `adm policy`. `oc` 4.22 has no `oc kubectl` subcommand.

## First commands in an unknown cluster

```
oc whoami                       # who you are
oc whoami --show-server         # which cluster
oc version                      # client and server versions
oc project                      # current project
oc get project <p> -o jsonpath='{.metadata.annotations.openshift\.io/sa\.scc\.uid-range}'   # UID range, such as 1000680000/10000
oc get pod <pod> -o jsonpath='{.metadata.annotations.openshift\.io/scc}'                   # which SCC admitted a pod
oc adm policy who-can create routes -n <p>
```

## Files

| Topic | File |
| --- | --- |
| running as a random UID; SCC errors | `openshift/scc.md` |
| exposing a Service | `openshift/routes.md` |
| a pipeline deploying into a project; pulling images | `openshift/access.md` |
| building in the cluster | `openshift/builds.md` |
| `oc` commands | `openshift/oc.md` |

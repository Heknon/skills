# oc

`oc` 4.22.14; flags taken from its `--help`. Every `kubectl` command works
as `oc <command>`. *changes* marks commands that act on the cluster.

## Where am I

| Command | Shows |
| --- | --- |
| `oc whoami`, `oc whoami --show-server`, `oc whoami --show-console` | user, API server, web console |
| `oc version` | client and server versions |
| `oc project`, `oc projects` | current project, all you can see |
| `oc status -n <p>` | what runs in the project, with warnings |

## Look

| Command | Shows |
| --- | --- |
| `oc get pods,deploy,rs,svc,route -n <p>` | the workload |
| `oc describe pod <pod> -n <p>` | state and events |
| `oc logs <pod> -n <p> --previous` | the crash before the last restart |
| `oc get events -n <p> --sort-by=.lastTimestamp` | recent events |
| `oc rollout status deployment/<name> -n <p>` | rollout progress |
| `oc get pod <pod> -o jsonpath='{.metadata.annotations.openshift\.io/scc}'` | the SCC that admitted the pod |
| `oc adm policy who-can <verb> <resource> -n <p>` | who has a right |
| `oc explain route.spec.tls` | field documentation from the cluster itself, for its version |

`oc explain` (and `kubectl explain`) reads the schema from the cluster:
the right source for a field when air gapped.

## Debug

| Command | Does |
| --- | --- |
| `oc debug deployment/<name> -n <p>` | starts a copy of a pod with a shell instead of the command, with the same image, environment and SCC: see why it fails to start *changes* (a temporary pod) |
| `oc debug deployment/<name> --as-user=1000680000` | the copy with a given UID |
| `oc rsh <pod>` | a shell in a running pod |

## Change

| Command | Does |
| --- | --- |
| `oc login --token=<t> --server=<url>` | logs in; writes your kubeconfig |
| `oc new-project <p>` | creates a project *changes* |
| `oc apply -f <file> -n <p>` | as kubectl *changes* |
| `oc create secret docker-registry ...`, `oc secrets link <sa> <secret> --for=pull` | pull secrets (`openshift/access.md`) *changes* |
| `oc new-build --binary --strategy=docker --name=<n>`, `oc start-build <n> --from-dir=. --follow --wait` | in-cluster builds (`openshift/builds.md`) *changes* |
| `oc rollout undo deployment/<name> --to-revision=<n>` | rolls back a Deployment not managed by Helm *changes*; for Helm releases use `helm rollback` |

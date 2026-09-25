# Helm commands

Flags differ between Helm 3 and 4 (`helm/versions.md`). Commands marked
*changes* act on the cluster: invariant 1 applies.

## Look

| Question | Command |
| --- | --- |
| releases in a namespace | `helm list -n <ns>` (`-a` also shows failed and pending) |
| a release's state | `helm status <release> -n <ns>` |
| its revisions and why each failed | `helm history <release> -n <ns>` |
| the values it was deployed with | `helm get values <release> -n <ns>` (only user-supplied; `--all` adds defaults). **Prints secret values if any were passed as values**: read it yourself, never paste it |
| the objects it deployed | `helm get manifest <release> -n <ns>` |
| its notes | `helm get notes <release> -n <ns>` |
| what a chart would render | `helm template <release> <chart> -f <values> [--show-only templates/x.yaml] [--api-versions route.openshift.io/v1]` |
| a chart's default values | `helm show values <chart> [--version X]` |
| problems in a chart | `helm lint --strict <chart> -f <values>` |

## Change

| Task | Command |
| --- | --- |
| install or upgrade | `helm upgrade --install ... --wait --timeout 10m --rollback-on-failure` (`core/deploy.md`) *changes* |
| what the server would accept, without saving | `helm upgrade --install ... --dry-run=server` (runs admission, needs the namespace rights; changes nothing) |
| roll back | `helm rollback <release> <revision> -n <ns> --wait --timeout 10m` *changes* |
| remove | `helm uninstall <release> -n <ns>` *changes*; deletes the objects and, without `--keep-history`, the history. Never as a fix |

## A release stuck in `pending-install`, `pending-upgrade` or `pending-rollback`

Seen when the process running Helm was killed (a cancelled job, a runner
lost). The next upgrade fails with `another operation
(install/upgrade/rollback) is in progress` (lab, Helm 3 and 4).

1. Make sure nothing is running: no deploy job for that environment is
   still running (its resource group helps).
2. `helm history <release> -n <ns>`: find the last `deployed` revision.
3. `helm rollback <release> <that revision> -n <ns> --wait`. Accepted in
   the pending state; it creates a new revision and clears the lock (lab).
4. Run the deploy again.

For a `pending-install` of a first install there is nothing to roll back
to. The way out is `helm uninstall <release> -n <ns>`, which deletes what
the install created. Propose it and let the person decide; never run it
yourself, and in production only after the challenge in `core/deploy.md`.

## Plugins

`helm diff upgrade` (the `helm-diff` plugin) shows what an upgrade
changes. It is not part of Helm; check `helm plugin list` before using
it, and install it from an internal mirror only. Without it, compare
`helm template` output with `helm get manifest`.

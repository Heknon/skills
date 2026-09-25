# Deploy, promote, roll back

**Verdict you produce:** what was or will be deployed where, the command,
and the evidence that it is running.

```
release:   <name> in <namespace>, chart <name>-<version>, revision <n>
image:     <repository>@<digest> (commit <sha>)
command:   <the helm command, as run or to be run>
observed:  <helm status, rollout status, pods ready n/n, or "not run: <why>">
undo:      helm rollback <name> <previous revision> -n <namespace> --wait
```

## Before any deploy: challenge it

Answer each, in writing, before the command runs. For production, show the
answers to the person first.

1. **What changes?** Render it and compare: `helm diff upgrade` if the
   plugin is installed, else `helm template` with the new values against
   `helm get manifest <release> -n <ns>` (manifests hold no secret values
   unless the chart puts secrets in templates). Name every object that
   changes.
2. **What could break?** A new required Secret or ConfigMap that does not
   exist yet; a migration Job that is not backward compatible with the
   running pods; a changed selector label (Deployments reject it:
   `field is immutable`); a resource request larger than the quota.
3. **How is it undone?** The previous revision from `helm history`, and
   whether the undo is clean: a database migration is not undone by
   `helm rollback`.
4. **Is this the tested image?** The digest deployed to production is the
   digest that passed staging.

## The command

The recipes' deploy step, for Helm 4 (`helm/versions.md` for Helm 3):

```
helm upgrade --install <release> <chart> --version <chart version>
  --namespace <ns>
  --values deploy/values.yaml --values deploy/values-<env>.yaml
  --set-string image.repository=<repo> --set-string image.tag=<sha> --set-string image.digest=<digest>
  --wait --timeout 10m --rollback-on-failure --history-max 10
```

- `--wait` waits until Deployments are available and Jobs of hooks are
  done. Without it, Helm 4 marks the release `deployed` once the objects
  are accepted: in the lab a release stayed `deployed` while no pod was
  ever ready.
- `--rollback-on-failure` (Helm 3: `--atomic`) rolls back when the wait
  fails. The lab's history after a failed upgrade: revision 2 `failed`,
  revision 3 `deployed`, description `Rollback to 1`. It cannot rescue a
  release whose previous revision was never healthy: the rollback waits
  too, and fails with `an error occurred while rolling back the release`.
- `--set-string` for every image field: `--set` turns an all-digit tag
  into a number, which the schema rejects (`got number, want string`).
- The chart's Deployment uses `maxUnavailable: 0`: during a failed
  rollout the old pods keep serving.

## Promote

Production gets the same image and chart version that passed staging,
with production values. In the recipes, a release tag pipeline reuses the
commit's image, and the production job is manual. Promoting means running
that job, never a new build.

## Roll back

1. `helm history <release> -n <ns>`: find the last `deployed` or
   `superseded` revision that was healthy.
2. Challenge it like a deploy: what does going back change, is there a
   migration in between.
3. `helm rollback <release> <revision> -n <ns> --wait --timeout 10m`. A
   rollback is a new revision.
4. Observe it (below). Then fix forward in the repository; the next
   pipeline would otherwise deploy the broken version again.

## Observe

In order; stop at the first that is not healthy and go to `core/debug.md`.

1. `helm status <release> -n <ns>`: `STATUS: deployed`.
2. `kubectl rollout status deployment/<name> -n <ns> --timeout 5m`:
   `successfully rolled out`.
3. `kubectl get pods -n <ns> -l app.kubernetes.io/instance=<release>`:
   every pod `Running` and `READY n/n`, restarts not climbing.
4. `kubectl get events -n <ns> --sort-by=.lastTimestamp`: no new
   `Warning` for the release's objects.
5. The Route or Ingress answers: `curl.exe -sS -o NUL -w "%{http_code}"
   https://<host>/healthz` in PowerShell.

## Never

- Never deploy to production unasked, or from a job you started without
  the person knowing it is production.
- Never `helm uninstall` and reinstall to fix a stuck release: it deletes
  the objects and their history. A release stuck in `pending-upgrade` is
  handled in `helm/commands.md`.
- Never `kubectl edit` or `oc edit` a Helm-managed object as a fix; the
  next deploy reverts it. Change values and deploy.
- Never pass `--force-replace` (Helm 3: `--force`) without understanding it
  deletes and recreates objects.

## Stop and ask

- Production is not reachable from where you are, or the deploy needs an
  approval you cannot see. Prepare the command and the challenge; ask.
- The rollback crosses a database migration. Ask the service's owner.

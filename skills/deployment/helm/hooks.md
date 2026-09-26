# Hooks

A hook is a template with the `helm.sh/hook` annotation. Helm creates it
at a point in the release life cycle, waits for it (a Job must complete),
and does not manage it as part of the release afterwards.

## The migration hook in the generic chart

```yaml
metadata:
  annotations:
    helm.sh/hook: pre-install,pre-upgrade
    helm.sh/hook-weight: "0"
    helm.sh/hook-delete-policy: before-hook-creation,hook-succeeded
spec:
  backoffLimit: 0
  activeDeadlineSeconds: 600
```

- Runs before any other object changes, with the new image. If it fails,
  the upgrade fails and the running pods are untouched; with
  `--rollback-on-failure` Helm rolls back.
- The migration must work with the **old** pods still running, since they
  serve until the new ones are ready. Add columns before code uses them;
  drop them a release later.
- `before-hook-creation` deletes the previous run's Job before creating
  the new one (Job specs are immutable, so the name would clash).
  `hook-succeeded` deletes a successful Job; a failed one stays, so its
  logs can be read: `kubectl logs job/<release>-migrate -n <ns>`.
- `backoffLimit: 0`: a migration is not retried blindly.
- An index build on a live MongoDB collection is planned as a one-off
  job before the release, with a person's go-ahead: the mongodb skill's
  `core/index-live.md`.
- Hooks wait on `--timeout`, per hook; set it above the migration's
  longest run.
- On a first install, `pre-install` runs before any other object of the
  release exists. The chart's migration Job therefore uses the `default`
  ServiceAccount (not the one the chart creates) and does not mount the
  chart's ConfigMap; it gets `env` and `envFromSecrets`, whose Secrets
  exist before the release. *lab:* when it used the chart's own
  ServiceAccount, the first install timed out with `error looking up
  service account mig-test/full: serviceaccount "full" not found`.

## Hook points

`pre-install`, `post-install`, `pre-upgrade`, `post-upgrade`,
`pre-rollback`, `post-rollback`, `pre-delete`, `post-delete`, `test`.
Weights order hooks at one point, lowest first; they are strings.

## Never

- Never run a migration from a `post-upgrade` hook when the new pods
  need the migrated schema: they start before it.
- Never make a hook depend on an object the same release creates in
  `pre-install`: the release's own objects do not exist yet.
- Never use `helm.sh/hook-delete-policy: hook-failed` on a migration: it
  deletes the evidence.

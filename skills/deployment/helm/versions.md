# Helm 3 and Helm 4

Read `helm version` first. Checked with Helm 4.3.0 and Helm 3.22.0, by
diffing `helm upgrade --help` and running both in the lab.

## Flags that differ on `helm upgrade` and `helm install`

| Purpose | Helm 3 | Helm 4 |
| --- | --- | --- |
| roll back if the release does not become ready | `--atomic` | `--rollback-on-failure` (`--atomic` is still accepted, hidden) |
| wait for readiness | `--wait` (on or off) | `--wait` means `--wait=watcher`; also `hookOnly` (the default when the flag is absent) and `legacy`. `--rollback-on-failure` turns on `watcher` |
| replace objects that cannot be patched | `--force` | `--force-replace` |
| server-side apply | not available | `--server-side=auto` (default: keeps the release's previous method), `true`, `false`; `--force-conflicts` takes fields owned by another manager |
| coloured output | | `--color`, `--colour` |
| chart download cache | | `--content-cache` |

Both: `--install`, `--namespace`, `--values`/`-f`, `--set`,
`--set-string`, `--set-file`, `--version`, `--timeout` (default 5m0s),
`--wait-for-jobs`, `--history-max` (default 10), `--cleanup-on-fail`,
`--take-ownership`, `--reuse-values`, `--reset-then-reuse-values`,
`--dry-run=server`, `--hide-notes`.

## Behaviour the lab showed

- Without `--wait`, Helm 4 marks a release `deployed` as soon as the
  objects are accepted; a release stayed `deployed` with no pod ever
  ready. Always pass `--wait` (or `--rollback-on-failure`) in a deploy.
- A failed wait with `--rollback-on-failure` leaves: the failed revision,
  then a new revision `Rollback to <n>`. If the previous revision was
  never healthy either, the rollback fails too: `an error occurred while
  rolling back the release`.
- An upgrade killed mid-way leaves the release `pending-upgrade`; the next
  upgrade, on Helm 3 and 4 alike, fails with `another operation
  (install/upgrade/rollback) is in progress`. `helm rollback <release>
  <last deployed revision>` is accepted in that state and clears it.
- `--set image.tag=12345` makes a number, `--set image.tag=1.10` stays the
  string `1.10`, on both versions. Use `--set-string` for tags.
- Charts packaged and pushed by one version install with the other; the
  OCI digest of the same `.tgz` pushed by Helm 3 and Helm 4 was identical.

## Writing for both

In a component or template used by teams on both versions, choose by
version in the script:

```sh
if helm version --short | grep -q '^v3\.'; then rollback=--atomic; else rollback=--rollback-on-failure; fi
helm upgrade --install "$RELEASE" "$CHART" ... --wait $rollback
```

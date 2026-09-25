# Workloads

What a Deployment needs to roll out without downtime and to fail loudly.
The generic chart implements each point; its values are named in brackets.

## Probes

| Probe | Question | On failure | Chart |
| --- | --- | --- | --- |
| startup | has the process finished starting? | liveness and readiness wait; after the budget, restart | `probes.startupSeconds` |
| readiness | may it receive traffic now? | removed from the Service; not restarted | `probes.path` |
| liveness | is it stuck beyond repair? | restarted | `probes.livenessPath`, default `probes.path` |

- Readiness answers from inside the process only; checking a database
  there takes every pod out when the database blinks.
- Liveness is loose (the chart: 6 failures, 10 s apart); a tight liveness
  probe turns slowness into a restart loop.
- `helm --wait` and `kubectl rollout status` wait on readiness: without a
  readiness probe, "ready" means only "started".

## Resources

- `requests` are what the scheduler reserves and what quotas count; set
  them near real use.
- `limits.memory` stops a leak from taking the node; going over it is
  `OOMKilled`. Leave `limits.cpu` out unless the namespace requires it:
  CPU limits throttle, they do not protect.
- A namespace with a ResourceQuota refuses pods without requests.

## Rollout

- `maxUnavailable: 0`, `maxSurge: 25%`: new pods start and become ready
  before old ones stop. In the lab, an upgrade whose pods could never be
  scheduled left the old pod serving while Helm timed out and rolled back.
- `revisionHistoryLimit` keeps old ReplicaSets for `kubectl rollout undo`;
  with Helm, roll back with `helm rollback` instead, so Helm's record
  stays true.
- `terminationGracePeriodSeconds` (chart: 30) must exceed the longest
  request; the process must exit on SIGTERM after finishing in-flight work.
  A Python server started through a shell (`sh -c "python ..."`) does not
  receive SIGTERM: use the exec form `CMD ["python", "-m", "web"]`.

## Availability

- Two or more replicas in production, spread across nodes
  (`topologySpreadConstraints` on the hostname, `ScheduleAnyway`).
- A PodDisruptionBudget (`maxUnavailable: 1`) so node drains take one pod
  at a time; with one replica it would block drains, so the chart creates
  it only with more than one.
- A HorizontalPodAutoscaler owns the replica count when enabled; the chart
  then leaves `replicas` out of the Deployment, so an upgrade does not
  reset it.

## Jobs and CronJobs

- `restartPolicy: Never` and a small `backoffLimit`; `activeDeadlineSeconds`
  so a stuck run ends.
- CronJobs: `concurrencyPolicy: Forbid` unless overlapping runs are safe;
  the schedule is in the controller manager's time zone (usually UTC)
  unless `timeZone` is set.

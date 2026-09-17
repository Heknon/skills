# Concurrency and clocks

**Verdict you produce:** the **lane**, the attribute set that names one
emitting process on one host, the resource attributes each worker sets, the
one process per host that emits host metrics, and the rule for which
timestamps may be compared. It goes into `vocabulary.md` under *Lanes and
time*.

Parallel workers on one host share a clock and nothing else. Workers on many
hosts share nothing, and their clocks disagree by whatever NTP left over.
Every duration the SDK writes comes from `time_ns()` at start and at end, a
wall clock, on the process that owns the span. Compare inside a lane and the
numbers are exact. Compare across lanes and the numbers are NTP plus wishes.

## Questions

1. **How many processes emit at once on one host?** Count the workers. Each
   process has its own `TracerProvider`, its own `Resource`, and its own
   `process.pid`. Two workers with identical resource attributes and no worker
   key are indistinguishable in every screen.
2. **How many hosts emit into one cycle?** More than one: `host.name` differs
   and the clocks differ. Every rule below about clocks applies.
3. **Which numbers describe the host, and which describe the worker?** CPU,
   memory, disk, network describe the host. Tests running, entities alive,
   queue depth describe the worker. A host number emitted by every worker is
   counted once per worker by the backend, and a sum over workers is `N`
   times the truth.
4. **Is any span opened in one process and ended in another?** Read the code
   for a `start_span` whose `end()` is in a different process. That is not
   possible with a `Span` object and it is not done by copying ids either.
5. **Does any chart or query subtract timestamps from two lanes?** A
   controller start against a worker end, a host A parent against a host B
   child. Those differences are clock skew plus the true value.

## Rules

**Lane.** A lane is `host.name` plus `process.pid`, set once as resource
attributes. The logical name of the worker, `PYTEST_XDIST_WORKER` such as
`gw2`, goes on every span as the span attribute the vocabulary names, such as
`sahara.worker.id`, because a pid is not stable across runs and a person
filters by the name. `sahara.worker.id` is bounded by the worker count, so it
may be a metric label; see `metrics/labels.md`.

**Host metrics.** One emitter per host. Either the collector's `hostmetrics`
receiver on that host, or one designated process. Never each worker. If each
worker must report, report the worker's own use, such as its RSS, under a
metric whose name says so, with `sahara.worker.id` as a label.

**Durations.** A span's duration is `end_time - start_time` on the process
that owns it. It is correct as long as that host's clock did not step during
the span. A negative or absurd duration means the clock stepped. Check the
host with `timedatectl` or `chronyc tracking` before blaming the code.

**Starts.** A start time is a wall clock reading and is comparable to another
start time only inside the same lane. The backend's waterfall orders spans by
timestamp. A child drawn before its parent, or a gap that is exactly the
clock offset, is the observable symptom of skew across lanes. Fix the clock.
Do not adjust the timestamps in code.

**A span across two processes.** Do not. The near process ends its span at
the hand off. The far process starts its own span, with `links=[Link(...)]`
to the near span's context and the same correlation keys. The far span is
a root of its own trace when the far process is its own unit, or a child via
`context=` when it is not; see `core/context-propagation.md`. A person who
wants "the total time" gets it from the correlation key: latest end minus
earliest start across the joined spans, computed by a query, and read with
the skew caveat.

**Ordering.** Inside one trace on one lane, order by start time. Across lanes
inside one trace, order by structure: parent before child, link source before
link target. Do not order by timestamp across lanes.

## Verdict

Write into `vocabulary.md` under *Lanes and time*:

```
lane: host.name + process.pid, resource attributes
worker key: <span attribute key, e.g. sahara.worker.id> = <value rule, e.g. PYTEST_XDIST_WORKER>
host metrics emitted by: <collector hostmetrics receiver on each host | the process named here>
clock source: <ntp or chrony, and the command that shows it>
compare timestamps: within one lane only; across lanes by structure
cross process spans: none; hand offs are two spans joined by a Link and <key>
```

## Never

- Never sum a host metric over workers. Group by `host.name` and take one.
- Never let two workers share `process.pid` in the resource by copying a
  parent's resource into a forked child. Build the `Resource` after the fork.
- Never subtract a timestamp on host A from one on host B and call it a
  duration.
- Never pass `start_time=` or `end_time=` taken from another process into
  `start_span` or `end()`.
- Never put `process.pid` or `host.name` in a span name or a metric label
  that is meant to be compared across runs. `sahara.worker.id` is the stable
  one.
- Never adjust timestamps in code to hide skew.

## Stop and ask

- The hosts have no NTP and cannot get it. Every cross host chart is then a
  guess, and a person decides which ones to keep.
- More than one process on a host wants to be the host metrics emitter.
- A required chart is a duration across two lanes, such as "time from the
  orchestrator's dispatch to the worker's first test". A person accepts the
  skew or funds a clock.

## Examples

| Situation | Rule | What to write |
| --- | --- | --- |
| Four xdist workers on one host | lane per worker, one host emitter | `sahara.worker.id=gw0..gw3` on every span; `hostmetrics` receiver once |
| Workers on eight hosts in one cycle | compare within a lane | cycle duration by query on `sahara.cycle.id`, read with skew caveat |
| Each worker emits `system.memory.usage` | host metric per worker, forbidden | move to the collector; keep `sahara.worker.rss` per worker if needed |
| Test span shows `-3ms` duration | clock stepped | `chronyc tracking` on that host; no code change |
| Orchestrator opens the cycle span, worker should close it | cross process span, forbidden | orchestrator span `cycle.dispatch`; each session root links to it; `sahara.cycle.id` on both |
| Child span starts 2s before its parent in the waterfall | skew across lanes | check the two hosts' offsets; order by structure |

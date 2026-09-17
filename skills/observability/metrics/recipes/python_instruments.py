"""One instrument of each kind, with labels checked against the vocabulary.

Written against opentelemetry-python 1.2x, public module opentelemetry.metrics.
Requires configure_metrics() from python_meter_setup.py to have run first;
before that, every call below goes to a no-op meter and is silently lost.

Rename before use:
  - LABEL_VALUES: copy the allowed values of every label tier key from the
    Span attributes table of vocabulary.md. Nothing else may be a key here.
  - The four metric names and units: exact strings from the Metrics table.
  - queue_depth_by_worker: replace the body with a read of your scheduler.
Delete the instruments you do not have a vocabulary row for. Never add a
label key here without adding it to vocabulary.md first.
"""

from __future__ import annotations

from typing import Callable, Iterable, Mapping

from opentelemetry.metrics import CallbackOptions, Observation, get_meter

from python_meter_setup import METER_NAME

# Label tier only. Every value a label may take, spelled exactly.
LABEL_VALUES: Mapping[str, frozenset[str]] = {
    "entity.definition": frozenset({"tank", "pump", "valve", "sensor"}),
    "entity.operation": frozenset({"create", "tag", "revert", "destroy", "call"}),
    "outcome": frozenset({"success", "failure"}),
    "worker.id": frozenset({"gw0", "gw1", "gw2", "gw3", "gw4", "gw5", "gw6", "gw7"}),
}


def label_set(**labels: str) -> dict[str, str]:
    """Return the labels as a dict, or raise. A bad label never reaches the SDK.

    Values are strings, always: Elastic stores a numeric attribute in a
    different field, numeric_labels.<key>, than a string one, labels.<key>.
    """
    checked: dict[str, str] = {}
    for key, value in labels.items():
        dotted_key = key.replace("__", ".")
        allowed = LABEL_VALUES.get(dotted_key)
        if allowed is None:
            raise ValueError(f"{dotted_key!r} is not a metric label in the vocabulary")
        if not isinstance(value, str):
            raise TypeError(f"label {dotted_key!r} must be a str, got {type(value).__name__}")
        if value not in allowed:
            raise ValueError(f"{value!r} is not an allowed value of {dotted_key!r}")
        checked[dotted_key] = value
    return checked


meter = get_meter(METER_NAME)

# counter: only goes up. Polls are too frequent to be spans.
controller_polls = meter.create_counter(
    "sahara.controller.polls",
    unit="{poll}",
    description="Controller status polls sent",
)

# updowncounter: a level whose sum across definitions is meaningful.
entities_live = meter.create_up_down_counter(
    "sahara.entities.live",
    unit="{entity}",
    description="Entities currently existing, per definition",
)

# histogram: a distribution with no span around each measurement.
# Boundaries come from the View in python_meter_setup.py, not from here.
controller_poll_duration = meter.create_histogram(
    "sahara.controller.poll.duration",
    unit="s",
    description="Poll round trip time in seconds",
)


# observable gauge: a level read on demand. The SDK calls the callback once
# per export interval, from the exporter's thread. Keep it fast and never let
# it raise; return nothing instead.
QueueDepthReader = Callable[[], Mapping[str, int]]


def queue_depth_by_worker() -> Mapping[str, int]:
    """Replace with a read of the scheduler. Keys are worker ids, values counts."""
    return {"gw0": 12, "gw1": 7}


def make_queue_depth_callback(
    reader: QueueDepthReader,
) -> Callable[[CallbackOptions], Iterable[Observation]]:
    def observe_queue_depth(options: CallbackOptions) -> Iterable[Observation]:
        try:
            depths = reader()
        except Exception:  # noqa: BLE001  a callback that raises stops the export
            return []
        observations: list[Observation] = []
        for worker_id, depth in depths.items():
            if worker_id not in LABEL_VALUES["worker.id"]:
                continue
            observations.append(Observation(depth, label_set(worker__id=worker_id)))
        return observations

    return observe_queue_depth


worker_queue_depth = meter.create_observable_gauge(
    "sahara.worker.queue.depth",
    callbacks=[make_queue_depth_callback(queue_depth_by_worker)],
    unit="{test}",
    description="Tests still queued on the worker",
)


# Call sites. Only these four shapes exist; label_set is the only way in.

def record_poll(definition: str, operation: str, succeeded: bool, elapsed_seconds: float) -> None:
    labels = label_set(
        entity__definition=definition,
        entity__operation=operation,
        outcome="success" if succeeded else "failure",
    )
    controller_polls.add(1, labels)
    controller_poll_duration.record(elapsed_seconds, label_set(entity__definition=definition))


def record_entity_created(definition: str) -> None:
    entities_live.add(1, label_set(entity__definition=definition))


def record_entity_destroyed(definition: str) -> None:
    entities_live.add(-1, label_set(entity__definition=definition))


if __name__ == "__main__":
    import time

    from python_meter_setup import configure_metrics

    provider = configure_metrics(console=True, export_interval_millis=1000)
    record_entity_created("tank")
    record_poll("tank", "create", True, 0.042)
    record_poll("tank", "create", True, 0.061)
    record_entity_destroyed("tank")
    time.sleep(1.5)
    provider.shutdown()


# OTLP data point each instrument produces, as MetricsData.to_json() prints it.
# Only the "data" object differs; resource and scope are as in
# python_meter_setup.py. Temporality 1 is DELTA, 2 is CUMULATIVE.
#
# sahara.controller.polls, counter:
#   "data": {"data_points": [{"attributes": {"entity.definition": "tank",
#             "entity.operation": "create", "outcome": "success"},
#             "start_time_unix_nano": ..., "time_unix_nano": ..., "value": 2}],
#            "aggregation_temporality": 1, "is_monotonic": true}
#   Elastic: field "sahara.controller.polls": 2.0   (increments in this interval)
#
# sahara.entities.live, updowncounter:
#   "data": {"data_points": [{"attributes": {"entity.definition": "tank"},
#             "start_time_unix_nano": ..., "time_unix_nano": ..., "value": 0}],
#            "aggregation_temporality": 2, "is_monotonic": false}
#   Elastic: field "sahara.entities.live": 0.0      (current level)
#
# sahara.controller.poll.duration, histogram:
#   "data": {"data_points": [{"attributes": {"entity.definition": "tank"},
#             "count": 2, "sum": 0.103, "min": 0.042, "max": 0.061,
#             "bucket_counts": [0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0],
#             "explicit_bounds": [0.005,0.01,0.025,0.05,0.1,0.25,0.5,1.0,2.5,5.0,10.0,30.0,60.0,120.0,300.0,600.0]}],
#            "aggregation_temporality": 1}
#   Elastic: field "sahara.controller.poll.duration": {"values": [0.0375, 0.075], "counts": [1, 1]}
#
# sahara.worker.queue.depth, observable gauge:
#   "data": {"data_points": [{"attributes": {"worker.id": "gw0"}, "time_unix_nano": ..., "value": 12},
#                            {"attributes": {"worker.id": "gw1"}, "time_unix_nano": ..., "value": 7}]}
#   Elastic: two documents, one per label set, field "sahara.worker.queue.depth": 12.0 and 7.0
#
# Label spelling in the Elastic document is UNVERIFIED between
# labels.entity.definition and labels.entity_definition; see metrics/labels.md.

# events

The queue worker calls `events.consumer.dispatch` for every message. The
message's `kind` picks the handler.

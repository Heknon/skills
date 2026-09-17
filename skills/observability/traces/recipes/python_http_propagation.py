"""Carry the trace context over HTTP and into a subprocess, opentelemetry-python 1.2x.

Written against the documented API of opentelemetry-api 1.2x and
opentelemetry-instrumentation-requests. Verified names:
opentelemetry.propagate.inject(carrier, context=None, setter=DefaultSetter),
opentelemetry.propagate.extract(carrier, context=None, getter=DefaultGetter),
opentelemetry.context.attach(context) -> token, detach(token),
RequestsInstrumentor().instrument(tracer_provider=None, request_hook=None,
response_hook=None). Default propagators: tracecontext,baggage, header names
`traceparent` and `tracestate`, W3C format
00-<32 hex trace id>-<16 hex span id>-<2 hex flags>.

Rename before use:
- TRACEPARENT_VARIABLE and TRACESTATE_VARIABLE if the project already has
  names for them. Both sides must use the same names.

Three parts:
1. Client side. Prefer RequestsInstrumentor: it injects headers and opens a
   CLIENT span per request by itself. Fall back to inject_headers when the
   package is missing or the HTTP client is not requests.
2. Server side. server_context extracts the incoming headers; the SERVER span
   is opened inside it so its parent is the caller's span.
3. Subprocess. The parent writes the traceparent string into an environment
   variable; the child reads it and attaches it before opening any span. The
   child must run configure_tracing first, it is a new process.

configure_tracing from python_otel_setup.py must have run in every process
that uses this file, or the propagator sees an invalid context and injects
nothing.
"""

from __future__ import annotations

import os
import subprocess
import sys
from contextlib import contextmanager
from typing import Iterator, Mapping, MutableMapping, Optional, Sequence

from opentelemetry import context as context_api
from opentelemetry import trace
from opentelemetry.propagate import extract, inject
from opentelemetry.trace import SpanKind

TRACEPARENT_HEADER = "traceparent"
TRACESTATE_HEADER = "tracestate"
TRACEPARENT_VARIABLE = "TRACEPARENT"
TRACESTATE_VARIABLE = "TRACESTATE"


# 1. Client side --------------------------------------------------------------

def instrument_requests_if_available() -> bool:
    """Turn on automatic header injection and CLIENT spans for requests."""
    try:
        from opentelemetry.instrumentation.requests import RequestsInstrumentor
    except ImportError:
        return False
    RequestsInstrumentor().instrument()
    return True


def inject_headers(headers: Optional[MutableMapping[str, str]] = None) -> MutableMapping[str, str]:
    """Manual fallback: add traceparent and tracestate to an HTTP header dict.

    Call it inside the CLIENT span for the request, so the injected parent is
    that span and not the span around it.
    """
    carrier: MutableMapping[str, str] = headers if headers is not None else {}
    inject(carrier)
    return carrier


# 2. Server side --------------------------------------------------------------

def _lower_keys(headers: Mapping[str, str]) -> dict[str, str]:
    return {key.lower(): value for key, value in headers.items()}


@contextmanager
def server_context(headers: Mapping[str, str]) -> Iterator[None]:
    """Attach the caller's context for the duration of handling one request."""
    incoming = extract(_lower_keys(headers))
    token = context_api.attach(incoming)
    try:
        yield
    finally:
        context_api.detach(token)


def handle_request(tracer: trace.Tracer, route_template: str, headers: Mapping[str, str]) -> None:
    """Example handler: the SERVER span's parent is the caller's CLIENT span."""
    with server_context(headers):
        with tracer.start_as_current_span(route_template, kind=SpanKind.SERVER):
            pass


# 3. Subprocess ---------------------------------------------------------------

def environment_with_trace_context(base: Optional[Mapping[str, str]] = None) -> dict[str, str]:
    """A copy of the environment carrying the current span as traceparent."""
    carrier: dict[str, str] = {}
    inject(carrier)
    environment = dict(os.environ if base is None else base)
    if TRACEPARENT_HEADER in carrier:
        environment[TRACEPARENT_VARIABLE] = carrier[TRACEPARENT_HEADER]
    if TRACESTATE_HEADER in carrier:
        environment[TRACESTATE_VARIABLE] = carrier[TRACESTATE_HEADER]
    return environment


def run_child(tracer: trace.Tracer, command: Sequence[str]) -> subprocess.CompletedProcess:
    """Run a command whose spans become children of the span opened here."""
    with tracer.start_as_current_span("process.run", attributes={"process.command": command[0]}):
        return subprocess.run(list(command), env=environment_with_trace_context(), check=False)


@contextmanager
def attach_inherited_context() -> Iterator[bool]:
    """In the child: attach the parent's context read from the environment.

    Yields True when a traceparent was found. Every span opened inside the
    block has the parent's span as its parent.
    """
    traceparent = os.environ.get(TRACEPARENT_VARIABLE)
    if not traceparent:
        yield False
        return
    carrier = {TRACEPARENT_HEADER: traceparent}
    tracestate = os.environ.get(TRACESTATE_VARIABLE)
    if tracestate:
        carrier[TRACESTATE_HEADER] = tracestate
    token = context_api.attach(extract(carrier))
    try:
        yield True
    finally:
        context_api.detach(token)


def child_main() -> None:
    """What the child process runs after its own configure_tracing."""
    tracer = trace.get_tracer("example.child")
    with attach_inherited_context():
        with tracer.start_as_current_span("child.work"):
            pass


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "child":
        child_main()
    else:
        tracer = trace.get_tracer("example.parent")
        instrument_requests_if_available()
        with tracer.start_as_current_span("example.parent"):
            print(inject_headers({}))
            handle_request(tracer, "GET /health", inject_headers({}))
            run_child(tracer, [sys.executable, __file__, "child"])

# Shape of data this recipe produces:
#
# inject_headers({})  -> {"traceparent": "00-<32 hex>-<16 hex>-01"}
#                        plus "tracestate" only when one is set.
#                        Flags 01 means sampled; 00 means the child is not
#                        recorded either, by ParentBased.
# environment_with_trace_context() -> os.environ plus
#                        TRACEPARENT="00-<32 hex>-<16 hex>-01"
#
# Spans, when both processes exported to the same backend:
#   example.parent   INTERNAL, root
#     GET /health    SERVER, parent example.parent, same trace_id
#     process.run    INTERNAL, parent example.parent
#       child.work   INTERNAL, parent process.run, same trace_id,
#                    resource of the child process, remote parent
#
# The backend's waterfall shows both processes in one trace when their clocks
# agree, see core/concurrency-and-clocks.md. What a SERVER span or a root
# becomes on each backend is in backends/paradigms.md; on Elastic 8.x both
# become transactions.

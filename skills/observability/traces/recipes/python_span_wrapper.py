"""Span helpers that make the invariants hard to break, opentelemetry-python 1.2x.

Written against the documented API of opentelemetry-api 1.2x. Verified
names: Tracer.start_as_current_span(name, kind=, attributes=, links=,
record_exception=, set_status_on_exception=), Span.record_exception,
Span.set_status, Status, StatusCode, SpanKind, trace.Link.

Rename before use:
- nothing. Span names and attribute keys come from vocabulary.md at the call
  site. This file holds no names of its own except the link attribute key
  LINK_RELATION_KEY, which traces/parent-or-link.md defines.

What each helper guarantees:
- operation: on an exception, status ERROR with "<Type>: <message>" as the
  description, the exception recorded as the `exception` event, and the
  exception re-raised. On success the status stays UNSET, which Elastic reads
  as success.
- exit_span: SpanKind.CLIENT plus peer.service, so Elastic draws a dependency.
- link_to: a Link carrying link.relation, for the links= argument at start.
"""

from __future__ import annotations

import functools
from contextlib import contextmanager
from typing import Callable, Iterator, Mapping, Optional, Sequence, TypeVar

from opentelemetry import trace
from opentelemetry.trace import Link, Span, SpanKind, Status, StatusCode, Tracer
from opentelemetry.util.types import Attributes

LINK_RELATION_KEY = "link.relation"
LINK_RELATIONS = ("belongs_to", "operates_on", "produced_by", "retries")
PEER_SERVICE_KEY = "peer.service"

ReturnType = TypeVar("ReturnType")


def _fail(span: Span, exception: BaseException) -> None:
    span.record_exception(exception)
    span.set_status(
        Status(StatusCode.ERROR, f"{type(exception).__name__}: {exception}")
    )


@contextmanager
def operation(
    tracer: Tracer,
    name: str,
    kind: SpanKind = SpanKind.INTERNAL,
    attributes: Attributes = None,
    links: Optional[Sequence[Link]] = None,
) -> Iterator[Span]:
    """One span around one thing that starts, ends, and can fail."""
    with tracer.start_as_current_span(
        name,
        kind=kind,
        attributes=attributes,
        links=links,
        # Done by hand below so the status description is always set.
        record_exception=False,
        set_status_on_exception=False,
    ) as span:
        try:
            yield span
        except BaseException as exception:
            _fail(span, exception)
            raise


def traced(
    tracer: Tracer,
    name: str,
    kind: SpanKind = SpanKind.INTERNAL,
    attributes: Attributes = None,
) -> Callable[[Callable[..., ReturnType]], Callable[..., ReturnType]]:
    """Decorator form of operation. The name is fixed at decoration time."""

    def decorate(function: Callable[..., ReturnType]) -> Callable[..., ReturnType]:
        @functools.wraps(function)
        def wrapper(*arguments, **keyword_arguments) -> ReturnType:
            with operation(tracer, name, kind=kind, attributes=attributes):
                return function(*arguments, **keyword_arguments)

        return wrapper

    return decorate


@contextmanager
def exit_span(
    tracer: Tracer,
    name: str,
    peer_service: str,
    attributes: Attributes = None,
    links: Optional[Sequence[Link]] = None,
) -> Iterator[Span]:
    """A call out of this service. peer_service names what was called.

    peer_service must come from the label tier: bounded, known in advance.
    Elastic keys the Dependencies screen and the service map by it.
    """
    merged: dict = {PEER_SERVICE_KEY: peer_service}
    if attributes:
        merged.update(attributes)
    with operation(
        tracer, name, kind=SpanKind.CLIENT, attributes=merged, links=links
    ) as span:
        yield span


def link_to(span: Span, relation: str, attributes: Attributes = None) -> Optional[Link]:
    """A Link to span, or None when span has no valid context.

    Pass the result in links=[...] at start. Filter out None first.
    """
    if relation not in LINK_RELATIONS:
        raise ValueError(f"unknown link relation {relation!r}; one of {LINK_RELATIONS}")
    span_context = span.get_span_context()
    if not span_context.is_valid:
        return None
    link_attributes: dict = {LINK_RELATION_KEY: relation}
    if attributes:
        link_attributes.update(attributes)
    return Link(span_context, link_attributes)


def links_from(*candidates: Optional[Link]) -> list[Link]:
    """Drop the None results of link_to so links= gets a clean list."""
    return [candidate for candidate in candidates if candidate is not None]


if __name__ == "__main__":
    tracer = trace.get_tracer("example.instrumentation")

    with operation(tracer, "session.run") as session_span:
        session_link = link_to(session_span, "belongs_to")

    with operation(tracer, "tests/a.py::test_x", links=links_from(session_link)) as test_span:
        test_span.set_attribute("test.nodeid_hash", "0" * 64)
        with exit_span(
            tracer, "entity.create", peer_service="tank", attributes={"entity.id": "tank-7"}
        ) as create_span:
            create_link = link_to(create_span, "operates_on")
        try:
            with exit_span(tracer, "entity.revert", peer_service="tank", links=links_from(create_link)):
                raise RuntimeError("controller refused")
        except RuntimeError:
            pass

# Shape of data this recipe produces, one span per with block:
#
# session.run          kind INTERNAL, root, status UNSET
# tests/a.py::test_x   kind INTERNAL, root, status UNSET,
#                      links [{trace_id, span_id of session.run,
#                              attributes {"link.relation": "belongs_to"}}]
# entity.create        kind CLIENT, parent test span,
#                      attributes {"peer.service": "tank", "entity.id": "tank-7"}
# entity.revert        kind CLIENT, parent test span, status ERROR,
#                      status description "RuntimeError: controller refused",
#                      events [{"name": "exception", attributes
#                        {"exception.type": "RuntimeError",
#                         "exception.message": "controller refused",
#                         "exception.stacktrace": "...", "exception.escaped": "False"}}],
#                      links [{... of entity.create, {"link.relation": "operates_on"}}]
#
# In Elastic 8.x: peer.service becomes span.destination.service.resource and
# service.target.name; entity.id becomes labels.entity_id; the link
# attributes are dropped and the link ids land in span.links.

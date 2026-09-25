# Worked example: Trace in, when search says nothing calls it

Follow this for "is X used" or "can I delete X". Copy the order of the
steps and the answer shape; change the names.

## The ask

> Nothing calls `handle_refund` in `events/handlers.py`. Can I delete it?

## Steps

1. **Locate it** (`core/locate.md`):

   ```
   events/handlers.py:21: def handle_refund(event):
   ```

2. **Search for calls** (`core/search-patterns.md`, uses): `\bhandle_refund\s*\(`
   in `**/*.py`. One hit, the definition itself. This is where a weak
   answer stops and says "unused".

3. **Go through `core/what-search-misses.md`.** Item 1, decorators: read
   the line above the definition.

   ```
   events/handlers.py:20: @handler("refund")
   ```

4. **Read the decorator** (`python/dynamic.md`, registration):

   ```
   events/registry.py:4: HANDLERS = {}
   events/registry.py:7: def handler(kind):
   events/registry.py:9:         HANDLERS[kind] = fn
   ```

   It stores the function in `HANDLERS` under the key `"refund"`.

5. **Find reads of the table**: `HANDLERS\[` and `HANDLERS\.get\(`.

   ```
   events/dispatch.py:15:     return HANDLERS[event["kind"]](event)
   ```

6. **Find where the key comes from.** `event["kind"]` comes from outside
   data, the message, so any producer can send `"refund"`; the handler is
   live even if no line in this repository sends it (`core/trace-in.md`
   step 6). Search for the string `"refund"` in `.py` and configuration:

   ```
   events/consumer.py:30:     kind = message.headers["kind"]   # "refund" for refund messages
   billing/refunds.py:44:     publish({"kind": "refund", ...})
   ```

7. **The rest of the list.** Items 2 to 11 checked: no other string
   references, no subclasses, no entry points. Other repositories may
   publish `"refund"` events too: without Sourcegraph that is not
   searched.

## The answer

```
## Found
events/handlers.py:20-21 - handle_refund, registered with @handler("refund")
events/registry.py:9 - the decorator stores it in HANDLERS["refund"]
events/dispatch.py:15 - called as HANDLERS[event["kind"]](event)
billing/refunds.py:44 - publishes events with kind "refund", which reach it

## How I know
A search for calls, \bhandle_refund\s*\(, finds only the definition. The
decorator on events/handlers.py:20 registers it; events/registry.py:7-9
shows the table; a search for HANDLERS\[ finds the dispatch at
events/dispatch.py:15; a search for "refund" finds the producer.

Not safe to delete: every refund event is handled by it.

## Not covered
Other repositories that may publish events with kind "refund": not
searched, no cross-repository search available.
```

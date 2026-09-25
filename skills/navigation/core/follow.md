# Follow

**Verdict you produce:** the chain a value or a request travels, from A to
B, one hop per line, each with `path:line`.

```
1. <where it enters: route, CLI argument, message, file> <path:line>
2. <the next function it is passed to or stored in> <path:line>
...
n. <where it ends: stored, returned, sent, raised> <path:line>
```

## Steps

1. **Find the start.** A request: the route (`python/entry-points.md`,
   routes). A command: the CLI definition. A message: the consumer. A
   value: where it is first assigned or read.
2. **At each hop, ask one question: where does it go next?** It is passed
   as an argument (follow the parameter into the callee), returned (follow
   to the caller), stored on an object or in a module-level name (search
   for where that attribute or name is read), or put in a queue, a file,
   a table (find the reader of that queue, file or table).
3. **Keep the name changes.** A value called `order_id` in the route may
   be `oid` two calls later and `key` in the cache. Write each name in the
   hop line.
4. **Stop at the end asked for**, or at the first place that leaves the
   process. Name what is on the other side if it is in this repository.
5. **Branches:** when a hop can go two ways (an `if`, a dispatch), follow
   each and label it, or ask which case matters.

## Never

- Never skip a hop because "it obviously just passes it through". Most
  bugs are in the hop someone skipped.

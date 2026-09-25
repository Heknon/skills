# Trace out

**Verdict you produce:** what `X` calls, reads and writes, each as
`path:line` of the target, in the order it happens.

```
X (<path:line>) does:
1. calls <name> -> <path:line of its definition>
2. reads <file, env var, setting, table> at <path:line>
3. writes <file, table, queue, network> at <path:line>
```

## Steps

1. **Read `X` whole.** It is the one place where reading beats searching.
2. **List every call, in order.** For each, resolve the name to its
   definition (`core/locate.md`), starting from `X`'s file imports. A call
   on an object, `self.repo.save(order)`, needs the object's type: find
   where `self.repo` is set, or ask a type checker (`python/types.md`).
3. **List what it reads**: parameters, module-level names, settings
   (`settings.X`, `os.environ["X"]`, `os.getenv("X")`), files opened for
   reading, database queries.
4. **List what it writes**: files, database writes, messages sent, network
   calls, logs if they matter, and mutations of arguments.
5. **Stop at the edge.** Go one level deep unless asked for more. For a
   call into an installed library, name the library and function, not its
   insides.

## Never

- Never guess what a method does from its name. `save` may queue, cache,
  or do nothing in a test double. Open its definition.

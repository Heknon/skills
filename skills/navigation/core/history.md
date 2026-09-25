# History

**Verdict you produce:** when a piece of code changed, who changed it,
and why, from the commits; or `not recorded`.

```
<path:line range> last changed in <commit> by <author> on <date>: "<message>"
introduced in <commit> ... (if asked)
why: <the reason as written in the commit, pull request or issue it names>, or not recorded
```

## Steps

1. **Check that there is history.** In the terminal: `git rev-parse
   --is-inside-work-tree`. No repository, or a shallow clone without the
   commits you need: say so; with Sourcegraph, its `commit_search` and
   `diff_search` may still have them.
2. **Who last changed these lines:** `git blame -L <start>,<end> -- <path>`.
3. **When a line or text first appeared:** `git log -S "<exact text>"
   --oneline -- <path>`. For a pattern, `-G "<regex>"`.
4. **The whole story of a function:** `git log -L :<function>:<path>`, or
   `git log -L <start>,<end>:<path>`.
5. **Across renames:** `git log --follow --oneline -- <path>`.
6. **Read the commit:** `git show --stat <commit>`, then `git show <commit>
   -- <path>`.
7. **Why:** only from the commit message, and from a pull request or issue
   it names. If it names none and says nothing, the reason is `not
   recorded`. Commands and flags are in `tools/git.md`.

## Never

- Never write a reason the history does not contain. Guessing why a
  choice was made is the most tempting invention in this skill.

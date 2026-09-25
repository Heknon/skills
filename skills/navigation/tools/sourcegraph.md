# Sourcegraph

**What it decides:** when and how to use Sourcegraph's tools, if they are
connected. They appear among your tools with the names below. If they are
not there, this file does not apply.

Sourcegraph searches every repository it indexes, not only the one open
in the editor, and its navigation tools give definitions and references
that plain search cannot. They are the best tools for Locate and Trace in,
and the only ones for questions that cross repositories.

## The tools

| Tool | Parameters | Use it for |
| --- | --- | --- |
| `go_to_definition` | `repo`, `path`, `symbol`, optional `revision` | Locate: the definition of `symbol` as used in the file `path` |
| `find_references` | `repo`, `path`, `symbol`, optional `revision`, `limit` (default 10) | Trace in: every use, across repositories. Set `limit` higher, such as 200 |
| `keyword_search` | `query` | exact text or regex search, with filters `repo:`, `file:`, `rev:`, `count:` |
| `nls_search` | `query` | search in plain words when you do not know the exact name |
| `read_file` | `repo`, `path`, optional `startLine`, `endLine`, `revision` | read a file in any indexed repository |
| `list_files` | `repo`, optional `path`, `revision` | a folder's contents |
| `list_repos` | `query`, optional `limit` | find a repository's exact name |
| `commit_search` | `repos`, optional `messageTerms`, `authors`, `contentTerms`, `files`, `after`, `before` | History: commits by message, author, or content |
| `diff_search` | `pattern`, `repos`, optional `added`, `removed`, `authors`, `after`, `before` | History: when code matching a pattern was added or removed |
| `compare_revisions` | `repo`, `base`, `head` | what changed between two revisions |
| `code_finder` | `task` | a question in words; returns files and line ranges |

## How to use them well

1. **Get the repository's exact name first** with `list_repos`. Names
   look like `git.example.com/team/service`. Tools need the exact name.
2. **Navigation needs a file and a symbol.** `go_to_definition` and
   `find_references` start from a place the symbol appears: pass the file
   where you saw it and the name as written there.
3. **Confirm by reading.** The answer is exact when the repository has a
   code intelligence index; without one, Sourcegraph falls back to search
   and can be wrong for common names. Open the result with `read_file` and
   see the definition or use.
4. **`keyword_search` queries**: `repo:^git\.example\.com/team/service$
   file:\.py$ def charge`. `repo:` and `file:` take regular expressions.
   Put `count:500` in the query for more results.
5. **Cross-repository trace in**: `find_references` from the definition,
   or `keyword_search` for the import path, such as `from billing.client
   import` with no `repo:` filter, to find every repository that imports
   it.
6. **Sourcegraph shows the indexed revision**, usually the default branch.
   Uncommitted local changes are not in it: for those, search locally.

## Never

- Never report a Sourcegraph result without the repository name, path and
  line.
- Never treat Sourcegraph's default branch as what is running in an
  environment; deployed code may be an older revision.

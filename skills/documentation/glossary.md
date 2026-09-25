# Glossary

One word per idea. Use these words, and no others for the same thing.

| Word | Means | Not |
| --- | --- | --- |
| **claim** | one factual statement in a page or docstring | "info", "detail" |
| **source** | what shows a claim is true: `path:line`, a command and its output, a commit, a record, a person | "reference" (that is a page kind) |
| **not recorded** | no commit, issue, ADR or person gives the reason | "unknown", a guess |
| **surface** | something a reader uses without reading the code: a command, option, environment variable, setting, route, public function, message, job | "feature" |
| **documented** | a page, README or docstring states what the surface does | a name appearing in a code block, which is **mentioned** |
| **page kind** | tutorial, how-to, reference, explanation, ADR, runbook, README, index page | "type", "category" |
| **unit** | a team, system, component, API or resource that owns docs | "project", "service" when meaning the level |
| **index page** | the one page per unit that summarises it and links to its parts | "landing page", "overview" |
| **site repository** | the repository that builds the combined site from all the others | "aggregator" |
| **combined site** | the one site built from every repository's docs | "portal", "hub" |
| **aggregation style** | how the site repository gets other repositories' pages: monorepo plugin, multirepo plugin, or copy step | |
| **strict build** | `mkdocs build --strict` or `zensical build --strict`, which exits 1 on a warning | "a build" |
| **restating docstring** | a docstring that says only what the name and signature already say | |
| **hidden fact** | something a caller must know that the signature does not show: an exception, a side effect, a unit, a shape | |

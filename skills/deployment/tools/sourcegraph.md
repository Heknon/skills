# Sourcegraph (optional)

**Use this only when Sourcegraph's tools appear among your tools**
(`keyword_search`, `read_file`, `list_repos`, ...). If they are not there,
this file does not apply, and everything it does can be done more slowly
through GitLab (`core/discover.md`). The tool names and parameters are the
ones the navigation skill documents (`tools/sourcegraph.md` there). No
Sourcegraph instance was available when this file was written: the query
syntax is Sourcegraph's standard syntax, not run here.

## Why it helps in deployment work

GitLab Community Edition searches code only inside one project; group and
instance-wide code search need advanced search (`core/discover.md`).
Sourcegraph searches every repository it indexes at once. That answers
the questions that span repositories:

| Question | `keyword_search` query |
| --- | --- |
| which repositories include this templates project | `file:(^|/)\.gitlab-ci\.yml$\|^ci/.*\.ya?ml$ platform/templates count:all` |
| which use this component, and at which version | `file:\.ya?ml$ /ci-components/python-checks@ count:all`, then read the version after `@` |
| which project includes are not pinned | `patterntype:regexp file:\.ya?ml$ project:\s*platform/templates` and read each hit's next lines for `ref:` |
| which pipelines deploy with the generic chart, and which version | `file:\.gitlab-ci\.yml$ platform/app --version count:all`, or `CHART_VERSION:` |
| which Dockerfiles use this base image | `file:(^|/)(Docker\|Container)file patterntype:regexp FROM\s+\S*python:3\.11 count:all` |
| who still deploys `latest` | `patterntype:regexp file:\.ya?ml$ image\.tag=latest\|tag:\s*latest` |
| which repositories still use kaniko or `only:`/`except:` | `file:\.gitlab-ci\.yml$ kaniko count:all`; `patterntype:regexp file:\.gitlab-ci\.yml$ ^\s+(only\|except):` |
| where a CI/CD variable name is used | `file:\.ya?ml$ KUBE_NAMESPACE count:all` |
| when an include's ref changed, and who changed it | `diff_search` with pattern `ref: v1\.`, the repository, and `added: true` |

In the table, `\|` stands for a plain `|`: the backslash is only there
for the table. Filters: `repo:^gitlab\.example\.com/shop/` limits to a group's
repositories (regular expression); `file:` takes a regular expression on
the path; `count:all` returns every match instead of the first page;
`patterntype:regexp` makes the pattern a regular expression; `-file:` and
`-repo:` exclude.

## What it cannot tell you

Sourcegraph sees text on the indexed branch (usually the default branch).
It does not resolve anything, so:

- an include written through a variable (`$CI_SERVER_FQDN/...`, `$TEMPLATES_PROJECT`)
  or pulled in by another included file does not match a search for the
  project path;
- it does not know which `rules` apply, which ref a pipeline ran on, or
  what a child pipeline generated at run time;
- a project whose configuration lives in another project
  (`ci_config_path`) has nothing to find in its own repository;
- CI/CD variables, protected settings and pipelines are not in Git at all.

So use it to **find candidates fast**, then **confirm each with GitLab**:
the lint API's `includes` list for that project (`core/discover.md`), or
`recipes/tools/ci_map.py --consumers` for a whole group. Report hits as
"found by text search, confirmed by lint" or "found by text search only".

## Never

- Never report a Sourcegraph result without its repository, path and
  line.
- Never treat the default branch Sourcegraph indexed as what runs in an
  environment; what runs is the deployed commit (`helm history`, the
  environment's last deployment).

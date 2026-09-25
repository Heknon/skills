# Read the Docs

**What it decides:** whether moving the docs site to Read the Docs can
work here, and what the move would take. It plans; it does not start the
move.

Read the Docs is a service that builds each repository's docs on every
push, keeps a copy per version and branch, previews pull requests, and
serves them with search. It builds MkDocs and Zensical sites. It is not a
site generator: the site is still MkDocs or Zensical.

## Facts, checked on 2026-09-25

From Read the Docs' own documentation, `docs.readthedocs.com`. The model
cannot look these up; if the team's instance is newer, say so.

| Fact | What it means here |
| --- | --- |
| The hosted service (Community, and Business for private repositories, with single sign-on) runs on Read the Docs' own servers on the internet. Its documentation names no on-premises or air-gapped option. | It must reach the repositories, and the docs leave the network. In an air-gapped network it cannot be used. |
| The software is open source, but its install guide says: "We do not recommend to follow this guide to deploy an instance of Read the Docs for production." | Self-hosting is possible and not supported. The team would run and upgrade it alone: a web application, a database, a cache, a search server, build workers and Docker. |
| Each build installs packages (`python.install`, or commands in `build.jobs`). | A self-hosted instance needs its build images and every package from the internal mirror. |
| One repository is one project. Several are combined as **subprojects** of a parent project. | Replaces the monorepo, multirepo or copy step (`aggregation.md`). |
| A subproject is served at `/projects/<slug>/<language>/<version>/` under the parent's address, and no longer from its own address. Search on the parent includes the subprojects. | Every address changes: `/billing/` becomes something like `/projects/billing/en/latest/`. Links and bookmarks need redirects. |
| Each repository needs a `.readthedocs.yaml` at its root. | One new file per repository, below. |

## The configuration, per repository

For MkDocs:

```yaml
version: 2
build:
  os: ubuntu-24.04
  tools:
    python: "3.12"
mkdocs:
  configuration: mkdocs.yml
  fail_on_warning: true
python:
  install:
    - requirements: docs/requirements.txt
```

`fail_on_warning: true` is the strict build. The `requirements:` path
above is an example: use the file the repository really has. If its docs
dependencies are in `pyproject.toml`, install the project instead, with
`- method: pip` and `path: .` (and `extra_requirements: [docs]` when they
are an optional group). `python.install` also takes `method: uv`, with
only one entry under `install`. In `mkdocs.yml`, set
`site_url: !ENV READTHEDOCS_CANONICAL_URL` so each version knows its own
address.

For Zensical, which has no `zensical:` key and builds through commands:

```yaml
version: 2
build:
  os: ubuntu-24.04
  tools:
    python: "3.12"
  jobs:
    install:
      - pip install zensical
    build:
      html:
        - zensical build --strict
    post_build:
      - mkdir -p $READTHEDOCS_OUTPUT/html/
      - cp --recursive site/* $READTHEDOCS_OUTPUT/html/
```

Zensical cannot read environment variables in its configuration, so its
`site_url` is written out in full.

## Planning the move, step by step

1. **Can the docs leave the network?** If the ask, the environment or
   the team's records say the network is air gapped, that is the answer:
   the hosted service is out, and the plan offers only self-hosting. Do
   not list the hosted service as an option. Ask only when nothing says.
   Say this first; it decides everything else.
2. **Who would run a self-hosted instance?** It is a service to install,
   upgrade and back up, unsupported by its makers. Name the owner, or
   write `ask`. Without one, the plan stops here, with the reason.
3. **Find the aggregation style** (`aggregation.md`, Step 1), and list
   each repository that feeds the site.
4. **Map each repository to a project**, and the site repository to the
   parent. The site repository's own pages (home, system pages, catalog)
   stay on the parent.
5. **List every address that changes**, old and new, from the built
   site's page list (`aggregation.md`, the list command). Each needs a
   redirect.
6. **List the links between repositories.** They become links between
   projects and must use the new addresses.
7. **Compare what is gained and what is lost.** Gained: a copy per
   version, pull request previews, search across all projects. Lost or
   changed: the addresses, one build per repository instead of one site
   build, and a service to run. Only claims from this file or from the
   team's own records; no guesses about speed or cost.
8. **Write the plan** as a page or in the answer: the verdict from steps
   1 and 2, the project list, the address table, the new files per
   repository, and the open questions. The decision is the team's.

## Never

- Never propose sending the docs or the code to the hosted service from
  an air-gapped network.
- Never start the move, add `.readthedocs.yaml` files or change
  addresses unasked.

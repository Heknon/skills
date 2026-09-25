# Structure

**What it decides:** how docs are organised across a team, its systems
and their parts, and where one fact or one page belongs.

## The levels

The words are Backstage's catalog kinds. They work whether or not
Backstage runs here.

| Level | What it is | Its docs live in | Its index page answers |
| --- | --- | --- | --- |
| **Team** (Group) | the people who own several systems | the site repository's home page | which systems we own, how we work, who to ask |
| **System** | components that together give one capability | the site repository, one page per system; or the repository's `docs\index.md` when the system is one repository | what it does, its components, how they connect, its diagram |
| **Component** | one deployable or releasable unit, usually one repository or one package | that repository's `docs\` folder and `README.md` | what it does, how to run, build and test it, its surfaces |
| **API** | an interface a component offers others: HTTP routes, a Python package, messages | the component that offers it | generated reference, where possible |
| **Resource** | a database, a queue, a bucket a component uses | the component that owns it; the system page if several share it | what it holds, who writes and reads it |
| **Code** | a module, a class, a function | its docstring | its contract (`python/docstrings.md`) |

## Is a part a System or a Component?

1. Is it deployed or released as one unit? **Component.**
2. Is it several such units that only make sense together? **System.**
3. Does it have a different owner from the parent? Its own **System**,
   linked from the parent.
4. Still unsure: treat it as a Component. Promoting it later is cheap.

## Where one fact goes

Find the **lowest level that owns all of it**:

- true of one function: its docstring;
- true of one component: that component's docs;
- about two components of one system (how they talk): the system page;
- about two systems: the team page;
- a convention for everything the team owns: the team page.

Everywhere else links to it. A parent summarises each child in one line
and links down. A child never repeats its parent; it links up.

## A repository's docs

Before adding anything, read the existing layout and keep it. A new page
goes next to pages of the same kind. If there is no layout yet, use:

```
README.md              what it is, how to install, run and test, link to docs
docs/
  index.md             the component's index page (templates/index.md)
  how-to/              one task per page
  reference/           API reference (generated), settings, commands
  explanation/         design and how it works
  adr/                 decision records, numbered: 0001-short-title.md
  runbooks/            one incident or alert per page
```

Create a folder only when its first page is written. An empty folder
tells the reader something exists when it does not.

## The team's catalog

The team page carries one table, the only list of what exists:

| System | Components | Repositories | Owner |
| --- | --- | --- | --- |

Every system in it has a page, and every component row links to that
repository's docs. Fill it from the repositories and from people, never
from names that sound alike. An owner nobody named is left as `ask`.

## Diagrams

One diagram per index page, at that page's level (the C4 model's
levels):

- team page: the systems and what connects them;
- system page: its components, the people and systems around it, and
  the arrows between them, each arrow labelled with what flows (HTTP,
  a queue name, a shared table);
- component page: only if the inside is not obvious from the reference.

Draw with Mermaid in a fenced `mermaid` block, which renders offline when
the site is set up for it (`mkdocs/site.md`). Every box and arrow is a
claim: back each one with navigation (Trace out, Follow) like any
sentence.

```mermaid
flowchart LR
  api[billing-api] -->|HTTP /charges| gateway[payment gateway]
  api -->|charges.created| queue[(events queue)]
  queue --> worker[billing-worker]
```

## Never

- Never invent a system name, a grouping or an owner. When the code and
  the people do not say, ask, or write `ask` in the catalog.
- Never copy a fact down to a child or up to a parent. Link.

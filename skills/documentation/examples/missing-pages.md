# Worked example: a page missing from the combined site

Follow this when the combined site is missing pages or has broken links.
Copy the order and the shape; change the facts.

## The ask

> The refunds page from billing is not on the docs site, and someone said
> its link to orders is broken. Fix it.

## Find the style (`mkdocs/aggregation.md`, Step 1)

The site repository's `mkdocs.yml`:

```yaml
site_url: https://docs.team.internal/
plugins:
  - search
  - monorepo
  ...
nav:
  - Home: index.md
  - Billing: '!include ../billing/mkdocs.yml'
  - Orders: '!include ../orders/mkdocs.yml'
```

`monorepo` and `!include`: style **A**. Billing's pages come from
billing's own `mkdocs.yml` and `nav:`, from the checkout next to the
site repository.

## Make the build show the problem (`mkdocs/site.md`)

The site has no `validation:` block, so a page left out of `nav:` is only
an `INFO` line and the strict build passes. With the block added:

```
$ uv run --no-sync mkdocs build --strict
WARNING -  The following pages exist in the docs directory, but are not included in the "nav" configuration:
  - billing/refunds.md
WARNING -  Doc file 'billing/refunds.md' contains a link '../../orders/docs/index.md', but the target '../orders/docs/index.md' is not found among documentation files.
Aborted with 2 warnings in strict mode!
```

Two causes, both in the billing repository:

1. `billing/mkdocs.yml` `nav:` lists `index.md` and `api.md`, not
   `refunds.md`. The page is built, but no menu leads to it.
2. The link goes through the repositories (`../../orders/docs/index.md`).
   In the combined site, orders' pages are at `orders/`, so the path
   leads nowhere.

## The fix

1. In the billing repository, `mkdocs.yml`, add the page to `nav:`:

   ```yaml
   nav:
     - Overview: index.md
     - API: api.md
     - Refunds: refunds.md
   ```

2. In `billing/docs/refunds.md`, link to orders by the combined site's
   full address, `https://docs.team.internal/orders/`, since a relative
   path cannot work in both the billing build and the combined one
   (`mkdocs/aggregation.md`, Links between repositories).
3. Keep the `validation:` block in the site's `mkdocs.yml`, so the next
   page left out fails the build. That is a change to the build: say it
   in the answer.

## The checks

```
$ uv run --no-sync mkdocs build --strict        # in the site repository
INFO    -  Documentation built in 0.58 seconds
(exit 0)

$ uv run --no-sync mkdocs build --strict        # in the billing repository
INFO    -  Documentation built in 0.08 seconds
(exit 0)
```

## The answer

```
## Changed
- billing/mkdocs.yml: added Refunds to nav.
- billing/docs/refunds.md: the orders link now uses the site's full
  address.
- site mkdocs.yml: added a validation block, so the strict build fails on
  pages left out of nav and on broken links.

## Sources
- The page was left out of nav, and the link was broken: the strict
  build's two warnings, above.
- Orders' pages are at orders/ in the combined site: the monorepo plugin
  names the folder from orders' site_name, "orders".

## Not verified
- https://docs.team.internal/orders/ is the address of the deployed site:
  taken from the site's site_url; no build checks a full address.

## Not done
- Other repositories may link to each other the same way; the strict
  build now reports each one.
- The site uses the monorepo plugin, which Zensical ignores. Moving
  before 2027-05-05 needs a copy step (mkdocs/aggregation.md).
```

# Worked example: the person's diagnosis is wrong

Follow this when the person tells you the cause, and the evidence points
elsewhere. Copy the order of the moments and the shape of the notes.
Change the facts, not the shape.

## The ask

> Users see old prices after we update them. It's the cache. Just turn
> caching off for the price endpoint.

## Start

**Scope** (`core/scope.md`). The ask is a change: turn caching off. But the
goal behind it is that users see new prices, so `done when` must observe
that, or turning the cache off could "succeed" while prices stay old.

**Assumptions** (`core/assumptions.md`). The person's diagnosis is the
largest one, so it is written down and treated as a hypothesis (the silent
assumptions table: "the person's diagnosis is right").

## Investigate

Two causes. H1 is the person's: the response cache serves old prices. H2
comes from asking what else would produce the same symptom: the price is
already old where the endpoint reads it.

Step 2 reproduces: update a price, read it back, old price. Step 3 is the
test that separates the two: read the same endpoint with the cache
bypassed. Still old. So the cache is not what serves the old price: H1 ruled
out. Step 4 reads where the endpoint gets prices: a read replica. Step 5
measures the replica lag: 40 minutes. H2 confirmed.

## Pushback

**Challenge** (`core/challenge.md`) the person's plan: turning off the
cache does not meet their goal (question 1: it fails because prices come
from the lagging replica either way), and it makes every request slower.
The evidence is observed, so **pushback** (`core/pushback.md`), once:

> You said the cache serves the old prices. I observed the old price with
> the cache bypassed (step 3), and the replica the endpoint reads is 40
> minutes behind (step 5). That means turning caching off would slow the
> endpoint and prices would still be old. I recommend reading prices from
> the primary for this endpoint. Tell me if you still want caching off.

The person answers: read from the primary, leave the cache on. The
decision is theirs; the verdict line records it.

## The notes

```
goal: "Users see old prices after we update them. It's the cache. Just turn caching off for the price endpoint."
kind: change
done when: a price updated through the admin API is returned by `GET /prices/<sku>` within 5 seconds, observed with `tools/price_roundtrip.py`
budget: 25 steps
scope out: why the replica lags 40 minutes

assumptions:
- A1 [false at step 3] the person's diagnosis: the response cache serves the old prices

hypotheses:
- H1 [ruled out at step 3] the response cache serves old prices | test: read /prices/<sku> with the cache bypassed | disproved if: the old price comes back with the cache bypassed
- H2 [confirmed at step 5] the endpoint reads prices from a lagging replica | test: read the data source in the endpoint, then measure replica lag | disproved if: it reads the primary, or lag is under 5 seconds

steps:
1. search "prices" in api/routes/ -> api/routes/prices.py:22 get_price(sku) -> /prices/<sku> is served by api/routes/prices.py
2. `python tools/price_roundtrip.py --sku P-100 --wait 5` -> wrote 12.50, read 11.90 after 5 s -> the stale price reproduces
3. `python tools/price_roundtrip.py --sku P-100 --wait 5 --no-cache` -> wrote 12.60, read 11.90 after 5 s -> the price is stale with the cache bypassed
4. read api/routes/prices.py lines 22-40 -> get_price uses db.replica() -> the endpoint reads from the replica
5. `python manage.py replica_lag` -> replica lag 2412 s -> the replica is 40 minutes behind
   verdict hypothesis-loop: H2 confirmed at step 5: the endpoint reads a replica 40 minutes behind
6. ask: pushback message, caching off will not fix it, read prices from the primary instead? -> person: read from the primary, keep the cache on -> the person chose reading from the primary
   verdict pushback: said the cache serves old prices vs stale with cache bypassed (step 3) and replica lag 2412 s (step 5); person decided read from the primary, keep the cache
7. edit api/routes/prices.py line 25 from db.replica() to db.primary() -> one line changed -> get_price reads the primary
8. `python tools/price_roundtrip.py --sku P-100 --wait 5` -> wrote 12.70, read 12.70 after 5 s -> the updated price is returned within 5 seconds

done: observed at step 8: wrote 12.70 and read 12.70 back within 5 seconds with the cache on
```

## The answer

```
The cache was not the cause. With the cache bypassed the old price still
came back (step 3), because /prices/<sku> read from a replica that is 40
minutes behind (steps 4 and 5). As you decided, the endpoint now reads
prices from the primary and the cache stays on (api/routes/prices.py line
25). A price written through the admin API is now returned within 5
seconds (step 8).

## Done when
A price updated through the admin API is returned by GET /prices/<sku>
within 5 seconds: observed at step 8.

## Not done
- Caching was not turned off, by your decision after step 6.
- Why the replica lags 40 minutes (scope out); other endpoints reading the
  replica will show the same staleness.

## Unverified
none

## Decided for you
none
```

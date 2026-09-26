# Lab record

Written by `run_lab.py`. Proof exit codes: 1 = the bug shows, 0 = it does not, 125 = no MongoDB.

| Sandbox | Pass that should find it | Planted at | Proof main / change | Sign IDs on the planted lines | Leads in all | Leads on added lines, per checklist | Contracts (defs) | New tool lines |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pagination | correctness | src/shop/catalog.py:28-29 | 0 / 1 | COR1 | 3 | api-contract 2, correctness 1 | 1 | 0 |
| lookup | callers | src/shop/invoices.py:8-11 (outside the diff) | 0 / 1 | - | 9 | edge-cases 3, models 1 | 1 | 0 |
| refunds | correctness | src/shop/refunds.py:30-30 | 0 / 1 | COR3 | 4 | correctness 3, edge-cases 1 | 0 | 2 |
| clean | none: clean | none | 0 / 0 | - | 3 | api-contract 1, errors 1, security 1 | 0 | 0 |
| status422 | none: clean | none | 0 / 0 | - | 6 | api-contract 2, correctness 2, errors 2 | 0 | 0 |
| login | security | src/shop/api.py:31-31 | 0 / 1 | SEC1 | 8 | api-contract 1, edge-cases 2, errors 1, security 1 | 3 | 0 |
| users | architecture, security | src/shop/api.py:51-51 | 0 / 1 | - | 5 | api-contract 1, data 1, edge-cases 2, errors 1 | 0 | 0 |
| mocktest | tests | tests/test_pricing.py:11-17 | 0 / 1 | TST1 | 4 | correctness 2, tests 2 | 0 | 0 |
| rereview | correctness | src/shop/points.py:31-31 | 0 / 1 | COR1 | 1 | correctness 1 | 1 | 0 |
| counter | concurrency | src/shop/pages.py:16-20 | 0 / 1 | CON1, CON5, COR1, EDG2 | 8 | api-contract 1, concurrency 2, correctness 1, edge-cases 1, errors 1 | 2 | 0 |
| docstring | none: nits only | none | 0 / 0 | - | 0 | - | 0 | 0 |
| defaults | callers | src/shop/repository.py:22-22 | 0 / 1 | COR4 | 4 | correctness 1 | 4 | 0 |
| swallow | errors | src/shop/api.py:38-43 | 0 / 1 | ERR1 | 2 | errors 2 | 0 | 0 |
| wide | correctness | src/shop/discounts.py:17-17 | 0 / 1 | COR1 | 7 | correctness 5, edge-cases 1, models 1 | 2 | 0 |

## Tool and proof lines

### pagination

```
main:    All checks passed! | Success: no issues found in 4 source files | 1 passed in 0.65s
change:  All checks passed! | Success: no issues found in 4 source files | 2 passed in 0.32s
proof:   main (no output)
         change page 1 size 10: 9 items; never shown: ['SKU-010', 'SKU-020']
```

### lookup

```
main:    All checks passed! | Success: no issues found in 5 source files | 3 passed in 0.01s
change:  All checks passed! | Success: no issues found in 5 source files | 3 passed in 0.01s
proof:   main Invoice 8 - guest customer
         change invoice_header('nobody@example.com', 8) raised AttributeError("'NoneType' object has no attribute 'name'")
```

### refunds

```
main:    All checks passed! | Success: no issues found in 3 source files | 2 passed in 0.01s
change:  Found 1 error. | Found 1 error in 1 file (checked 3 source files) | 4 passed in 0.01s
proof:   main (no output)
         change refund_amount(4000 cents, 50 percent) = 8000
```

### clean

```
main:    All checks passed! | Success: no issues found in 4 source files | 2 passed in 0.61s
change:  All checks passed! | Success: no issues found in 4 source files | 5 passed in 0.29s
proof:   main (no output)
         change total of o-1: 3499; unknown order: 404
```

### status422

```
main:    All checks passed! | Success: no issues found in 4 source files | 2 passed in 0.67s
change:  All checks passed! | Success: no issues found in 4 source files | 2 passed in 0.28s
proof:   main qty 11: 200 {'sku': 'SKU-1', 'left': 1}
         change qty 11: 422 {'detail': 'at most 10 units per order'}
```

### login

```
main:    All checks passed! | Success: no issues found in 4 source files | 2 passed in 0.97s
change:  All checks passed! | Success: no issues found in 4 source files | 4 passed in 0.34s
proof:   main api_key {"$ne": null}: 422 {'detail': [{'type': 'string_type', 'loc': ['body', 'api_key'], 'msg': 'Input should be a valid string', 'input': {'$ne': None}}]}
         change api_key {"$ne": null}: 200 {'client_id': 'acme', 'scopes': ['orders:read']}
```

### users

```
main:    All checks passed! | Success: no issues found in 7 source files | 2 passed in 0.99s
change:  All checks passed! | Success: no issues found in 7 source files | 2 passed in 0.36s
proof:   main GET /users/by-email/ann@example.com: 404 {"detail":"Not Found"}
         change GET /users/by-email/ann@example.com: 200 {"_id":"6ab77d6853a5b2c7deefd53a","email":"ann@example.com","name":"Ann","password_hash":"h$1"}
```

### mocktest

```
main:    All checks passed! | Success: no issues found in 3 source files | 1 passed in 0.01s
change:  All checks passed! | Success: no issues found in 3 source files | 3 passed in 0.01s
proof:   main (no output)
         change with shipping_cents broken: 3 passed in 0.01s
```

### rereview

```
main:    All checks passed! | Success: no issues found in 3 source files | 1 passed in 0.01s
change:  All checks passed! | Success: no issues found in 3 source files | 4 passed in 0.01s
proof:   main (no output)
         change moving the whole balance of 10 raised InsufficientPoints
```

### counter

```
main:    All checks passed! | Success: no issues found in 4 source files | 1 passed in 0.30s
change:  All checks passed! | Success: no issues found in 4 source files | 2 passed in 0.06s
proof:   main 2000 views from 16 threads stored as 2000
         change 2000 views from 16 threads stored as 231
```

### docstring

```
main:    All checks passed! | Success: no issues found in 3 source files | 1 passed in 0.01s
change:  All checks passed! | Success: no issues found in 3 source files | 3 passed in 0.01s
proof:   main (no output)
         change (no output)
```

### defaults

```
main:    All checks passed! | Success: no issues found in 4 source files | 3 passed in 0.01s
change:  All checks passed! | Success: no issues found in 5 source files | 3 passed in 0.01s
proof:   main revenue_cents('c-2') = 1200
         change revenue_cents('c-2') = 11100
```

### swallow

```
main:    All checks passed! | Success: no issues found in 4 source files | 1 passed in 0.62s
change:  All checks passed! | Success: no issues found in 4 source files | 2 passed in 0.33s
proof:   main store down: 500 Internal Server Error
         change store down: 201 {"order_id":"o-1","saved":true}
```

### wide

```
main:    All checks passed! | Success: no issues found in 43 source files | 4 passed in 0.01s
change:  All checks passed! | Success: no issues found in 43 source files | 4 passed in 0.01s
proof:   main (no output)
         change discounted_cents(10000, None, order_count=10) = 10000
```

## Passes run by hand

- users: architecture's searches (its `checklist/finding.md`) on the added lines: L3 at `src/shop/api.py:51` (`-> User`), L1 at `:52` (`await User.find_one(`). The leak is found by this pass, not by a sign.
- lookup: `review_diff.py defs` listed `find_customer` (no longer raises `CustomerNotFound`); `git grep -n -w find_customer` then found the caller `src/shop/invoices.py:8`; `mypy --check-untyped-defs` reported `invoices.py:11` [union-attr] where the project's mypy passed.
- defaults: `review_diff.py defs` printed the moved `list_orders` with `include_cancelled: bool = False` -> `= True`.

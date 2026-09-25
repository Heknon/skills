# Worked example: the ask contains a guess

Follow this when the person tells you how the code behaves. What they
say is a hypothesis to check, not a source (`core/claims.md`, rule 4).

## The ask

> Write a how-to for charging a customer. It retries three times on a
> timeout, and we chose three because the gateway rate-limits us.

## Check each claim against the code

| Claim in the ask | Code | Result |
| --- | --- | --- |
| retries three times | `retries: int = 5` (`src/billing/charges.py:9`), loop `for attempt in range(retries)` (line 20) | **wrong**: five attempts in total by default |
| on a timeout | `except GatewayTimeout:` (line 24) | right |
| chosen because of rate limits | `git log -L 9,9:src/billing/charges.py` shows one commit, message "add charge" | **not recorded** |

Two findings to tell the person: the number is five, not three; and no
record gives the reason. The page states five and does not state the
reason.

## Kind and template

The reader wants to charge a customer: a **how-to**
(`core/page-types.md`, `templates/how-to.md`). The retry details are
reference facts: the page links to the API reference instead of listing
every parameter.

## The page

````markdown
# How to charge a customer

Use this to take a payment from a customer through the payment gateway.

## Before you start

- The customer's id.
- The amount in cents.

## Steps

1. Call `charge()` with the customer id and the amount in cents.

   ```python
   from billing.charges import charge

   payment = charge("c-1042", 1234)
   ```

2. Keep `payment["id"]`. It is the payment id the gateway returned.

If the gateway times out, `charge()` tries again, up to five attempts in
total, waiting longer after each timeout. After the last one it raises
`GatewayTimeout`.

## Check it worked

`payment["status"]` holds the gateway's status for the payment.

## Related

- [Billing API](../reference/api.md): every parameter of `charge()`.
````

## The answer

```
## Changed
- docs/how-to/charge-a-customer.md: new how-to.

## Sources
- amount in cents: format_amount divides by 100 (charges.py:34).
- five attempts by default: src/billing/charges.py:9 (retries: int = 5)
  and :20 (range(retries)).
- retries on GatewayTimeout only: charges.py:24.
- waits longer each time: charges.py:25, time.sleep(delay * (attempt + 1)).
- raises GatewayTimeout after the last attempt: charges.py:27.
- payment["id"] and payment["status"]: charges.py:29.

## Not verified
- none

## Not done
- You said it retries three times; the code's default is five (charges.py:9).
  The page says five. If three is intended, the code needs changing.
- You said three was chosen because of the gateway's rate limits. No
  commit, issue or ADR records a reason, so the page does not give one.
  An ADR would be the place, once someone who knows confirms it.
```

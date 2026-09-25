# Ledger

Records every money movement once.

```mermaid
flowchart LR
  billing[billing-worker] -->|POST /entries| ledger[ledger-api]
  ledger --> db[(ledger database)]
```

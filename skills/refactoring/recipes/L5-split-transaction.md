# L5: one transaction owner

**End state:** the architecture skill's
`shapes/L5-split-transaction.md`: repositories flush and never commit;
the service wraps the use case in the unit of work's `transaction()`.
**Steps:** the unit of work added unused, the use case routed through
it, then one commit that changes behaviour on purpose.

The last step is not a refactoring. The before commits each write, so a
failed transfer keeps its first half; after it, the transfer rolls
back. That is the bug the shape fixes (its after-only test fails on the
before: `[70, 0]`). So it is its own commit, with the test that fails
first, named as a behaviour change (`core/refactor-or-fix.md`); do it
when the ask is atomicity or the shape, and say so.

## Pins

The shape's test (a transfer that succeeds). Search every caller of
the repository's write methods (`\.add\(` on `Accounts` here) in all
files, scripts included: after step 3 each must run inside a unit of
work, or its write is lost (Traps).

## Steps

### 1. Add the unit of work, not used yet

```diff
diff --git a/app/bank.py b/app/bank.py
--- a/app/bank.py
+++ b/app/bank.py
@@ -1,2 +1,5 @@
+from collections.abc import AsyncIterator
+from contextlib import asynccontextmanager
+
 from sqlalchemy import update
 from sqlalchemy.ext.asyncio import AsyncSession
@@ -26,4 +29,15 @@ class Accounts:
 
 
+class UnitOfWork:
+    def __init__(self, session: AsyncSession) -> None:
+        self.session = session
+        self.accounts = Accounts(session)
+
+    @asynccontextmanager
+    async def transaction(self) -> AsyncIterator[None]:
+        async with self.session.begin():                 # the one commit or rollback
+            yield
+
+
 async def transfer(session: AsyncSession, source: int, target: int, amount: int) -> None:
     accounts = Accounts(session)
```

Commit: `Add UnitOfWork beside Accounts`

### 2. Reach the repository through the unit of work, still committing per write

No transaction yet: each write still commits, so behaviour is the same.

```diff
diff --git a/app/bank.py b/app/bank.py
--- a/app/bank.py
+++ b/app/bank.py
@@ -41,5 +41,5 @@ class UnitOfWork:
 
 async def transfer(session: AsyncSession, source: int, target: int, amount: int) -> None:
-    accounts = Accounts(session)
-    await accounts.add(source, -amount)
-    await accounts.add(target, amount)
+    uow = UnitOfWork(session)
+    await uow.accounts.add(source, -amount)
+    await uow.accounts.add(target, amount)
```

Commit: `Reach Accounts through UnitOfWork in transfer`

### 3. Commit once, in the unit of work (behaviour change: a failed transfer now rolls back)

The test comes first: with only `test_rollback.py` added to step 2's
code, the tests gave `1 failed, 1 passed`; with the change, `2 passed`.
The commit body names the change: "A transfer to a missing account
used to keep the debit; it now rolls back."

```diff
diff --git a/app/bank.py b/app/bank.py
--- a/app/bank.py
+++ b/app/bank.py
@@ -25,6 +25,5 @@ class Accounts:
             update(Account).where(Account.id == account_id).values(balance=Account.balance + delta))
         if result.rowcount == 0:
-            raise LookupError(account_id)
-        await self.session.commit()                      # each write commits
+            raise LookupError(account_id)                # no commit here
 
 
@@ -42,4 +41,5 @@ class UnitOfWork:
 async def transfer(session: AsyncSession, source: int, target: int, amount: int) -> None:
     uow = UnitOfWork(session)
-    await uow.accounts.add(source, -amount)
-    await uow.accounts.add(target, amount)
+    async with uow.transaction():
+        await uow.accounts.add(source, -amount)
+        await uow.accounts.add(target, amount)
diff --git a/test_rollback.py b/test_rollback.py
new file mode 100644
--- /dev/null
+++ b/test_rollback.py
@@ -0,0 +1,6 @@
+from test_shape import run
+
+
+def test_failed_credit_keeps_the_money(tmp_path):
+    balances, failure = run(1, 99, 30, tmp_path)
+    assert balances == [100, 0] and isinstance(failure, LookupError)
```

Commit: `Make a transfer one transaction`

## Traps seen in the lab

| Trap | What happened |
| --- | --- |
| `transaction()` added while the repository still committed | red: `sqlalchemy.exc.InvalidRequestError: Can't operate on closed transaction inside context manager.  Please complete the context manager before emitting further commands.` The commit comes out in the same step as `transaction()` goes in |
| a script that called `Accounts(s).add(1, 5)` with no unit of work | after step 2 the balance was 105; after step 3, 100: the session closed without a commit and the write was lost, with no error. Every such caller moves into a unit of work in step 3 |
| seniority's change check | `OK` at every step, step 3 included: it compares signatures, not commits. The behaviour change is shown by the test that failed first |

## What the checks said (lab)

```
L5   start  tests 1 passed | ruff clean | mypy {'attr-defined': 1} | import-all 2 ok, 0 failed, 0 skipped
L5   1. Add UnitOfWork beside Accounts
      tests 1 passed | ruff same | mypy same | import-all 2 ok, 0 failed, 0 skipped
      names none lost | change check OK
L5   2. Reach Accounts through UnitOfWork in transfer
      tests 1 passed | ruff same | mypy same | import-all 2 ok, 0 failed, 0 skipped
      names none lost | change check OK
L5   3.     test first: 1 failed, 1 passed
L5   3. Make a transfer one transaction
      tests 2 passed | ruff same | mypy same | import-all 2 ok, 0 failed, 0 skipped
      names none lost | change check OK
L5   end    identical to the shape's after (3 files)
```

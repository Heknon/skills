import sqlite3

DB = "ledger.sqlite3"


def add_entry(entry):
    with sqlite3.connect(DB) as db:
        db.execute("insert into entries (customer, amount, kind) values (?, ?, ?)",
                   (entry["customer"], entry["amount"], entry["kind"]))


ROUTES = {("POST", "/entries"): add_entry}


def main():
    print("serving", list(ROUTES))

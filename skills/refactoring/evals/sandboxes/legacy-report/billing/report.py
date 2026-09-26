import csv
import datetime


def build_report(path):
    # overdue invoices per customer, as text for the morning mail
    today = datetime.date.today()
    rows = []
    f = open(path, encoding="utf-8")
    for r in csv.DictReader(f):
        rows.append(r)
    f.close()
    out = {}
    for r in rows:
        if r["status"] == "paid":
            continue
        due = datetime.date.fromisoformat(r["due"])
        days = (today - due).days
        if days <= 0:
            continue
        amt = float(r["amount"])
        if r["currency"] != "EUR":
            amt = amt * float(r.get("rate") or 1)
        if r["customer"] not in out:
            out[r["customer"]] = [0, 0.0, 0]
        out[r["customer"]][0] += 1
        out[r["customer"]][1] += amt
        if days > out[r["customer"]][2]:
            out[r["customer"]][2] = days
    lines = ["Overdue on " + today.strftime("%d %b %Y")]
    for c in sorted(out, key=lambda k: -out[k][1]):
        n, total, worst = out[c]
        flag = " !" if worst > 60 else ""
        lines.append("%-12s %2d  %10.2f EUR  %3d days%s" % (c, n, total, worst, flag))
    if len(lines) == 1:
        lines.append("nothing overdue")
    return "\n".join(lines)

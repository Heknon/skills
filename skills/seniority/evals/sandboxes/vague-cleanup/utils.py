import time
import json


def load(p):
    f = open(p)
    d = json.load(f)
    return d


def retry(fn, n=3):
    for i in range(n):
        try:
            return fn()
        except Exception:
            time.sleep(1)
    return None


def fmt_money(v):
    return "$" + str(round(v, 2))


def chunks(l, n):
    out = []
    for i in range(0, len(l), n):
        out.append(l[i:i + n])
    return out

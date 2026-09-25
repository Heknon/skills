#!/bin/sh
# Builds the git history this scenario needs. Run once in the copied sandbox.
set -e
git init -q -b main
git config user.email dev@example.com
git config user.name "Noa Ben-David"
mkdir -p rates docs/explanation
cat > rates/__init__.py <<'PY'
PY
cat > rates/provider.py <<'PY'
import json
import urllib.request

PROVIDER_URL = "http://fx-provider.internal/v2/latest"


def fetch_rates(base: str) -> dict[str, float]:
    with urllib.request.urlopen(f"{PROVIDER_URL}?base={base}", timeout=10) as response:
        return json.load(response)["rates"]
PY
git add -A
git commit -qm "Add rates provider"
cat > rates/cache.py <<'PY'
import json

import redis

from rates.provider import fetch_rates

RATES_TTL_SECONDS = 3600
_client = redis.Redis(host="redis.internal", port=6379, db=2)


def get_rates(base: str) -> dict[str, float]:
    key = f"fx:{base}"
    cached = _client.get(key)
    if cached is not None:
        return json.loads(cached)
    rates = fetch_rates(base)
    _client.set(key, json.dumps(rates), ex=RATES_TTL_SECONDS)
    return rates
PY
git add -A
git commit -qm "add cache"
sed -i 's/RATES_TTL_SECONDS = 3600/RATES_TTL_SECONDS = 3600  # one hour/' rates/cache.py
git commit -qam "tweak"
cat > docs/index.md <<'MD'
# Rates

Exchange rates for the billing system.

- [How rates are cached](explanation/caching.md)
MD
cat > mkdocs.yml <<'YML'
site_name: Rates
theme:
  name: material
  font: false
nav:
  - Home: index.md
YML
git add -A
git commit -qm "docs skeleton"
rm setup.sh

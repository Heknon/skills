COUNTRIES = {"GB": "United Kingdom", "DE": "Germany", "FR": "France", "IE": "Ireland"}


def country_name(code):
    return COUNTRIES.get(code.strip().upper())


def clean(record):
    """One customer from the partner export, tidied for our database."""
    return {
        "name": record["name"].strip(),
        "email": record["email"].strip().lower(),
        "phone": (record.get("phone") or "").strip(),
        "company": (record.get("company") or "").strip(),
        "country": country_name(record["country"]).strip(),
    }

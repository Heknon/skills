def totals_by_region(rows):
    """Sum the amounts of each region."""
    totals = {}
    for row in rows:
        region = row["region"]
        totals[region] = totals.get(region, 0.0) + row["amount"]
    return totals

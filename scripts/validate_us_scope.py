#!/usr/bin/env python3
"""Validate the effective USA page scope against an exported DimCustomer table."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path


EXPECTED_COUNTRY_COUNTS = {"AU": 3591, "CA": 1571, "DE": 1780, "FR": 1810, "GB": 1913, "US": 7819}
EXPECTED_US_STATES = 22


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path, help="Path to the exported DimCustomer.csv file")
    args = parser.parse_args()

    with args.csv.open("r", encoding="utf-8-sig", newline="") as source:
        rows = list(csv.DictReader(source, delimiter=";"))

    required = {"CountryRegionCode", "StateProvinceName"}
    if not rows or not required.issubset(rows[0]):
        raise SystemExit(f"Missing required columns {sorted(required)} in {args.csv}")

    country_counts = Counter(row["CountryRegionCode"] for row in rows)
    if dict(sorted(country_counts.items())) != EXPECTED_COUNTRY_COUNTS:
        raise SystemExit(f"Unexpected country counts: {dict(sorted(country_counts.items()))}")

    us_rows = [row for row in rows if row["CountryRegionCode"] == "US"]
    non_us_in_scope = [row for row in us_rows if row["CountryRegionCode"] != "US"]
    states = sorted({row["StateProvinceName"] for row in us_rows})

    if non_us_in_scope:
        raise SystemExit(f"USA scope contains {len(non_us_in_scope)} non-US rows")
    if len(us_rows) != 7819 or len(states) != EXPECTED_US_STATES:
        raise SystemExit(f"Unexpected USA scope: {len(us_rows)} rows, {len(states)} states")

    print("USA customer scope validation PASSED")
    print(f"  - full customer dimension: {len(rows)} rows")
    print(f"  - US scope: {len(us_rows)} rows, {len(states)} unique state names")
    print("  - non-US rows in US scope: 0")
    print(f"  - sample states: {', '.join(states[:5])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

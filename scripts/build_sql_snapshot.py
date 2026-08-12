#!/usr/bin/env python3
"""Build a deterministic, non-PII SQL input snapshot from pbi-tools CSV exports."""

from __future__ import annotations

import argparse
import csv
import gzip
import io
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "DATA" / "financial_sql_input.csv.gz"
FIELDS = (
    "SalesOrderNumber",
    "SalesOrderLineNumber",
    "OrderDateKey",
    "CustomerKey",
    "ProductKey",
    "SalesAmount",
    "TotalProductCost",
    "Freight",
    "TaxAmt",
    "CountryRegionCode",
    "StateProvinceName",
    "ProductCategory",
)


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter=";"))


def decimal_point(value: str) -> str:
    return value.strip().replace(",", ".")


def build_snapshot(export_dir: Path, output: Path) -> tuple[int, int, int]:
    required = ("FactInternetSales.csv", "DimCustomer.csv", "DimProduct.csv")
    missing = [name for name in required if not (export_dir / name).is_file()]
    if missing:
        raise SystemExit(f"Missing pbi-tools exports: {', '.join(missing)}")

    customers = {
        row["CustomerKey"]: (row["CountryRegionCode"], row["StateProvinceName"])
        for row in read_rows(export_dir / "DimCustomer.csv")
    }
    products = {
        row["ProductKey"]: row["Category Name"]
        for row in read_rows(export_dir / "DimProduct.csv")
    }

    facts: list[dict[str, str]] = []
    for fact in read_rows(export_dir / "FactInternetSales.csv"):
        customer = customers.get(fact["CustomerKey"])
        category = products.get(fact["ProductKey"])
        if customer is None or category is None:
            raise SystemExit(
                "Unresolved dimension key: "
                f"customer={fact['CustomerKey']} product={fact['ProductKey']}"
            )
        facts.append(
            {
                "SalesOrderNumber": fact["SalesOrderNumber"],
                "SalesOrderLineNumber": fact["SalesOrderLineNumber"],
                "OrderDateKey": fact["OrderDateKey"],
                "CustomerKey": fact["CustomerKey"],
                "ProductKey": fact["ProductKey"],
                "SalesAmount": decimal_point(fact["SalesAmount"]),
                "TotalProductCost": decimal_point(fact["TotalProductCost"]),
                "Freight": decimal_point(fact["Freight"]),
                "TaxAmt": decimal_point(fact["TaxAmt"]),
                "CountryRegionCode": customer[0],
                "StateProvinceName": customer[1],
                "ProductCategory": category,
            }
        )

    facts.sort(key=lambda row: (row["SalesOrderNumber"], int(row["SalesOrderLineNumber"])))
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
            with io.TextIOWrapper(compressed, encoding="utf-8", newline="") as text:
                writer = csv.DictWriter(text, fieldnames=FIELDS, lineterminator="\n")
                writer.writeheader()
                writer.writerows(facts)

    return len(facts), len(customers), len(products)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("export_dir", type=Path, help="Directory produced by pbi-tools export-data")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    facts, customers, products = build_snapshot(args.export_dir.resolve(), args.output.resolve())
    print("SQL input snapshot built")
    print(f"  - facts: {facts:,}")
    print(f"  - customer dimension rows resolved: {customers:,}")
    print(f"  - product dimension rows resolved: {products:,}")
    print(f"  - output: {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

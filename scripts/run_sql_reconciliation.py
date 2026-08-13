#!/usr/bin/env python3
"""Run independent SQL KPIs over the committed source snapshot and compare to DAX."""

from __future__ import annotations

import argparse
import csv
import gzip
import math
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "DATA" / "financial_sql_input.csv.gz"
DEFAULT_QUERY = ROOT / "sql" / "reconcile_kpis.sql"
DEFAULT_OUTPUT = ROOT / "DOCS" / "sql_reconciliation.csv"
DEFAULT_DAX = ROOT / "DOCS" / "dax_reconciliation.csv"
OUTPUT_FIELDS = (
    "Granularity",
    "Member",
    "Revenue",
    "COGS",
    "Shipping",
    "Tax",
    "GrossProfit",
    "NetProfit",
    "GrossMargin",
    "NetMargin",
    "RevenueLY",
)
MONEY_FIELDS = (
    "Revenue", "COGS", "Shipping", "Tax", "GrossProfit", "NetProfit"
)
RATIO_FIELDS = ("GrossMargin", "NetMargin")


def load_source(connection: sqlite3.Connection, source: Path) -> int:
    connection.execute(
        """
        CREATE TABLE financial_source (
            SalesOrderNumber TEXT NOT NULL,
            SalesOrderLineNumber INTEGER NOT NULL,
            OrderDateKey INTEGER NOT NULL,
            CustomerKey INTEGER NOT NULL,
            ProductKey INTEGER NOT NULL,
            SalesAmount TEXT NOT NULL,
            TotalProductCost TEXT NOT NULL,
            Freight TEXT NOT NULL,
            TaxAmt TEXT NOT NULL,
            CountryRegionCode TEXT NOT NULL,
            StateProvinceName TEXT NOT NULL,
            ProductCategory TEXT NOT NULL
        )
        """
    )
    count = 0
    with gzip.open(source, mode="rt", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        expected = [column[1] for column in connection.execute("PRAGMA table_info(financial_source)")]
        if reader.fieldnames != expected:
            raise SystemExit(
                f"Unexpected SQL snapshot columns: {reader.fieldnames}; expected {expected}"
            )
        batch: list[tuple[str, ...]] = []
        for row in reader:
            batch.append(tuple(row[name] for name in expected))
            count += 1
            if len(batch) == 5_000:
                connection.executemany(
                    f"INSERT INTO financial_source VALUES ({','.join('?' for _ in expected)})",
                    batch,
                )
                batch.clear()
        if batch:
            connection.executemany(
                f"INSERT INTO financial_source VALUES ({','.join('?' for _ in expected)})",
                batch,
            )
    return count


def query_rows(connection: sqlite3.Connection, query: Path) -> list[dict[str, str]]:
    cursor = connection.execute(query.read_text(encoding="utf-8-sig"))
    names = [column[0] for column in cursor.description]
    if tuple(names) != OUTPUT_FIELDS:
        raise SystemExit(f"Unexpected SQL output columns: {names}")
    rows: list[dict[str, str]] = []
    for values in cursor.fetchall():
        row: dict[str, str] = {}
        for name, value in zip(names, values, strict=True):
            if value is None:
                row[name] = ""
            elif isinstance(value, (int, float)):
                row[name] = format(value, ".17g")
            else:
                row[name] = str(value)
        rows.append(row)
    return rows


def write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def close(left: str, right: str, *, atol: float) -> bool:
    return math.isclose(float(left), float(right), rel_tol=1e-12, abs_tol=atol)


def compare_to_dax(sql_rows: list[dict[str, str]], dax_path: Path) -> None:
    dax_rows = read_csv(dax_path)
    sql_index = {(row["Granularity"], row["Member"]): row for row in sql_rows}
    dax_index = {(row["Granularity"], row["Member"]): row for row in dax_rows}
    if sql_index.keys() != dax_index.keys():
        missing_sql = sorted(dax_index.keys() - sql_index.keys())
        missing_dax = sorted(sql_index.keys() - dax_index.keys())
        raise SystemExit(
            f"SQL/DAX context mismatch; missing SQL={missing_sql}, missing DAX={missing_dax}"
        )

    failures: list[str] = []
    for key in sorted(sql_index):
        sql_row = sql_index[key]
        dax_row = dax_index[key]
        for field in MONEY_FIELDS:
            if not close(sql_row[field], dax_row[field], atol=0.01):
                failures.append(f"{key} {field}: SQL={sql_row[field]} DAX={dax_row[field]}")
        for field in RATIO_FIELDS:
            if not close(sql_row[field], dax_row[field], atol=1e-10):
                failures.append(f"{key} {field}: SQL={sql_row[field]} DAX={dax_row[field]}")
        if key[0] == "Year" and dax_row["RevenueLY"]:
            if not sql_row["RevenueLY"] or not close(
                sql_row["RevenueLY"], dax_row["RevenueLY"], atol=0.01
            ):
                failures.append(
                    f"{key} RevenueLY: SQL={sql_row['RevenueLY']} DAX={dax_row['RevenueLY']}"
                )
    if failures:
        preview = "\n  - ".join(failures[:20])
        raise SystemExit(f"SQL/DAX reconciliation failed:\n  - {preview}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--query", type=Path, default=DEFAULT_QUERY)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--dax", type=Path, default=DEFAULT_DAX)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    for path in (args.source, args.query, args.dax):
        if not path.is_file():
            raise SystemExit(f"Required input missing: {path}")

    with sqlite3.connect(":memory:") as connection:
        count = load_source(connection, args.source)
        sql_rows = query_rows(connection, args.query)
    if count != 60_398:
        raise SystemExit(f"Expected 60,398 facts; loaded {count:,}")
    if len(sql_rows) != 68:
        raise SystemExit(f"Expected 68 SQL contexts; queried {len(sql_rows)}")
    compare_to_dax(sql_rows, args.dax)
    write_rows(args.output, sql_rows)

    print("Independent SQL reconciliation PASSED")
    print(f"  - source facts: {count:,}")
    print(f"  - compared SQL/DAX contexts: {len(sql_rows)}")
    print("  - monetary tolerance: $0.01")
    print("  - ratio tolerance: 1e-10")
    print(f"  - evidence: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

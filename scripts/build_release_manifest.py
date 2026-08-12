#!/usr/bin/env python3
"""Build or check the machine-readable FIN-C3 release manifest."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "release" / "financial-c3-manifest.json"
ARTIFACTS = (
    "Financial_Report.pbix",
    "Financial_Report.pbit",
    "DATA/financial_sql_input.csv.gz",
    "DOCS/dax_reconciliation.csv",
    "DOCS/sql_reconciliation.csv",
    "Financial_Report/Model/tables/Tablas de Medidas.tmdl",
    "sql/reconcile_kpis.sql",
    "Images/executive_overview.png",
    "Images/overview.png",
    "Images/usa_detailed.png",
    "Images/glossary.png",
    "output/pdf/financial_c3_release_evidence.pdf",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().lower()


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def source_count(path: Path) -> int:
    with gzip.open(path, mode="rt", encoding="utf-8", newline="") as handle:
        return sum(1 for _ in handle) - 1


def rounded(value: str, digits: int) -> float:
    return round(float(value), digits)


def build_manifest(release_date: str) -> dict:
    for relative in ARTIFACTS:
        if not (ROOT / relative).is_file():
            raise SystemExit(f"Release artifact missing: {relative}")

    sql_rows = read_rows(ROOT / "DOCS" / "sql_reconciliation.csv")
    dax_rows = read_rows(ROOT / "DOCS" / "dax_reconciliation.csv")
    sql_index = {(row["Granularity"], row["Member"]): row for row in sql_rows}
    total = sql_index[("Total", "All")]
    year_2012 = sql_index[("Year", "2012")]
    year_2013 = sql_index[("Year", "2013")]
    usa_au_revenue = sum(
        float(sql_index[("Country", country)]["Revenue"])
        for country in ("US", "AU")
    )
    bicycle = sql_index[("Category", "Bicicleta")]
    context_counts = Counter(row["Granularity"] for row in sql_rows)

    return {
        "schema_version": "1.0.0",
        "project": "financial-performance-dashboard-powerbi",
        "release": {
            "stage": "FIN-C3",
            "date": release_date,
            "status": "verified-local",
        },
        "source": {
            "name": "Microsoft AdventureWorksDW2019",
            "fact_table": "FactInternetSales",
            "snapshot_rows": source_count(ROOT / "DATA" / "financial_sql_input.csv.gz"),
            "order_date_min": "2010-12-29",
            "order_date_max": "2014-01-28",
            "partial_years": [2010, 2014],
            "sql_input_kind": "non-PII analytical projection exported from the embedded PBIX snapshot",
        },
        "model_contract": {
            "active_date_path": "FactInternetSales[OrderDateKey] -> DimDate[DateKey]",
            "measure_count": 35,
            "page_count": 4,
            "sql_dax_contexts": len(sql_rows),
            "context_counts": dict(sorted(context_counts.items())),
            "dax_evidence_rows": len(dax_rows),
        },
        "dashboard_contract": {
            "canvas": "1280x720",
            "capture": "1920x1080",
            "navigation_pages": 4,
            "executive_kpi_cards": 4,
            "driver_kpi_cards": 4,
            "visible_country_maps": 1,
            "visible_gauges": 0,
            "design_stage": "FIN-C2/C3",
        },
        "tolerances": {
            "money_absolute": 0.01,
            "ratio_absolute": 1e-10,
        },
        "kpi_contract": {
            "total": {
                "revenue": rounded(total["Revenue"], 2),
                "cogs": rounded(total["COGS"], 2),
                "shipping": rounded(total["Shipping"], 2),
                "tax": rounded(total["Tax"], 2),
                "gross_profit": rounded(total["GrossProfit"], 2),
                "net_profit": rounded(total["NetProfit"], 2),
                "gross_margin": rounded(total["GrossMargin"], 10),
                "net_margin": rounded(total["NetMargin"], 10),
            },
            "year_2013": {
                "revenue": rounded(year_2013["Revenue"], 2),
                "revenue_share": round(float(year_2013["Revenue"]) / float(total["Revenue"]), 10),
                "growth_vs_2012": round(
                    float(year_2013["Revenue"]) / float(year_2012["Revenue"]) - 1,
                    10,
                ),
                "gross_margin": rounded(year_2013["GrossMargin"], 10),
                "net_margin": rounded(year_2013["NetMargin"], 10),
            },
            "concentration": {
                "usa_plus_australia_revenue_share": round(
                    usa_au_revenue / float(total["Revenue"]), 10
                ),
                "bicycle_revenue_share": round(
                    float(bicycle["Revenue"]) / float(total["Revenue"]), 10
                ),
            },
        },
        "toolchain": {
            "power_bi_desktop": "2.156.951.0",
            "pbi_tools_core": "1.2.0",
            "python": "3.12",
            "sql_engine": "Python sqlite3 / SQLite",
            "pbit_linux_asset_sha256": "ac3a3434f837e49fab1ba69a29cac78b3fb11fc1476c91a7ee87a85ef0131d5e",
        },
        "artifacts": {
            relative: {
                "bytes": (ROOT / relative).stat().st_size,
                "sha256": sha256(ROOT / relative),
            }
            for relative in ARTIFACTS
        },
        "expected_variations": [
            "KPI changes require matching SQL and DAX evidence plus a release note.",
            "Source snapshot or row-count changes require an explicit data refresh decision.",
            "PBIX and PBIT hashes may change after model, layout, data, or Desktop version changes.",
            "Screenshot and PDF hashes may change after a verified visual render or tool update.",
            "Partial-period limitations and the OrderDateKey contract must remain visible.",
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--release-date")
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.check:
        if not args.output.is_file():
            raise SystemExit(f"Release manifest missing: {args.output}")
        actual = json.loads(args.output.read_text(encoding="utf-8-sig"))
        release_date = actual.get("release", {}).get("date")
        if not release_date:
            raise SystemExit("Release manifest date is missing")
        expected = build_manifest(release_date)
        if actual != expected:
            raise SystemExit(
                "Release manifest drift detected; rebuild with "
                f"--release-date {release_date}"
            )
        print("FIN-C3 release manifest validation PASSED")
        return 0

    if not args.release_date:
        raise SystemExit("--release-date is required when writing the manifest")
    manifest = build_manifest(args.release_date)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"FIN-C3 release manifest built: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Fail-fast validation for the Financial Power BI FIN-I1 to FIN-I3 scope."""

from __future__ import annotations

import csv
import json
import math
import re
import struct
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "Financial_Report"
MODEL = PROJECT / "Model"
REPORT = PROJECT / "Report"
EVIDENCE = ROOT / "DOCS" / "dax_reconciliation.csv"

EXPECTED_GRANULARITIES = {
    "Total": 1,
    "Year": 5,
    "Country": 6,
    "State": 53,
    "Category": 3,
}

EXPECTED_PAGES = {
    "000_Home": "Executive Overview",
    "001_Reporte Financiero": "Drivers de margen y LY",
    "002_Detalle USA": "Geographic Drill-down",
    "003_Ayuda": "Definiciones y fuentes",
}

EXPECTED_IMAGES = (
    "executive_overview.png",
    "overview.png",
    "usa_detailed.png",
    "glossary.png",
)

REQUIRED_CSV_COLUMNS = {
    "Granularity", "Member", "Revenue", "COGS", "Shipping", "Tax",
    "GrossProfit", "NetProfit", "GrossMargin", "NetMargin", "RevenueLY",
    "RevenueDeltaLY", "RevenueDeltaLYPct", "GrossMarginDeltaLY",
    "NetMarginDeltaLY", "GrossResidual", "NetResidual",
    "GrossMarginResidual", "NetMarginResidual",
}

REQUIRED_MEASURES = {
    "Cantidad vendida", "Clientes únicos", "COGS", "Costo Total Envios",
    "Costo Total + Envíos", "Impuestos", "Ingresos", "Utilidad bruta",
    "Utilidad neta", "% Margen Bruto", "Operaciones", "Ingresos Acumulados",
    "COGS PA", "% Margen Bruto PA", "% Margen Neto", "Ingresos PA",
    "Ratio Costo Operacional %", "Coste LY", "KPI_Grafico", "Ingresos YTD",
    "Ingresos YTD LY", "Ratio Costo Operacional % LY", "Margen Bruto % LY",
    "Margen Neto % LY", "COGS %", "COGS % LY", "Costos totales",
    "Ingresos vs LY", "Ingresos vs LY %", "Margen bruto vs LY pp",
    "Margen neto vs LY pp", "Reconciliación utilidad bruta",
    "Reconciliación utilidad neta", "Reconciliación margen bruto",
    "Reconciliación margen neto",
}


def close(left: float, right: float, *, atol: float = 1e-6) -> bool:
    return math.isclose(left, right, rel_tol=1e-12, abs_tol=atol)


def number(row: dict[str, str], name: str) -> float:
    raw = row[name].strip()
    return float(raw) if raw else math.nan


def validate_evidence(errors: list[str]) -> None:
    if not EVIDENCE.is_file():
        errors.append("DOCS/dax_reconciliation.csv is missing")
        return

    with EVIDENCE.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        columns = set(reader.fieldnames or ())

    missing = REQUIRED_CSV_COLUMNS - columns
    if missing:
        errors.append(f"Reconciliation CSV columns missing: {sorted(missing)}")
        return

    counts = Counter(row["Granularity"] for row in rows)
    if counts != Counter(EXPECTED_GRANULARITIES):
        errors.append(f"Unexpected reconciliation coverage: {dict(counts)}")
    if len(rows) != 68:
        errors.append(f"Expected 68 reconciliation rows; found {len(rows)}")

    for row in rows:
        label = f"{row['Granularity']}={row['Member']}"
        revenue = number(row, "Revenue")
        cogs = number(row, "COGS")
        shipping = number(row, "Shipping")
        tax = number(row, "Tax")
        gross_profit = number(row, "GrossProfit")
        net_profit = number(row, "NetProfit")
        gross_margin = number(row, "GrossMargin")
        net_margin = number(row, "NetMargin")

        checks = (
            ("gross profit", gross_profit, revenue - cogs),
            ("net profit", net_profit, revenue - cogs - shipping - tax),
            ("gross margin", gross_margin, gross_profit / revenue),
            ("net margin", net_margin, net_profit / revenue),
        )
        for name, actual, expected in checks:
            if not close(actual, expected):
                errors.append(f"{label}: {name} does not reconcile")

        for residual in (
            "GrossResidual", "NetResidual", "GrossMarginResidual", "NetMarginResidual"
        ):
            if abs(number(row, residual)) > 1e-12:
                errors.append(f"{label}: {residual} is not zero")

    year_rows = {
        int(row["Member"]): row for row in rows if row["Granularity"] == "Year"
    }
    for year in sorted(year_rows):
        if year - 1 not in year_rows:
            continue
        actual_ly = number(year_rows[year], "RevenueLY")
        prior_revenue = number(year_rows[year - 1], "Revenue")
        if not close(actual_ly, prior_revenue):
            errors.append(f"Year {year}: RevenueLY does not equal {year - 1} revenue")

    for granularity in ("State", "Category"):
        margins = {
            round(number(row, "GrossMargin"), 8)
            for row in rows
            if row["Granularity"] == granularity
        }
        if len(margins) < 2:
            errors.append(f"{granularity} margin results do not respond to row context")


def measure_names(tmdl: str) -> set[str]:
    names: set[str] = set()
    pattern = re.compile(r"^\s*measure\s+(?:'([^']+)'|([^\s=]+))\s*=", re.MULTILINE)
    for quoted, plain in pattern.findall(tmdl):
        names.add(quoted or plain)
    return names


def validate_model(errors: list[str]) -> None:
    relationships_path = MODEL / "relationships.tmdl"
    measures_path = MODEL / "tables" / "Tablas de Medidas.tmdl"
    if not relationships_path.is_file() or not measures_path.is_file():
        errors.append("Required TMDL relationship or measure source is missing")
        return

    relationships = relationships_path.read_text(encoding="utf-8-sig")
    if "fromColumn: FactInternetSales.OrderDateKey" not in relationships:
        errors.append("Active OrderDateKey relationship is missing")
    if "toColumn: DimDate.DateKey" not in relationships:
        errors.append("DimDate DateKey target is missing")
    if "fromColumn: FactInternetSales.DueDateKey" in relationships:
        errors.append("DueDateKey remains connected to the explicit DimDate table")
    if "crossFilteringBehavior: bothDirections" in relationships:
        errors.append("A bidirectional relationship remains in the audited model")

    measures_tmdl = measures_path.read_text(encoding="utf-8-sig")
    names = measure_names(measures_tmdl)
    if len(names) != 35:
        errors.append(f"Expected 35 DAX measures; found {len(names)}")
    missing = REQUIRED_MEASURES - names
    if missing:
        errors.append(f"Required DAX measures missing: {sorted(missing)}")
    for token in ("Ã", "Â", "ðŸ"):
        if token in measures_tmdl:
            errors.append(f"Encoding-corrupted DAX name remains: {token}")

    required_formulas = (
        "[Ingresos] - [COGS]",
        "[Ingresos] - [Costos totales]",
        "[COGS] + [Costo Total Envios] + [Impuestos]",
        "SAMEPERIODLASTYEAR(DimDate[Date])",
        "DATESYTD(DimDate[Date])",
    )
    for formula in required_formulas:
        if formula not in measures_tmdl:
            errors.append(f"Required DAX contract missing: {formula}")


def validate_report(errors: list[str]) -> None:
    sections = REPORT / "sections"
    found = sorted(path.name for path in sections.iterdir() if path.is_dir())
    if found != sorted(EXPECTED_PAGES):
        errors.append(f"Unexpected report-page topology: {found}")
        return

    for folder, display_name in EXPECTED_PAGES.items():
        path = sections / folder / "section.json"
        section = json.loads(path.read_text(encoding="utf-8-sig"))
        if section.get("displayName") != display_name:
            errors.append(
                f"{folder}: expected display name {display_name!r}; "
                f"found {section.get('displayName')!r}"
            )

    source_text = "\n".join(
        path.read_text(encoding="utf-8-sig")
        for path in REPORT.rglob("*.json")
    )
    required_text = (
        "EXECUTIVE OVERVIEW",
        "2013 aportó $16,4 M",
        "Priorizar USA y Australia",
        "96,5% del ingreso",
        "snapshot sólo cubre hasta el 28 de enero",
        "DRIVERS DE MARGEN Y VARIACIÓN LY",
        "GEOGRAPHIC DRILL-DOWN — USA",
        "DEFINICIONES Y FUENTES",
        "OrderDateKey relacionado activamente con DimDate[DateKey]",
        "2010 y 2014 son períodos parciales",
    )
    for token in required_text:
        if token not in source_text:
            errors.append(f"Expected FIN-I3 narrative missing: {token}")


def png_dimensions(path: Path) -> tuple[int, int] | None:
    try:
        with path.open("rb") as handle:
            if handle.read(8) != b"\x89PNG\r\n\x1a\n":
                return None
            length = struct.unpack(">I", handle.read(4))[0]
            if handle.read(4) != b"IHDR" or length < 8:
                return None
            return struct.unpack(">II", handle.read(8))
    except OSError:
        return None


def validate_artifacts(errors: list[str]) -> None:
    for name in ("Financial_Report.pbix", "Financial_Report.pbit"):
        path = ROOT / name
        if not path.is_file() or path.stat().st_size < 1_000_000:
            errors.append(f"Missing or unexpectedly small Power BI artifact: {name}")

    for name in EXPECTED_IMAGES:
        path = ROOT / "Images" / name
        dimensions = png_dimensions(path)
        if dimensions != (1920, 1080):
            errors.append(f"{name}: expected 1920x1080 PNG; found {dimensions}")

    project_text = "\n".join(
        path.read_text(encoding="utf-8-sig")
        for path in PROJECT.rglob("*.*")
        if path.suffix.lower() in {".json", ".tmdl"}
    )
    for private_ref in ("C:\\Users\\", "DESKTOP-VGOI634", "File.Contents("):
        if private_ref in project_text:
            errors.append(f"Private workstation reference remains in source: {private_ref}")

    readme = (ROOT / "README.md").read_text(encoding="utf-8-sig")
    for token in (
        "FIN-I1", "FIN-I2", "FIN-I3", "35-measure", "68 evaluated contexts",
        "OrderDateKey", "Images/executive_overview.png", "dax_reconciliation.csv",
        "native `.pbip`", "2010 and 2014 are partial years",
    ):
        if token not in readme:
            errors.append(f"README evidence missing: {token}")


def main() -> int:
    errors: list[str] = []
    validate_evidence(errors)
    validate_model(errors)
    validate_report(errors)
    validate_artifacts(errors)

    if errors:
        print("FIN-I1 to FIN-I3 validation FAILED:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("FIN-I1 to FIN-I3 validation PASSED")
    print("  - 35 DAX measures and OrderDateKey time path verified")
    print("  - 68 reconciliation contexts passed with zero diagnostic residual")
    print("  - four-page analytical narrative and 1920x1080 previews verified")
    print("  - PBIX, PBIT, TMDL/report source, documentation, and privacy checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

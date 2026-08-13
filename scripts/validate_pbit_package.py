#!/usr/bin/env python3
"""Validate a compiled Power BI template from its package contents."""

from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PBIT = ROOT / "Financial_Report.pbit"
EXPECTED_PAGES = (
    "Executive Overview",
    "Drivers de margen y LY",
    "Geographic Drill-down",
    "Definiciones y fuentes",
)
REQUIRED_PARTS = {
    "Version",
    "Settings",
    "Metadata",
    "DiagramLayout",
    "Report/Layout",
    "DataModelSchema",
    "[Content_Types].xml",
}


def decode_json(package: zipfile.ZipFile, name: str) -> dict:
    return json.loads(package.read(name).decode("utf-16-le"))


def validate_page_contract(sections: list[dict]) -> list[str]:
    """Validate page identity and semantic order independently of JSON array order."""
    errors: list[str] = []
    if len(sections) != len(EXPECTED_PAGES):
        return [f"Expected {len(EXPECTED_PAGES)} compiled pages; found {len(sections)}"]

    ordinals = tuple(section.get("ordinal") for section in sections)
    if any(type(ordinal) is not int for ordinal in ordinals):
        return [f"Compiled report page ordinal missing or invalid: {ordinals}"]

    expected_ordinals = tuple(range(len(EXPECTED_PAGES)))
    if tuple(sorted(ordinals)) != expected_ordinals:
        return [
            "Compiled report page ordinals must be unique and contiguous: "
            f"expected {expected_ordinals}, found {ordinals}"
        ]

    pages = tuple(
        section.get("displayName")
        for section in sorted(sections, key=lambda section: section["ordinal"])
    )
    if pages != EXPECTED_PAGES:
        errors.append(f"Unexpected compiled report pages by ordinal: {pages}")
    return errors


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    if not path.is_file():
        return [f"PBIT missing: {path}"]
    if not zipfile.is_zipfile(path):
        return [f"PBIT is not a ZIP-compatible Power BI package: {path}"]

    with zipfile.ZipFile(path) as package:
        names = set(package.namelist())
        missing = REQUIRED_PARTS - names
        if missing:
            errors.append(f"PBIT package parts missing: {sorted(missing)}")
            return errors
        if "DataModel" in names:
            errors.append("PBIT unexpectedly contains an embedded DataModel payload")

        model = decode_json(package, "DataModelSchema")
        if model.get("compatibilityLevel") != 1606:
            errors.append(f"Unexpected compatibility level: {model.get('compatibilityLevel')}")
        tables = model.get("model", {}).get("tables", [])
        measure_table = next(
            (table for table in tables if table.get("name") == "Tablas de Medidas"), None
        )
        if measure_table is None:
            errors.append("Tablas de Medidas missing from compiled model")
        else:
            measures = measure_table.get("measures", [])
            if len(measures) != 35:
                errors.append(f"Expected 35 compiled measures; found {len(measures)}")
            by_name = {measure.get("name"): measure for measure in measures}
            expected_formulas = {
                "Ingresos": "SUM(FactInternetSales[SalesAmount])",
                "Utilidad bruta": "[Ingresos] - [COGS]",
                "Utilidad neta": "[Ingresos] - [Costos totales]",
                "Costos totales": "[COGS] + [Costo Total Envios] + [Impuestos]",
                "Ingresos YTD": "DATESYTD(DimDate[Date])",
                "Ingresos PA": "SAMEPERIODLASTYEAR(DimDate[Date])",
            }
            for name, formula in expected_formulas.items():
                measure = by_name.get(name)
                if measure is None or formula not in measure.get("expression", ""):
                    errors.append(f"Compiled DAX contract missing: {name} -> {formula}")

        relationships = model.get("model", {}).get("relationships", [])
        explicit_date = [
            relationship
            for relationship in relationships
            if relationship.get("toTable") == "DimDate"
            and relationship.get("toColumn") == "DateKey"
        ]
        if len(explicit_date) != 1:
            errors.append(f"Expected one explicit DimDate relationship; found {len(explicit_date)}")
        elif explicit_date[0].get("fromColumn") != "OrderDateKey":
            errors.append(
                "Compiled explicit date relationship does not use FactInternetSales[OrderDateKey]"
            )
        if any(
            relationship.get("crossFilteringBehavior") == "bothDirections"
            for relationship in relationships
        ):
            errors.append("Compiled model retains a bidirectional relationship")

        report = decode_json(package, "Report/Layout")
        errors.extend(validate_page_contract(report.get("sections", [])))
        serialized_report = json.dumps(report, ensure_ascii=False)
        for token in (
            "2013 aportó $16,4 M",
            "Priorizar USA y Australia",
            "GEOGRAPHIC DRILL-DOWN — USA",
            "OrderDateKey relacionado activamente con DimDate[DateKey]",
        ):
            if token not in serialized_report:
                errors.append(f"Compiled report narrative missing: {token}")

        serialized_model = json.dumps(model, ensure_ascii=False)
        for private_ref in ("C:\\Users\\", "DESKTOP-VGOI634", "File.Contents("):
            if private_ref in serialized_model or private_ref in serialized_report:
                errors.append(f"Private workstation reference in compiled PBIT: {private_ref}")

    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("pbit", nargs="?", type=Path, default=DEFAULT_PBIT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    path = args.pbit.resolve()
    errors = validate(path)
    if errors:
        print("Compiled PBIT validation FAILED:")
        for error in errors:
            print(f"  - {error}")
        return 1
    print("Compiled PBIT validation PASSED")
    print("  - package structure and data-free template contract verified")
    print("  - 35 measures and OrderDateKey relationship verified")
    print("  - four report pages and executive narrative verified")
    print("  - private workstation references absent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

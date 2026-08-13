#!/usr/bin/env python3
"""Fail-fast validation for the Financial Power BI FIN-S1 to FIN-S3 scope."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "Financial_Report"
REPORT = PROJECT / "Report"

EXPECTED_HIDDEN = {
    "000_Home": {
        "06000_image (291c2)", "07000_image (9eab8)", "08000_image (a2c99)",
        "09000_image (16cc0)", "10000_image (6a55f)", "12000_image (f8239)",
        "14000_image (a7b49)", "17002_shape (00abd)",
    },
    "001_Reporte Financiero": {
        "00000_image (3bd6f)", "10000_image (37104)", "11000_image (0592e)",
        "14000_textbox (21c99)", "15000_image (66860)", "17011_image (be4d2)",
        "17012_image (cd1a8)", "17013_image (10c6b)", "17014_image (35989)",
    },
    "002_Detalle USA": {
        "02000_image (ca600)", "05000_shape (e7799)", "08000_image (ecc5a)", "09000_image (19b46)",
        "10000_image (99e88)", "14000_image (de450)",
    },
}

BANNED_TEXT = (
    "COGS % VS LI", "C.O.G.S.", "DESKTOP-VGOI634", "C:\\Users\\", "File.Contents(", "📦", "💰", "📊", "🚚",
    "📉", "⚖️", "📈", "💵", "🔄", "👉", "😊", "ℹ️",
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def walk(value: Any, path: tuple[str, ...] = ()) -> Iterable[tuple[tuple[str, ...], Any]]:
    yield path, value
    if isinstance(value, dict):
        for key, child in value.items():
            yield from walk(child, path + (key,))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk(child, path + (str(index),))


def literal_value(value: Any) -> str | None:
    try:
        return value["expr"]["Literal"]["Value"]
    except (KeyError, TypeError):
        return None


def validate_us_filter(errors: list[str]) -> None:
    path = REPORT / "sections" / "002_Detalle USA" / "filters.json"
    filters = load_json(path)
    if len(filters) != 1:
        errors.append(f"USA page must have exactly one page filter; found {len(filters)}")
        return
    serialized = json.dumps(filters, ensure_ascii=False)
    required = ('"Entity": "DimCustomer"', '"Property": "CountryRegionCode"', '"Value": "\'US\'"')
    for token in required:
        if token not in serialized:
            errors.append(f"USA page filter is missing {token}")
    for code in ("AU", "CA", "DE", "FR", "GB"):
        if f'"Value": "\'{code}\'"' in serialized:
            errors.append(f"USA page filter unexpectedly includes {code}")

    usa_root = REPORT / "sections" / "002_Detalle USA"
    usa_queries = "\n".join(p.read_text(encoding="utf-8-sig") for p in usa_root.rglob("query.json"))
    if '"Entity": "DimCustomer"' not in usa_queries or '"Property": "StateProvinceName"' not in usa_queries:
        errors.append("USA visuals are not bound to the effective DimCustomer geography fields")
    for code in ("AU", "CA", "DE", "FR", "GB"):
        if f'"Value": "\'{code}\'"' in usa_queries:
            errors.append(f"USA visual query hard-codes non-US scope: {code}")


def validate_json_and_style(errors: list[str]) -> None:
    json_files = sorted(REPORT.rglob("*.json"))
    if not json_files:
        errors.append("No extracted report JSON files found")
        return

    for path in json_files:
        try:
            value = load_json(path)
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"Invalid JSON: {path.relative_to(ROOT)} ({exc})")
            continue

        if path.name not in {"config.json", "dataTransforms.json"}:
            continue
        visual_type = value.get("singleVisual", {}).get("visualType") if isinstance(value, dict) else None
        for json_path, child in walk(value):
            key = json_path[-1] if json_path else ""
            if key.lower().endswith("fontfamily"):
                if isinstance(child, str) and child != "Segoe UI":
                    errors.append(f"Non-standard font in {path.relative_to(ROOT)}: {child}")
                elif isinstance(child, dict) and literal_value(child) != "'''Segoe UI'''":
                    errors.append(f"Non-standard font expression in {path.relative_to(ROOT)}")
            if visual_type != "image" and key == "image" and isinstance(child, dict):
                errors.append(f"Decorative plot image remains in {path.relative_to(ROOT)}")
            if any(part.lower() in {"shadow", "dropshadow", "glow"} for part in json_path[:-1]) and key == "show":
                enabled = child is True or literal_value(child) == "true"
                if enabled:
                    errors.append(f"Enabled shadow/glow remains in {path.relative_to(ROOT)}")


def validate_hidden_visuals(errors: list[str]) -> None:
    for page, visuals in EXPECTED_HIDDEN.items():
        for visual in visuals:
            path = REPORT / "sections" / page / "visualContainers" / visual / "config.json"
            if not path.is_file():
                errors.append(f"Expected visual missing: {path.relative_to(ROOT)}")
                continue
            if load_json(path).get("singleVisual", {}).get("isHidden") is not True:
                errors.append(f"Decorative visual is not hidden: {path.relative_to(ROOT)}")
                continue
            config = load_json(path)
            positions = [layout.get("position", {}) for layout in config.get("layouts", [])]
            if not positions or any(position.get("x", 0) > -9000 or position.get("y", 0) > -9000 for position in positions):
                errors.append(f"Decorative visual remains on-canvas: {path.relative_to(ROOT)}")
            container = load_json(path.with_name("visualContainer.json"))
            if container.get("x", 0) > -9000 or container.get("y", 0) > -9000:
                errors.append(f"Decorative visual container remains on-canvas: {path.relative_to(ROOT)}")


def validate_content(errors: list[str]) -> None:
    source_text = "\n".join(p.read_text(encoding="utf-8-sig") for p in PROJECT.rglob("*.*") if p.suffix.lower() in {".json", ".tmdl"})
    for banned in BANNED_TEXT:
        if banned in source_text:
            errors.append(f"Banned or inconsistent report text remains: {banned}")
    for expected in (
        "EXECUTIVE OVERVIEW", "2010–2014 | ADVENTUREWORKS SAMPLE",
        "DRIVERS DE MARGEN Y VARIACIÓN LY", "GEOGRAPHIC DRILL-DOWN — USA",
        "DEFINICIONES Y FUENTES",
        "Ingresos − costos totales.", "SAMEPERIODLASTYEAR",
    ):
        if expected not in source_text:
            errors.append(f"Expected FIN-S3 content missing: {expected}")
    if r"localhost\SQLEXPRESS" not in source_text:
        errors.append("The model source is not configured with the documented generic SQL Server host")
    dim_customer = (PROJECT / "Model" / "tables" / "DimCustomer.tmdl").read_text(encoding="utf-8-sig")
    for expected in ("Sql.Databases", "AdventureWorksDW2019", "dbo_DimCustomer", '"CountryRegionCode"'):
        if expected not in dim_customer:
            errors.append(f"Refreshable DimCustomer source is missing: {expected}")


def validate_readme(errors: list[str]) -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8-sig")
    required = (
        "AdventureWorksDW2019", "learn.microsoft.com", "2010-12-29", "2014-01-28",
        "60,398", "reporting currency", "millions", "Images/overview.png",
        "Images/executive_overview.png", "Images/usa_detailed.png", "Images/glossary.png", "Limitations",
        "What each page answers", "FIN-S1", "FIN-S2", "FIN-S3",
    )
    for token in required:
        if token not in readme:
            errors.append(f"README is missing required documentation: {token}")


def main() -> int:
    errors: list[str] = []
    if not (PROJECT / ".pbixproj.json").is_file():
        errors.append("Financial_Report/.pbixproj.json is missing")
    pages = sorted(p.name for p in (REPORT / "sections").iterdir() if p.is_dir()) if (REPORT / "sections").is_dir() else []
    if pages != ["000_Home", "001_Reporte Financiero", "002_Detalle USA", "003_Ayuda"]:
        errors.append(f"Unexpected report pages: {pages}")

    if not errors:
        validate_us_filter(errors)
        validate_json_and_style(errors)
        validate_hidden_visuals(errors)
        validate_content(errors)
        validate_readme(errors)

    if errors:
        print("FIN-S1 to FIN-S3 validation FAILED:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("FIN-S1 to FIN-S3 validation PASSED")
    print("  - USA page locked to DimCustomer[CountryRegionCode] = US")
    print("  - four-page structure and cleaned report JSON verified")
    print("  - visual style, glossary, source privacy, and README evidence verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

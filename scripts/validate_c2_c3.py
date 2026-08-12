#!/usr/bin/env python3
"""Fail-fast verification for the FIN-C2/C3 dashboard redesign."""

from __future__ import annotations

import json
import struct
from collections import Counter
from pathlib import Path
from typing import Any
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "Financial_Report" / "Report"
SECTIONS = REPORT / "sections"

PAGES = {
    "home": "000_Home",
    "drivers": "001_Reporte Financiero",
    "usa": "002_Detalle USA",
    "help": "003_Ayuda",
}

PAGE_IDS = {
    key: json.loads((SECTIONS / folder / "section.json").read_text(encoding="utf-8-sig"))["name"]
    for key, folder in PAGES.items()
}

NAV_POSITIONS = {
    "home": (796, 24, 108, 36),
    "drivers": (912, 24, 108, 36),
    "usa": (1028, 24, 108, 36),
    "help": (1144, 24, 108, 36),
}


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def literal(value: Any) -> Any:
    try:
        return value["expr"]["Literal"]["Value"]
    except (KeyError, TypeError):
        return None


def visual_config(page: str, folder: str) -> dict[str, Any]:
    return load(SECTIONS / PAGES[page] / "visualContainers" / folder / "config.json")


def position(config: dict[str, Any]) -> dict[str, Any]:
    return config.get("layouts", [{}])[0].get("position", {})


def is_visible(config: dict[str, Any]) -> bool:
    pos = position(config)
    return config.get("singleVisual", {}).get("isHidden") is not True and pos.get("x", -1) >= 0 and pos.get("y", -1) >= 0


def alt_text(config: dict[str, Any]) -> str | None:
    for item in config.get("singleVisual", {}).get("vcObjects", {}).get("general", []):
        value = literal(item.get("properties", {}).get("altText"))
        if isinstance(value, str):
            return value.strip("'")
    return None


def validate_shell(errors: list[str]) -> None:
    for page_key, folder in PAGES.items():
        root = SECTIONS / folder / "visualContainers"
        for required in ("canvas", "header", "header_accent", "page_title", "page_subtitle"):
            path = root / f"c2c3_{required}" / "config.json"
            if not path.is_file() or not is_visible(load(path)):
                errors.append(f"{page_key}: missing visible C2/C3 shell visual {required}")

        for target, expected in NAV_POSITIONS.items():
            path = root / f"c2c3_nav_{target}" / "config.json"
            if not path.is_file():
                errors.append(f"{page_key}: navigation button missing for {target}")
                continue
            config = load(path)
            pos = position(config)
            actual = tuple(round(float(pos.get(key, -1))) for key in ("x", "y", "width", "height"))
            if actual != expected:
                errors.append(f"{page_key}: {target} navigation position {actual}, expected {expected}")
            links = config["singleVisual"].get("vcObjects", {}).get("visualLink", [])
            destination = None
            if links:
                destination = literal(links[0].get("properties", {}).get("navigationSection"))
            if destination != f"'{PAGE_IDS[target]}'":
                errors.append(f"{page_key}: {target} navigation points to {destination!r}")
            if not alt_text(config):
                errors.append(f"{page_key}: {target} navigation has no alt text")


def validate_fit_and_accessibility(errors: list[str]) -> None:
    for page_key, folder in PAGES.items():
        root = SECTIONS / folder / "visualContainers"
        for visual in root.iterdir():
            if not visual.is_dir() or not (visual / "config.json").is_file():
                continue
            config = load(visual / "config.json")
            if not is_visible(config):
                continue
            pos = position(config)
            right = float(pos.get("x", 0)) + float(pos.get("width", 0))
            bottom = float(pos.get("y", 0)) + float(pos.get("height", 0))
            if right > 1280.01 or bottom > 720.01:
                errors.append(f"{page_key}: {visual.name} exceeds the 1280x720 canvas")
            visual_type = config.get("singleVisual", {}).get("visualType")
            if visual_type != "shape" and not alt_text(config):
                errors.append(f"{page_key}: visible {visual.name} has no alt text")


def visible_type_counts(page_key: str) -> Counter[str]:
    counts: Counter[str] = Counter()
    root = SECTIONS / PAGES[page_key] / "visualContainers"
    for visual in root.iterdir():
        if not visual.is_dir() or not (visual / "config.json").is_file():
            continue
        config = load(visual / "config.json")
        if is_visible(config):
            counts[config.get("singleVisual", {}).get("visualType", "unknown")] += 1
    return counts


def validate_visual_choices(errors: list[str]) -> None:
    home = visible_type_counts("home")
    if home["card"] != 4 or home["clusteredColumnChart"] != 1:
        errors.append(f"home: expected four cards and one trend chart; found {dict(home)}")

    drivers = visible_type_counts("drivers")
    expected = {"card": 4, "clusteredColumnChart": 1, "filledMap": 1, "gauge": 0}
    for visual_type, count in expected.items():
        if drivers[visual_type] != count:
            errors.append(f"drivers: expected {count} visible {visual_type}; found {drivers[visual_type]}")

    usa = visible_type_counts("usa")
    for visual_type in ("slicer", "pivotTable", "scatterChart", "lineChart"):
        if usa[visual_type] != 1:
            errors.append(f"usa: expected one visible {visual_type}; found {usa[visual_type]}")

    help_counts = visible_type_counts("help")
    if any(help_counts[item] for item in ("gauge", "filledMap", "scatterChart", "lineChart")):
        errors.append(f"help: definitions page contains an analytical chart: {dict(help_counts)}")

    driver_root = SECTIONS / PAGES["drivers"] / "visualContainers"
    for folder in (
        "08000_Ingresos por País",
        "09000_Ingresos por País",
        "17003_Ratio Costo Operacional vs LY",
        "17005_% Margen Neto VS LY",
        "17006_% Margen Bruto VS LY",
        "17007_COGS % VS LI",
    ):
        if is_visible(load(driver_root / folder / "config.json")):
            errors.append(f"drivers: retired redundant visual remains visible: {folder}")

    matrix = visual_config("usa", "01000_pivotTable (61544)")["singleVisual"]["projections"]
    expected_values = {
        "Tablas de Medidas.Ingresos",
        "Tablas de Medidas.Utilidad neta",
        "Tablas de Medidas.Utilidad bruta",
        "Tablas de Medidas.% Margen Bruto",
        "Tablas de Medidas.% Margen Neto",
        "Tablas de Medidas.COGS",
        "Tablas de Medidas.Costo Total Envios",
    }
    actual_values = {item["queryRef"] for item in matrix.get("Values", [])}
    if actual_values != expected_values:
        errors.append("usa: detailed matrix source and embedded snapshot contract differ")
    rows = [item.get("queryRef") for item in matrix.get("Rows", [])]
    if rows != ["DimCustomer.StateProvinceName"] or matrix.get("Columns"):
        errors.append("usa: matrix must use state as its only hierarchy and no nested columns")

    scatter = visual_config("usa", "11000_Ingresos VS %Margen Bruto por Ciudad")
    labels = scatter["singleVisual"].get("objects", {}).get("categoryLabels", [])
    if not labels or literal(labels[0].get("properties", {}).get("show")) != "false":
        errors.append("usa: scatter labels must remain off to prevent overlap")


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


def validate_evidence(errors: list[str]) -> None:
    for name in ("executive_overview.png", "overview.png", "usa_detailed.png", "glossary.png"):
        dimensions = png_dimensions(ROOT / "Images" / name)
        if dimensions != (1920, 1080):
            errors.append(f"{name}: expected 1920x1080; found {dimensions}")

    source = "\n".join(path.read_text(encoding="utf-8-sig") for path in REPORT.rglob("*.json"))
    for token in (
        "EXECUTIVE OVERVIEW",
        "RESULTADO CLAVE",
        "ACCIÓN RECOMENDADA",
        "LECTURA RESPONSABLE",
        "ALCANCE FIJO  ·  USA",
        "Reproducibilidad y control de calidad",
    ):
        if token not in source:
            errors.append(f"C2/C3 narrative token missing: {token}")

    readme = (ROOT / "README.md").read_text(encoding="utf-8-sig")
    for token in ("FIN-C2", "FIN-C3", "DOCS/c2_c3_verification.md", "consistent four-page navigation"):
        if token not in readme:
            errors.append(f"README C2/C3 evidence missing: {token}")


def artifact_layout(path: Path) -> dict[str, Any]:
    with ZipFile(path) as package:
        raw = package.read("Report/Layout")
    for encoding in ("utf-16-le", "utf-8-sig", "utf-8"):
        try:
            return json.loads(raw.decode(encoding))
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
    raise ValueError(f"Unable to decode Report/Layout from {path.name}")


def validate_distributed_layouts(errors: list[str]) -> None:
    """Verify the source's visible visual contract in both distributed files."""
    source_sections: dict[str, list[dict[str, Any]]] = {}
    for folder in PAGES.values():
        section_root = SECTIONS / folder
        section = load(section_root / "section.json")
        configs: list[dict[str, Any]] = []
        for visual in (section_root / "visualContainers").iterdir():
            config_path = visual / "config.json"
            if not config_path.is_file():
                continue
            config = load(config_path)
            if is_visible(config):
                configs.append(config)
        source_sections[section["name"]] = configs

    for artifact_name in ("Financial_Report.pbix", "Financial_Report.pbit"):
        artifact = ROOT / artifact_name
        try:
            layout = artifact_layout(artifact)
        except (OSError, KeyError, ValueError) as exc:
            errors.append(f"{artifact_name}: report layout unavailable ({exc})")
            continue
        sections = {section["name"]: section for section in layout.get("sections", [])}
        checked = 0
        for section_id, expected_configs in source_sections.items():
            actual_section = sections.get(section_id)
            if actual_section is None:
                errors.append(f"{artifact_name}: missing section {section_id}")
                continue
            actual_by_name = {
                load_config["name"]: load_config
                for item in actual_section.get("visualContainers", [])
                for load_config in [json.loads(item["config"])]
            }
            for expected in expected_configs:
                name = expected["name"]
                actual = actual_by_name.get(name)
                if actual is None:
                    errors.append(f"{artifact_name}: visible visual {name} missing")
                    continue
                checked += 1
                expected_single = expected.get("singleVisual", {})
                actual_single = actual.get("singleVisual", {})
                if expected_single.get("visualType") != actual_single.get("visualType"):
                    errors.append(f"{artifact_name}: visual type drift for {name}")
                if position(expected) != position(actual):
                    errors.append(f"{artifact_name}: position drift for {name}")
                if expected_single.get("projections") != actual_single.get("projections"):
                    errors.append(f"{artifact_name}: projection drift for {name}")
        if checked != 75:
            errors.append(f"{artifact_name}: expected 75 visible source visuals; checked {checked}")


def main() -> int:
    errors: list[str] = []
    validate_shell(errors)
    validate_fit_and_accessibility(errors)
    validate_visual_choices(errors)
    validate_evidence(errors)
    validate_distributed_layouts(errors)

    if errors:
        print("FIN-C2/C3 validation FAILED:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("FIN-C2/C3 validation PASSED")
    print("  - consistent four-page navigation and 1280x720 fit")
    print("  - KPI-first overview, one country map, and no visible gauges")
    print("  - USA analytical views, alt text, and overlap controls verified")
    print("  - source, PBIX, PBIT, and four 1920x1080 captures are aligned")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

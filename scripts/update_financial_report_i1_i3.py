#!/usr/bin/env python3
"""Apply the FIN-I1 to FIN-I3 analytical and narrative layer.

The semantic model is versioned as TMDL. Live PBIX model changes are applied
with apply_live_model_i1.ps1, while this script keeps the extracted report
source and its executive story deterministic and reviewable.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "Financial_Report"
REPORT = PROJECT / "Report"
EVIDENCE = ROOT / "DOCS" / "dax_reconciliation.csv"

PAGE_NAMES = {
    "000_Home": "Executive Overview",
    "001_Reporte Financiero": "Drivers de margen y LY",
    "002_Detalle USA": "Geographic Drill-down",
    "003_Ayuda": "Definiciones y fuentes",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def literal(value: str) -> dict[str, Any]:
    return {"expr": {"Literal": {"Value": value}}}


def load_evidence() -> list[dict[str, str]]:
    if not EVIDENCE.is_file():
        raise SystemExit(f"Reconciliation evidence not found: {EVIDENCE}")
    with EVIDENCE.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def evidence_row(rows: list[dict[str, str]], granularity: str, member: str) -> dict[str, str]:
    try:
        return next(row for row in rows if row["Granularity"] == granularity and row["Member"] == member)
    except StopIteration as exc:
        raise SystemExit(f"Missing evidence row: {granularity} / {member}") from exc


def money_millions(value: float) -> str:
    return f"${value / 1_000_000:.1f} M".replace(".", ",")


def percent(value: float) -> str:
    return f"{value * 100:.1f}%".replace(".", ",")


def set_textbox(
    config: dict[str, Any],
    paragraphs: list[dict[str, Any]],
    *,
    x: float,
    y: float,
    width: float,
    height: float,
) -> None:
    config.setdefault("singleVisual", {})["isHidden"] = False
    for layout in config.get("layouts", []):
        layout.setdefault("position", {}).update({"x": x, "y": y, "width": width, "height": height})
    config["singleVisual"]["objects"]["general"][0]["properties"]["paragraphs"] = paragraphs


def sync_container(config_path: Path, *, x: float, y: float, width: float, height: float) -> None:
    container_path = config_path.with_name("visualContainer.json")
    container = read_json(container_path)
    container.update({"x": x, "y": y, "width": width, "height": height})
    write_json(container_path, container)


def retire_visual(config_path: Path) -> None:
    config = read_json(config_path)
    config.setdefault("singleVisual", {})["isHidden"] = True
    for layout in config.get("layouts", []):
        layout.setdefault("position", {}).update({"x": -10000, "y": -10000, "width": 1, "height": 1})
    write_json(config_path, config)
    sync_container(config_path, x=-10000, y=-10000, width=1, height=1)


def title_paragraph(text: str, size: str = "15pt") -> dict[str, Any]:
    return {
        "textRuns": [
            {
                "value": text,
                "textStyle": {
                    "fontWeight": "bold",
                    "fontFamily": "Segoe UI",
                    "fontSize": size,
                    "color": "#1F4E78",
                },
            }
        ],
        "horizontalTextAlignment": "left",
    }


def body_paragraph(text: str, size: str = "12pt", color: str = "#222222") -> dict[str, Any]:
    return {
        "textRuns": [
            {
                "value": text,
                "textStyle": {"fontFamily": "Segoe UI", "fontSize": size, "color": color},
            }
        ],
        "horizontalTextAlignment": "left",
    }


def set_simple_title(config_path: Path, text: str, *, x: float, width: float, size: str) -> None:
    config = read_json(config_path)
    position = config["layouts"][0]["position"]
    position.update({"x": x, "width": width})
    paragraphs = config["singleVisual"]["objects"]["general"][0]["properties"]["paragraphs"]
    paragraphs[0]["textRuns"][0].update(
        {
            "value": text,
            "textStyle": {
                "fontWeight": "bold",
                "fontFamily": "Segoe UI",
                "fontSize": size,
                "color": "#1F4E78",
            },
        }
    )
    paragraphs[0]["horizontalTextAlignment"] = "center"
    write_json(config_path, config)


def set_button_label(config_path: Path, label: str, alt_text: str) -> None:
    config = read_json(config_path)
    text_items = config["singleVisual"]["objects"].get("text", [])
    for item in text_items:
        properties = item.get("properties", {})
        if "text" in properties:
            properties["text"] = literal(f"'{label}'")
    general = config["singleVisual"].setdefault("vcObjects", {}).setdefault("general", [{"properties": {}}])
    general[0].setdefault("properties", {})["altText"] = literal(f"'{alt_text}'")
    write_json(config_path, config)


def glossary_paragraph(label: str, definition: str) -> dict[str, Any]:
    return {
        "textRuns": [
            {
                "value": f"{label}: ",
                "textStyle": {
                    "fontWeight": "bold",
                    "fontFamily": "Segoe UI",
                    "fontSize": "10pt",
                    "color": "#1F4E78",
                },
            },
            {
                "value": definition,
                "textStyle": {"fontFamily": "Segoe UI", "fontSize": "10pt", "color": "#000000"},
            },
        ]
    }


def rewrite_glossary(config_path: Path) -> None:
    config = read_json(config_path)
    paragraphs = [
        {
            "textRuns": [
                {
                    "value": "DEFINICIONES Y FUENTES",
                    "textStyle": {
                        "fontWeight": "bold",
                        "fontFamily": "Segoe UI",
                        "fontSize": "26pt",
                        "color": "#1F4E78",
                    },
                }
            ],
            "horizontalTextAlignment": "center",
        },
        {
            "textRuns": [
                {
                    "value": "Contrato analítico alineado con el modelo DAX reconciliado.",
                    "textStyle": {"fontFamily": "Segoe UI", "fontSize": "10pt", "color": "#404040"},
                }
            ],
            "horizontalTextAlignment": "center",
        },
        {"textRuns": [{"value": "", "textStyle": {"fontSize": "4pt"}}]},
        glossary_paragraph("Ingresos", "suma de SalesAmount antes de costos, fletes e impuestos."),
        glossary_paragraph("COGS", "suma de TotalProductCost asociada a las ventas."),
        glossary_paragraph("Costos totales", "COGS + costos de envío + impuestos."),
        glossary_paragraph("Utilidad bruta", "Ingresos − COGS."),
        glossary_paragraph("Utilidad neta", "Ingresos − costos totales."),
        glossary_paragraph("Margen bruto", "Utilidad bruta / Ingresos."),
        glossary_paragraph("Margen neto", "Utilidad neta / Ingresos."),
        glossary_paragraph("Ratio de costo operacional", "(COGS + costos de envío) / Ingresos; excluye impuestos."),
        glossary_paragraph("LY (Last Year)", "mismo período del año anterior mediante SAMEPERIODLASTYEAR."),
        glossary_paragraph("Fecha analítica", "OrderDateKey relacionado activamente con DimDate[DateKey]."),
        glossary_paragraph("Fuente", "Microsoft AdventureWorksDW2019, tabla FactInternetSales."),
        glossary_paragraph("Cobertura", "2010-12-29 a 2014-01-28; 2010 y 2014 son períodos parciales."),
        glossary_paragraph("Validación", "identidades verificadas en total, año, país, estado y categoría."),
    ]
    config["singleVisual"]["objects"]["general"][0]["properties"]["paragraphs"] = paragraphs
    write_json(config_path, config)


def update_page_names() -> None:
    for folder, display_name in PAGE_NAMES.items():
        path = REPORT / "sections" / folder / "section.json"
        section = read_json(path)
        section["displayName"] = display_name
        write_json(path, section)


def update_home_story(rows: list[dict[str, str]]) -> None:
    total = evidence_row(rows, "Total", "All")
    year_2013 = evidence_row(rows, "Year", "2013")
    us = evidence_row(rows, "Country", "US")
    au = evidence_row(rows, "Country", "AU")
    bikes = evidence_row(rows, "Category", "Bicicleta")

    total_revenue = float(total["Revenue"])
    year_share = float(year_2013["Revenue"]) / total_revenue
    country_share = (float(us["Revenue"]) + float(au["Revenue"])) / total_revenue
    bike_share = float(bikes["Revenue"]) / total_revenue

    first_path = REPORT / "sections" / "000_Home" / "visualContainers" / "13000_textbox (46ac1)" / "config.json"
    first_config = read_json(first_path)
    first_paragraphs = [
        title_paragraph("RESULTADO CLAVE"),
        body_paragraph(
            f"2013 aportó {money_millions(float(year_2013['Revenue']))} "
            f"({percent(year_share)} del total) y creció "
            f"{percent(float(year_2013['RevenueDeltaLYPct']))} frente a 2012."
        ),
        body_paragraph(
            f"Margen bruto: {percent(float(year_2013['GrossMargin']))} | "
            f"Margen neto: {percent(float(year_2013['NetMargin']))}.",
            size="11pt",
            color="#555555",
        ),
    ]
    set_textbox(first_config, first_paragraphs, x=245, y=290, width=525, height=135)
    write_json(first_path, first_config)
    sync_container(first_path, x=245, y=290, width=525, height=135)

    second_path = REPORT / "sections" / "000_Home" / "visualContainers" / "15000_textbox (b4ec3)" / "config.json"
    second_config = read_json(second_path)
    second_paragraphs = [
        title_paragraph("ACCIÓN RECOMENDADA"),
        body_paragraph(
            f"Priorizar USA y Australia ({percent(country_share)} del ingreso) y proteger el mix de bicicletas "
            f"({percent(bike_share)} del ingreso)."
        ),
        body_paragraph(
            "No interpretar 2014 como caída anual: el snapshot sólo cubre hasta el 28 de enero.",
            size="11pt",
            color="#C00000",
        ),
    ]
    set_textbox(second_config, second_paragraphs, x=245, y=445, width=525, height=155)
    write_json(second_path, second_config)
    sync_container(second_path, x=245, y=445, width=525, height=155)

    info_path = REPORT / "sections" / "000_Home" / "visualContainers" / "17001_textbox (c0499)" / "config.json"
    info_config = read_json(info_path)
    info_paragraphs = [title_paragraph("Definiciones", "9pt")]
    set_textbox(info_config, info_paragraphs, x=1085, y=670, width=105, height=38)
    write_json(info_path, info_config)
    sync_container(info_path, x=1085, y=670, width=105, height=38)


def update_navigation() -> None:
    buttons = {
        "000_Home/visualContainers/04000_asd/config.json": ("Drill-down geográfico", "Abrir el análisis geográfico de USA."),
        "000_Home/visualContainers/05000_asd/config.json": ("Drivers de margen", "Abrir los drivers de margen y variación LY."),
        "001_Reporte Financiero/visualContainers/02000_/config.json": ("Resumen ejecutivo", "Volver al resumen ejecutivo."),
        "001_Reporte Financiero/visualContainers/03000_asd/config.json": ("Drill-down geográfico", "Abrir el análisis geográfico de USA."),
        "001_Reporte Financiero/visualContainers/17015_asd/config.json": ("Definiciones", "Abrir definiciones, fuentes y cobertura."),
        "002_Detalle USA/visualContainers/06000_/config.json": ("Resumen ejecutivo", "Volver al resumen ejecutivo."),
        "002_Detalle USA/visualContainers/07000_asd/config.json": ("Drivers de margen", "Volver a los drivers de margen y LY."),
    }
    for relative, (label, alt_text) in buttons.items():
        set_button_label(REPORT / "sections" / relative, label, alt_text)


def validate_model_contract() -> None:
    relationships = (PROJECT / "Model" / "relationships.tmdl").read_text(encoding="utf-8-sig")
    if "fromColumn: FactInternetSales.OrderDateKey\n\ttoColumn: DimDate.DateKey" not in relationships:
        raise SystemExit("FIN-I1 OrderDateKey relationship is missing from TMDL")
    measures = (PROJECT / "Model" / "tables" / "Tablas de Medidas.tmdl").read_text(encoding="utf-8-sig")
    required = (
        "measure 'Costos totales'",
        "measure 'Ingresos vs LY %'",
        "measure 'Reconciliación utilidad bruta'",
        "measure 'Reconciliación margen neto'",
    )
    for token in required:
        if token not in measures:
            raise SystemExit(f"FIN-I1 measure missing from TMDL: {token}")
    if "Ã" in measures:
        raise SystemExit("Mojibake remains in the measure catalog")


def main() -> int:
    rows = load_evidence()
    validate_model_contract()
    update_page_names()
    update_home_story(rows)
    update_navigation()

    set_simple_title(
        REPORT / "sections" / "000_Home" / "visualContainers" / "11000_textbox (0c686)" / "config.json",
        "EXECUTIVE OVERVIEW",
        x=225,
        width=650,
        size="24pt",
    )
    retire_visual(
        REPORT / "sections" / "000_Home" / "visualContainers" / "17002_shape (00abd)" / "config.json"
    )
    set_simple_title(
        REPORT / "sections" / "001_Reporte Financiero" / "visualContainers" / "12000_textbox (90cda)" / "config.json",
        "DRIVERS DE MARGEN Y VARIACIÓN LY",
        x=250,
        width=440,
        size="18pt",
    )
    set_simple_title(
        REPORT / "sections" / "002_Detalle USA" / "visualContainers" / "03000_textbox (d318a)" / "config.json",
        "GEOGRAPHIC DRILL-DOWN — USA",
        x=250,
        width=410,
        size="18pt",
    )
    rewrite_glossary(
        REPORT / "sections" / "003_Ayuda" / "visualContainers" / "00000_textbox (dcd7d)" / "config.json"
    )

    for path in (PROJECT / "Model").rglob("*.tmdl"):
        text = "\n".join(line.rstrip() for line in path.read_text(encoding="utf-8-sig").splitlines()).rstrip() + "\n"
        path.write_text(text, encoding="utf-8")

    print("FIN-I1 to FIN-I3 source transformations applied successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

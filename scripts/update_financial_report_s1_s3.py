#!/usr/bin/env python3
"""Apply the audited FIN-S1 to FIN-S3 cleanup to the extracted Power BI source.

The script is intentionally idempotent: rerunning it produces the same report source.
It only uses Python's standard library and never modifies the embedded dataset.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "Financial_Report"
REPORT = PROJECT / "Report"

DECORATIVE_VISUALS = {
    "000_Home": {
        "06000_image (291c2)",
        "07000_image (9eab8)",
        "08000_image (a2c99)",
        "09000_image (16cc0)",
        "10000_image (6a55f)",
        "12000_image (f8239)",
        "13000_textbox (46ac1)",
        "14000_image (a7b49)",
        "15000_textbox (b4ec3)",
    },
    "001_Reporte Financiero": {
        "00000_image (3bd6f)",
        "10000_image (37104)",
        "11000_image (0592e)",
        "14000_textbox (21c99)",
        "15000_image (66860)",
        "17011_image (be4d2)",
        "17012_image (cd1a8)",
        "17013_image (10c6b)",
        "17014_image (35989)",
    },
    "002_Detalle USA": {
        "02000_image (ca600)",
        "05000_shape (e7799)",
        "08000_image (ecc5a)",
        "09000_image (19b46)",
        "10000_image (99e88)",
        "14000_image (de450)",
    },
}

TEXT_REPLACEMENTS = {
    "COGS % VS LI": "COGS % vs LY",
    "% Margen Neto VS LY": "% Margen neto vs LY",
    "% Margen Bruto VS LY": "% Margen bruto vs LY",
    "Ingresos VS %Margen Bruto por Ciudad": "Ingresos vs margen bruto por ciudad",
    "Ingresos VS C.O.G.S. por año": "Ingresos vs COGS por año",
    "Ingresos VS Periodo Anterior": "Ingresos vs periodo anterior",
    "G L O B A L": "REPORTE FINANCIERO",
    " U.S.A. ": "DETALLE USA",
    "U.S.A.": "DETALLE USA",
}

COLOR_REPLACEMENTS = {
    "#359e86": "#1F4E78",  # primary navy
    "#41a4ff": "#2F75B5",  # secondary blue
    "#eb9629": "#D97706",  # controlled orange accent
    "#e66c37": "#D97706",
    "#d9b300": "#D97706",
    "#e1c233": "#D97706",
    "#a1343c": "#C00000",  # negative variance
}

EMOJI = ("ℹ️", "ℹ", "😊", "📦", "💰", "📊", "🚚", "📉", "⚖️", "📈", "💵", "🔄", "👉")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def literal(value: str) -> dict[str, Any]:
    return {"expr": {"Literal": {"Value": value}}}


def set_show_false(value: Any) -> None:
    if isinstance(value, dict):
        for key, child in list(value.items()):
            if key == "show":
                if isinstance(child, dict):
                    value[key] = literal("false")
                else:
                    value[key] = False
            else:
                set_show_false(child)
    elif isinstance(value, list):
        for child in value:
            set_show_false(child)


def normalize(value: Any, *, remove_plot_images: bool) -> Any:
    if isinstance(value, str):
        updated = value
        for old, new in TEXT_REPLACEMENTS.items():
            updated = updated.replace(old, new)
        for old, new in COLOR_REPLACEMENTS.items():
            updated = updated.replace(old, new).replace(old.upper(), new)
        for symbol in EMOJI:
            updated = updated.replace(symbol, "")
        return updated

    if isinstance(value, list):
        return [normalize(child, remove_plot_images=remove_plot_images) for child in value]

    if isinstance(value, dict):
        updated: dict[str, Any] = {}
        for key, child in value.items():
            if remove_plot_images and key == "image" and isinstance(child, dict):
                # Non-image visuals only: remove decorative plot-area bitmaps.
                continue
            normalized = normalize(child, remove_plot_images=remove_plot_images)
            if key.lower().endswith("fontfamily"):
                if isinstance(normalized, dict) and "expr" in normalized:
                    normalized = literal("'''Segoe UI'''")
                elif isinstance(normalized, str):
                    normalized = "Segoe UI"
            updated[key] = normalized
            if key.lower() in {"shadow", "dropshadow", "glow"}:
                set_show_false(updated[key])
        return updated

    return value


def style_title(config: dict[str, Any], text: str, font_size: str, x: float, width: float) -> None:
    position = config["layouts"][0]["position"]
    position["x"] = x
    position["width"] = width
    paragraphs = config["singleVisual"]["objects"]["general"][0]["properties"]["paragraphs"]
    run = paragraphs[0]["textRuns"][0]
    run["value"] = text
    run["textStyle"] = {
        "fontWeight": "bold",
        "fontFamily": "Segoe UI",
        "fontSize": font_size,
        "color": "#1F4E78",
    }
    paragraphs[0]["horizontalTextAlignment"] = "center"


def replace_textbox(config: dict[str, Any], text: str, font_size: str, color: str, x: float, width: float) -> None:
    position = config["layouts"][0]["position"]
    position["x"] = x
    position["width"] = width
    config["singleVisual"]["objects"]["general"][0]["properties"]["paragraphs"] = [
        {
            "textRuns": [
                {
                    "value": text,
                    "textStyle": {
                        "fontWeight": "bold",
                        "fontFamily": "Segoe UI",
                        "fontSize": font_size,
                        "color": color,
                    },
                }
            ],
            "horizontalTextAlignment": "center",
        }
    ]


def glossary_paragraph(label: str, definition: str) -> dict[str, Any]:
    return {
        "textRuns": [
            {
                "value": f"{label}: ",
                "textStyle": {"fontWeight": "bold", "fontFamily": "Segoe UI", "fontSize": "11pt", "color": "#1F4E78"},
            },
            {"value": definition, "textStyle": {"fontFamily": "Segoe UI", "fontSize": "11pt", "color": "#000000"}},
        ]
    }


def rewrite_glossary(config: dict[str, Any]) -> None:
    paragraphs = [
        {
            "textRuns": [
                {
                    "value": "AYUDA Y GLOSARIO FINANCIERO",
                    "textStyle": {"fontWeight": "bold", "fontFamily": "Segoe UI", "fontSize": "28pt", "color": "#1F4E78"},
                }
            ],
            "horizontalTextAlignment": "center",
        },
        {
            "textRuns": [
                {
                    "value": "Definiciones alineadas con las medidas DAX del modelo.",
                    "textStyle": {"fontFamily": "Segoe UI", "fontSize": "11pt", "color": "#404040"},
                }
            ],
            "horizontalTextAlignment": "center",
        },
        {"textRuns": [{"value": "", "textStyle": {"fontSize": "5pt"}}]},
        glossary_paragraph("Ingresos", "suma de SalesAmount antes de costos, fletes e impuestos."),
        glossary_paragraph("Ingresos acumulados (YTD)", "ingresos acumulados desde el inicio del año hasta la fecha seleccionada."),
        glossary_paragraph("COGS", "costo directo de los productos vendidos, calculado como suma de TotalProductCost."),
        glossary_paragraph("Costos de envío", "suma del importe Freight asociado a las ventas."),
        glossary_paragraph("Costo total + envíos", "COGS + costos de envío."),
        glossary_paragraph("Utilidad bruta", "Ingresos − COGS."),
        glossary_paragraph("Utilidad neta", "Ingresos − COGS − costos de envío − impuestos."),
        glossary_paragraph("Margen bruto", "Utilidad bruta / Ingresos."),
        glossary_paragraph("Margen neto", "Utilidad neta / Ingresos."),
        glossary_paragraph("Ratio de costo operacional", "(COGS + costos de envío) / Ingresos; un valor menor indica mayor eficiencia de costos."),
        glossary_paragraph("LY (Last Year)", "mismo período del año anterior, calculado con SAMEPERIODLASTYEAR."),
    ]
    config["singleVisual"]["objects"]["general"][0]["properties"]["paragraphs"] = paragraphs


def retire_visual(config_path: Path) -> None:
    """Move a visual outside the 1280x720 canvas while keeping it reversible."""
    config = read_json(config_path)
    config.setdefault("singleVisual", {})["isHidden"] = True
    for layout in config.get("layouts", []):
        position = layout.get("position", {})
        position.update({"x": -10000, "y": -10000, "width": 1, "height": 1})
    write_json(config_path, config)

    container_path = config_path.with_name("visualContainer.json")
    if not container_path.is_file():
        raise SystemExit(f"Expected visual container not found: {container_path}")
    container = read_json(container_path)
    container.update({"x": -10000, "y": -10000, "width": 1, "height": 1})
    write_json(container_path, container)


def make_dim_customer_refreshable() -> None:
    """Replace the workstation-only Excel dependency with AdventureWorks SQL."""
    path = PROJECT / "Model" / "tables" / "DimCustomer.tmdl"
    source = path.read_text(encoding="utf-8-sig")
    if "Excel.Workbook(File.Contents" not in source:
        return

    start = source.index("\tpartition DimCustomer = m")
    end = source.index("\n\tannotation PBI_ResultType", start)
    partition = r'''\tpartition DimCustomer = m
\t\tmode: import
\t\tqueryGroup: Consultas
\t\tsource =
\t\t\t\tlet
\t\t\t\t    Origen = Sql.Databases("localhost\SQLEXPRESS"),
\t\t\t\t    AdventureWorksDW2019 = Origen{[Name="AdventureWorksDW2019"]}[Data],
\t\t\t\t    dbo_DimCustomer = AdventureWorksDW2019{[Schema="dbo",Item="DimCustomer"]}[Data],
\t\t\t\t    #"Columnas seleccionadas" = Table.SelectColumns(dbo_DimCustomer,{"CustomerKey", "GeographyKey", "CustomerAlternateKey", "FirstName", "MiddleName", "LastName", "NameStyle", "BirthDate", "MaritalStatus", "Gender", "EmailAddress", "YearlyIncome", "TotalChildren", "NumberChildrenAtHome", "EnglishEducation", "SpanishEducation", "EnglishOccupation", "SpanishOccupation", "HouseOwnerFlag", "NumberCarsOwned", "AddressLine1", "Phone", "DateFirstPurchase", "CommuteDistance"}),
\t\t\t\t    #"Consultas combinadas" = Table.NestedJoin(#"Columnas seleccionadas", {"GeographyKey"}, DimGeography, {"GeographyKey"}, "DimGeography", JoinKind.LeftOuter),
\t\t\t\t    #"Geografía expandida" = Table.ExpandTableColumn(#"Consultas combinadas", "DimGeography", {"CountryRegionCode", "City", "StateProvinceCode", "StateProvinceName"}, {"CountryRegionCode", "City", "StateProvinceCode", "StateProvinceName"}),
\t\t\t\t    #"Año insertado" = Table.AddColumn(#"Geografía expandida", "Año de Nacimiento", each Date.Year([BirthDate]), Int64.Type),
\t\t\t\t    #"Edad agregada" = Table.AddColumn(#"Año insertado", "Edad", each Año - [Año de Nacimiento], Int64.Type),
\t\t\t\t    #"Rango etario agregado" = Table.AddColumn(#"Edad agregada", "Rango Etario", each if [Edad] < 18 then "Menor de edad" else if [Edad] <= 25 then "Joven Adulto" else if [Edad] <= 60 then "Adulto" else "Mayor", type text),
\t\t\t\t    #"Nombre completo agregado" = Table.AddColumn(#"Rango etario agregado", "Nombre Completo", each Text.Combine({[FirstName], " ", [LastName]}), type text)
\t\t\t\tin
\t\t\t\t    #"Nombre completo agregado"
'''.replace("\\t", "\t")
    path.write_text(source[:start] + partition + source[end:], encoding="utf-8")


def update_report() -> None:
    if not (PROJECT / ".pbixproj.json").is_file() or not REPORT.is_dir():
        raise SystemExit(f"Power BI source not found: {PROJECT}")

    for config_path in REPORT.rglob("config.json"):
        config = read_json(config_path)
        visual_type = config.get("singleVisual", {}).get("visualType") if isinstance(config, dict) else None
        config = normalize(config, remove_plot_images=visual_type not in {None, "image"})
        write_json(config_path, config)

    for transform_path in REPORT.rglob("dataTransforms.json"):
        transform = normalize(read_json(transform_path), remove_plot_images=True)
        write_json(transform_path, transform)

    for page, visual_names in DECORATIVE_VISUALS.items():
        for visual_name in visual_names:
            config_path = REPORT / "sections" / page / "visualContainers" / visual_name / "config.json"
            if not config_path.is_file():
                raise SystemExit(f"Expected visual not found: {config_path}")
            retire_visual(config_path)

    # FIN-S1: USA visuals use DimCustomer geography fields, so the stable page
    # filter must target that effective dimension rather than DimGeography.
    usa_filter_path = REPORT / "sections" / "002_Detalle USA" / "filters.json"
    usa_filters = read_json(usa_filter_path)
    serialized_filters = json.dumps(usa_filters, ensure_ascii=False)
    if "DimGeography" not in serialized_filters and "DimCustomer" not in serialized_filters:
        raise SystemExit("Expected USA country filter entity not found")
    usa_filters = json.loads(serialized_filters.replace("DimGeography", "DimCustomer"))
    write_json(usa_filter_path, usa_filters)

    home_title = REPORT / "sections" / "000_Home" / "visualContainers" / "11000_textbox (0c686)" / "config.json"
    home_title_config = read_json(home_title)
    replace_textbox(home_title_config, "ANÁLISIS Y REPORTE FINANCIERO", "28pt", "#1F4E78", 260.0, 760.0)
    write_json(home_title, home_title_config)

    home_period = REPORT / "sections" / "000_Home" / "visualContainers" / "16000_textbox (a1ebe)" / "config.json"
    home_period_config = read_json(home_period)
    replace_textbox(home_period_config, "2010–2014 | ADVENTUREWORKS SAMPLE", "18pt", "#FFFFFF", 735.0, 520.0)
    write_json(home_period, home_period_config)

    global_title = REPORT / "sections" / "001_Reporte Financiero" / "visualContainers" / "12000_textbox (90cda)" / "config.json"
    global_config = read_json(global_title)
    style_title(global_config, "REPORTE FINANCIERO", "22pt", 250.0, 360.0)
    write_json(global_title, global_config)

    usa_title = REPORT / "sections" / "002_Detalle USA" / "visualContainers" / "03000_textbox (d318a)" / "config.json"
    usa_config = read_json(usa_title)
    style_title(usa_config, "DETALLE USA", "26pt", 260.0, 320.0)
    write_json(usa_title, usa_config)

    usa_slicer = REPORT / "sections" / "002_Detalle USA" / "visualContainers" / "00000_Filtros" / "config.json"
    usa_slicer_config = read_json(usa_slicer)
    title_properties = usa_slicer_config["singleVisual"]["vcObjects"]["title"][0]["properties"]
    title_properties["underline"] = literal("false")
    usa_slicer_config["singleVisual"]["vcObjects"]["background"][0]["properties"]["color"] = {
        "solid": {"color": literal("'#F2F2F2'")}
    }
    usa_slicer_config["singleVisual"]["objects"]["items"][0]["properties"]["background"] = {
        "solid": {"color": literal("'#FFFFFF'")}
    }
    write_json(usa_slicer, usa_slicer_config)

    glossary = REPORT / "sections" / "003_Ayuda" / "visualContainers" / "00000_textbox (dcd7d)" / "config.json"
    glossary_config = read_json(glossary)
    rewrite_glossary(glossary_config)
    write_json(glossary, glossary_config)

    for tmdl_path in (PROJECT / "Model").rglob("*.tmdl"):
        source = tmdl_path.read_text(encoding="utf-8-sig")
        source = source.replace(r"DESKTOP-VGOI634\SQLEXPRESS", r"localhost\SQLEXPRESS")
        source = "\n".join(line.rstrip() for line in source.splitlines()).rstrip() + "\n"
        tmdl_path.write_text(source, encoding="utf-8")

    make_dim_customer_refreshable()


if __name__ == "__main__":
    update_report()
    print("FIN-S1 to FIN-S3 transformations applied successfully.")

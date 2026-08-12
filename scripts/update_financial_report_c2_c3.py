#!/usr/bin/env python3
"""Rebuild the Financial Power BI report for FIN-C2 and FIN-C3.

FIN-C2 replaces the legacy decorative layout with a decision-oriented grid,
consistent page navigation, focused KPI cards, and fewer chart types.
FIN-C3 applies the visual system, accessibility metadata, and final sizing.

The transformation is idempotent. Generated visuals use a ``c2c3_`` prefix;
rerunning the script removes and recreates only those generated containers.
The semantic model and embedded data are never modified.
"""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any


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

SHAPE_TEMPLATE = SECTIONS / PAGES["home"] / "visualContainers" / "00000_shape (d3df0)"
TEXT_TEMPLATE = SECTIONS / PAGES["home"] / "visualContainers" / "13000_textbox (46ac1)"
BUTTON_TEMPLATE = SECTIONS / PAGES["home"] / "visualContainers" / "04000_asd"
CARD_TEMPLATE = (
    SECTIONS
    / PAGES["drivers"]
    / "visualContainers"
    / "17010_Ingresos VS Periodo Anterior"
)
CHART_TEMPLATE = (
    SECTIONS
    / PAGES["drivers"]
    / "visualContainers"
    / "04000_COGS, Utilidad Bruta e Ingresos por Bimestre"
)

COLORS = {
    "navy": "#102A43",
    "navy_2": "#163A5F",
    "blue": "#2F75B5",
    "teal": "#0F8B8D",
    "orange": "#D97706",
    "red": "#C0392B",
    "green": "#198754",
    "ink": "#1F2937",
    "muted": "#5B6573",
    "line": "#D7E0E8",
    "canvas": "#F4F7FB",
    "white": "#FFFFFF",
    "soft_blue": "#EAF2F8",
    "soft_orange": "#FFF4E5",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def literal(value: str) -> dict[str, Any]:
    return {"expr": {"Literal": {"Value": value}}}


def quoted(value: str) -> dict[str, Any]:
    return literal(f"'{value}'")


def color(value: str) -> dict[str, Any]:
    return {"solid": {"color": quoted(value)}}


def generated_id(page_key: str, key: str) -> str:
    return hashlib.sha1(f"financial-c2-c3:{page_key}:{key}".encode()).hexdigest()[:20]


def page_root(page_key: str) -> Path:
    return SECTIONS / PAGES[page_key] / "visualContainers"


def set_position(config_path: Path, x: float, y: float, width: float, height: float, z: int) -> None:
    config = read_json(config_path)
    config.setdefault("singleVisual", {}).pop("isHidden", None)
    for layout in config.setdefault("layouts", [{"id": 0, "position": {}}]):
        layout.setdefault("position", {}).update(
            {"x": x, "y": y, "z": z, "width": width, "height": height, "tabOrder": z}
        )
    write_json(config_path, config)

    container_path = config_path.with_name("visualContainer.json")
    container = read_json(container_path)
    container.update({"x": x, "y": y, "z": z, "width": width, "height": height, "tabOrder": z})
    write_json(container_path, container)


def retire(path: Path) -> None:
    config_path = path / "config.json"
    if not config_path.is_file():
        raise SystemExit(f"Expected visual not found: {path}")
    config = read_json(config_path)
    config.setdefault("singleVisual", {})["isHidden"] = True
    for layout in config.get("layouts", []):
        layout.setdefault("position", {}).update(
            {"x": -10000, "y": -10000, "width": 1, "height": 1}
        )
    write_json(config_path, config)
    container_path = path / "visualContainer.json"
    container = read_json(container_path)
    container.update({"x": -10000, "y": -10000, "width": 1, "height": 1})
    write_json(container_path, container)


def clone_visual(page_key: str, key: str, template: Path) -> Path:
    destination = page_root(page_key) / f"c2c3_{key}"
    shutil.copytree(template, destination)
    config_path = destination / "config.json"
    config = read_json(config_path)
    config["name"] = generated_id(page_key, key)
    config.setdefault("singleVisual", {}).pop("isHidden", None)
    write_json(config_path, config)
    return destination


def run_style(text: str, *, size: str, text_color: str, bold: bool = False) -> dict[str, Any]:
    style: dict[str, Any] = {
        "fontFamily": "Segoe UI",
        "fontSize": size,
        "color": text_color,
    }
    if bold:
        style["fontWeight"] = "bold"
    return {"value": text, "textStyle": style}


def paragraph(
    *runs: dict[str, Any],
    align: str = "left",
    space_before: str | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {"textRuns": list(runs), "horizontalTextAlignment": align}
    if space_before is not None:
        result["spaceBefore"] = space_before
    return result


def make_shape(
    page_key: str,
    key: str,
    *,
    x: float,
    y: float,
    width: float,
    height: float,
    z: int,
    fill: str,
    outline: str | None = None,
) -> Path:
    visual = clone_visual(page_key, key, SHAPE_TEMPLATE)
    path = visual / "config.json"
    config = read_json(path)
    objects = config["singleVisual"]["objects"]
    objects["fill"] = [{"properties": {"fillColor": color(fill)}, "selector": {"id": "default"}}]
    objects["outline"] = [
        {
            "properties": {
                "show": literal("true" if outline else "false"),
                "lineColor": color(outline or fill),
                "weight": literal("1D"),
            }
        }
    ]
    write_json(path, config)
    set_position(path, x, y, width, height, z)
    return visual


def make_textbox(
    page_key: str,
    key: str,
    paragraphs: list[dict[str, Any]],
    *,
    x: float,
    y: float,
    width: float,
    height: float,
    z: int,
    alt_text: str,
) -> Path:
    visual = clone_visual(page_key, key, TEXT_TEMPLATE)
    path = visual / "config.json"
    config = read_json(path)
    single = config["singleVisual"]
    single["objects"]["general"][0]["properties"]["paragraphs"] = paragraphs
    general = single.setdefault("vcObjects", {}).setdefault("general", [{"properties": {}}])
    general[0].setdefault("properties", {})["altText"] = quoted(alt_text)
    write_json(path, config)
    set_position(path, x, y, width, height, z)
    return visual


def make_button(
    page_key: str,
    key: str,
    label: str,
    target: str,
    *,
    x: float,
    y: float,
    width: float,
    height: float,
    z: int,
    active: bool,
) -> Path:
    visual = clone_visual(page_key, key, BUTTON_TEMPLATE)
    path = visual / "config.json"
    config = read_json(path)
    single = config["singleVisual"]
    single["objects"] = {
        "icon": [{"properties": {"shapeType": quoted("blank")}, "selector": {"id": "default"}}],
        "shape": [{"properties": {"roundEdge": literal("8L")}, "selector": {"id": "default"}}],
        "fill": [
            {
                "properties": {
                    "show": literal("true"),
                    "fillColor": color(COLORS["orange"] if active else COLORS["navy_2"]),
                },
                "selector": {"id": "default"},
            }
        ],
        "outline": [
            {
                "properties": {
                    "show": literal("true"),
                    "lineColor": color(COLORS["orange"] if active else "#56738E"),
                    "weight": literal("1D"),
                },
                "selector": {"id": "default"},
            }
        ],
        "shadow": [{"properties": {"show": literal("false")}}],
        "glow": [{"properties": {"show": literal("false")}}],
        "text": [
            {"properties": {"show": literal("true")}},
            {
                "properties": {
                    "text": quoted(label),
                    "fontFamily": literal("'''Segoe UI'''") ,
                    "fontColor": color(COLORS["white"]),
                    "bold": literal("true"),
                    "fontSize": literal("10D"),
                },
                "selector": {"id": "default"},
            },
        ],
    }
    single["vcObjects"] = {
        "visualLink": [
            {
                "properties": {
                    "show": literal("true"),
                    "type": quoted("PageNavigation"),
                    "navigationSection": quoted(PAGE_IDS[target]),
                }
            }
        ],
        "title": [{"properties": {"show": literal("false"), "text": quoted("")}}],
        "visualHeader": [{"properties": {"show": literal("false")}}],
        "general": [
            {
                "properties": {
                    "altText": quoted(f"Ir a {label}. Página {'activa' if active else 'de navegación'}.")
                }
            }
        ],
    }
    write_json(path, config)
    set_position(path, x, y, width, height, z)
    return visual


def update_measure_references(value: Any, old: str, new: str) -> Any:
    if isinstance(value, str):
        if value == old:
            return new
        if value == f"Tablas de Medidas.{old}":
            return f"Tablas de Medidas.{new}"
        return value
    if isinstance(value, list):
        return [update_measure_references(item, old, new) for item in value]
    if isinstance(value, dict):
        return {key: update_measure_references(item, old, new) for key, item in value.items()}
    return value


def make_card(
    page_key: str,
    key: str,
    measure: str,
    title: str,
    *,
    x: float,
    y: float,
    width: float,
    height: float,
    z: int,
    underlying_type: int,
    format_string: str,
    accent: str,
    display_units: int = 1,
) -> Path:
    visual = clone_visual(page_key, key, CARD_TEMPLATE)
    for filename in ("config.json", "query.json", "dataTransforms.json"):
        path = visual / filename
        data = update_measure_references(read_json(path), "Ingresos", measure)
        if filename == "dataTransforms.json":
            data["queryMetadata"]["Select"][0]["Type"] = 3 if underlying_type == 260 else 1
            data["selects"][0]["type"]["underlyingType"] = underlying_type
        write_json(path, data)

    path = visual / "config.json"
    config = read_json(path)
    single = config["singleVisual"]
    query_ref = f"Tablas de Medidas.{measure}"
    single["columnProperties"] = {query_ref: {"formatString": format_string}}
    single["objects"] = {
        "labels": [
            {
                "properties": {
                    "fontFamily": literal("'''Segoe UI'''") ,
                    "fontSize": literal("22D"),
                    "color": color(COLORS["ink"]),
                    # 1 = None. The custom format controls compact money values
                    # and operations remain exact instead of being rounded to "60 mil".
                    "labelDisplayUnits": literal(f"{display_units}D"),
                    "labelPrecision": literal("1L" if underlying_type != 260 else "0L"),
                }
            }
        ],
        "categoryLabels": [
            {
                "properties": {
                    "show": literal("false"),
                    "fontFamily": literal("'''Segoe UI'''") ,
                }
            }
        ],
    }
    single["vcObjects"] = {
        "title": [
            {
                "properties": {
                    "show": literal("true"),
                    "text": quoted(title),
                    "alignment": quoted("left"),
                    "fontFamily": literal("'''Segoe UI'''") ,
                    "fontSize": literal("11D"),
                    "fontColor": color(COLORS["muted"]),
                    "titleWrap": literal("false"),
                }
            }
        ],
        "background": [
            {"properties": {"show": literal("true"), "color": color(COLORS["white"]), "transparency": literal("0D")}}
        ],
        "border": [
            {"properties": {"show": literal("true"), "color": color(COLORS["line"]), "radius": literal("8D")}}
        ],
        "dropShadow": [{"properties": {"show": literal("false")}}],
        "visualHeader": [{"properties": {"show": literal("false")}}],
        "general": [
            {"properties": {"altText": quoted(f"Indicador {title}: medida {measure}.")}}
        ],
    }
    write_json(path, config)
    set_position(path, x, y, width, height, z)
    make_shape(
        page_key,
        f"{key}_accent",
        x=x,
        y=y,
        width=5,
        height=height,
        z=z + 1,
        fill=accent,
    )
    return visual


def style_data_visual(
    visual: Path,
    *,
    title: str,
    x: float,
    y: float,
    width: float,
    height: float,
    z: int,
    alt_text: str,
) -> None:
    path = visual / "config.json"
    config = read_json(path)
    single = config["singleVisual"]
    vc = single.setdefault("vcObjects", {})
    vc["title"] = [
        {
            "properties": {
                "show": literal("true"),
                "text": quoted(title),
                "alignment": quoted("left"),
                "fontFamily": literal("'''Segoe UI'''") ,
                "fontSize": literal("12D"),
                "fontColor": color(COLORS["ink"]),
                "titleWrap": literal("true"),
            }
        }
    ]
    vc["background"] = [
        {"properties": {"show": literal("true"), "color": color(COLORS["white"]), "transparency": literal("0D")}}
    ]
    vc["border"] = [
        {"properties": {"show": literal("true"), "color": color(COLORS["line"]), "radius": literal("8D")}}
    ]
    vc["dropShadow"] = [{"properties": {"show": literal("false")}}]
    vc["visualHeader"] = [{"properties": {"show": literal("false")}}]
    vc["general"] = [{"properties": {"altText": quoted(alt_text)}}]
    write_json(path, config)
    set_position(path, x, y, width, height, z)


def make_shell(page_key: str, title: str, subtitle: str, active: str) -> None:
    make_shape(page_key, "canvas", x=0, y=0, width=1280, height=720, z=0, fill=COLORS["canvas"])
    make_shape(page_key, "header", x=0, y=0, width=1280, height=86, z=10, fill=COLORS["navy"])
    make_shape(page_key, "header_accent", x=0, y=82, width=1280, height=4, z=11, fill=COLORS["orange"])
    make_textbox(
        page_key,
        "page_title",
        [paragraph(run_style(title, size="21pt", text_color=COLORS["white"], bold=True))],
        x=24,
        y=4,
        width=600,
        height=52,
        z=20,
        alt_text=f"Título de página: {title}",
    )
    make_textbox(
        page_key,
        "page_subtitle",
        [paragraph(run_style(subtitle, size="9pt", text_color="#D9E4EE"))],
        x=24,
        y=47,
        width=650,
        height=34,
        z=21,
        alt_text=subtitle,
    )
    labels = (("home", "Resumen"), ("drivers", "Drivers"), ("usa", "USA"), ("help", "Definiciones"))
    for index, (target, label) in enumerate(labels):
        make_button(
            page_key,
            f"nav_{target}",
            label,
            target,
            x=796 + index * 116,
            y=24,
            width=108,
            height=36,
            z=30 + index,
            active=target == active,
        )


def rebuild_home() -> None:
    root = page_root("home")
    for path in root.iterdir():
        if path.is_dir() and not path.name.startswith("c2c3_"):
            retire(path)

    make_shell(
        "home",
        "EXECUTIVE OVERVIEW",
        "AdventureWorks · 60.398 operaciones · 2010–2014 · moneda de reporte USD",
        "home",
    )
    card_specs = (
        ("revenue", "Ingresos", "Ingresos", 258, "$ #,0.0;-$ #,0.0;$ 0.0", COLORS["blue"], 1000000),
        ("gross_profit", "Utilidad bruta", "Utilidad bruta", 259, "$ #,0.0;-$ #,0.0;$ 0.0", COLORS["teal"], 1000000),
        ("net_margin", "% Margen Neto", "Margen neto", 259, "0.0%;-0.0%;0.0%", COLORS["green"], 1),
        ("operations", "Operaciones", "Operaciones", 260, "#,0", COLORS["orange"], 1),
    )
    for index, (key, measure, title, underlying, fmt, accent, units) in enumerate(card_specs):
        make_card(
            "home",
            f"kpi_{key}",
            measure,
            title,
            x=24 + index * 302,
            y=105,
            width=278,
            height=108,
            z=100 + index * 3,
            underlying_type=underlying,
            format_string=fmt,
            accent=accent,
            display_units=units,
        )

    trend = clone_visual("home", "trend", CHART_TEMPLATE)
    style_data_visual(
        trend,
        title="Evolución de ingresos, utilidad bruta y COGS",
        x=24,
        y=235,
        width=756,
        height=356,
        z=130,
        alt_text="Gráfico de columnas por año y semestre con ingresos, utilidad bruta y COGS.",
    )

    make_shape("home", "insight_card", x=800, y=235, width=456, height=166, z=120, fill=COLORS["white"])
    make_textbox(
        "home",
        "insight",
        [
            paragraph(run_style("RESULTADO CLAVE", size="12pt", text_color=COLORS["blue"], bold=True)),
            paragraph(run_style("2013 aportó $16,4 M (55,7% del total) y creció 179,9% frente a 2012.", size="12pt", text_color=COLORS["ink"])),
            paragraph(run_style("Margen bruto 41,4% · Margen neto 30,9%", size="10pt", text_color=COLORS["muted"])),
        ],
        x=824,
        y=254,
        width=408,
        height=125,
        z=131,
        alt_text="Resultado clave de 2013 y márgenes principales.",
    )
    make_shape("home", "action_card", x=800, y=421, width=456, height=170, z=120, fill=COLORS["white"])
    make_textbox(
        "home",
        "action",
        [
            paragraph(run_style("ACCIÓN RECOMENDADA", size="12pt", text_color=COLORS["orange"], bold=True)),
            paragraph(run_style("Priorizar USA y Australia: concentran 62,8% del ingreso.", size="12pt", text_color=COLORS["ink"])),
            paragraph(run_style("Proteger el mix de bicicletas, responsable del 96,5% del ingreso.", size="10pt", text_color=COLORS["muted"])),
        ],
        x=824,
        y=440,
        width=408,
        height=130,
        z=131,
        alt_text="Acción recomendada sobre concentración geográfica y de producto.",
    )
    make_shape("home", "limitation_bar", x=24, y=611, width=1232, height=84, z=120, fill=COLORS["soft_orange"])
    make_textbox(
        "home",
        "limitation",
        [
            paragraph(run_style("LECTURA RESPONSABLE", size="10pt", text_color=COLORS["orange"], bold=True)),
            paragraph(run_style("2010 y 2014 son períodos parciales; el snapshot sólo cubre hasta el 28 de enero de 2014. No interpretar 2014 como caída anual.", size="10pt", text_color=COLORS["ink"])),
        ],
        x=44,
        y=625,
        width=1192,
        height=54,
        z=131,
        alt_text="Advertencia de períodos parciales 2010 y 2014.",
    )


def rebuild_drivers() -> None:
    root = page_root("drivers")
    keep = {
        "04000_COGS, Utilidad Bruta e Ingresos por Bimestre",
        "07000_Ingresos por País",
    }
    for path in root.iterdir():
        if path.is_dir() and not path.name.startswith("c2c3_") and path.name not in keep:
            retire(path)

    make_shell(
        "drivers",
        "DRIVERS DE MARGEN Y VARIACIÓN LY",
        "Variaciones interanuales, estructura de costos y concentración geográfica",
        "drivers",
    )
    specs = (
        ("revenue_ly", "Ingresos vs LY %", "Ingresos vs LY", "0.0%;-0.0%;0.0%", COLORS["blue"]),
        ("gross_margin", "% Margen Bruto", "Margen bruto", "0.0%;-0.0%;0.0%", COLORS["teal"]),
        ("net_margin", "% Margen Neto", "Margen neto", "0.0%;-0.0%;0.0%", COLORS["green"]),
        ("cost_ratio", "Ratio Costo Operacional %", "Ratio costo operacional", "0.0%;-0.0%;0.0%", COLORS["orange"]),
    )
    for index, (key, measure, title, fmt, accent) in enumerate(specs):
        make_card(
            "drivers",
            f"kpi_{key}",
            measure,
            title,
            x=24 + index * 302,
            y=105,
            width=278,
            height=108,
            z=100 + index * 3,
            underlying_type=259,
            format_string=fmt,
            accent=accent,
        )

    chart = root / "04000_COGS, Utilidad Bruta e Ingresos por Bimestre"
    style_data_visual(
        chart,
        title="Ingresos, utilidad bruta y COGS por período",
        x=24,
        y=235,
        width=790,
        height=460,
        z=130,
        alt_text="Columnas comparativas por año y semestre para ingresos, utilidad bruta y COGS.",
    )
    chart_config = read_json(chart / "config.json")
    chart_objects = chart_config["singleVisual"].setdefault("objects", {})
    chart_objects["labels"] = [{"properties": {"show": literal("false")}}]
    chart_objects.setdefault("valueAxis", [{}])[0].setdefault("properties", {})["gridlineThickness"] = literal("1D")
    write_json(chart / "config.json", chart_config)

    country_map = root / "07000_Ingresos por País"
    style_data_visual(
        country_map,
        title="Distribución de ingresos por país",
        x=834,
        y=235,
        width=422,
        height=460,
        z=130,
        alt_text="Mapa único de distribución de ingresos por país; reemplaza tres mapas redundantes.",
    )


def focus_usa_matrix(visual: Path) -> None:
    """Keep the auditable seven measures but remove misleading nested columns."""
    keep_names = [
        "DimCustomer.StateProvinceName",
        "Tablas de Medidas.Ingresos",
        "Tablas de Medidas.Utilidad neta",
        "Tablas de Medidas.Utilidad bruta",
        "Tablas de Medidas.% Margen Bruto",
        "Tablas de Medidas.% Margen Neto",
        "Tablas de Medidas.COGS",
        "Tablas de Medidas.Costo Total Envios",
    ]

    config_path = visual / "config.json"
    config = read_json(config_path)
    single = config["singleVisual"]
    single["projections"] = {
        "Values": [{"queryRef": name} for name in keep_names[1:]],
        "Rows": [{"queryRef": keep_names[0], "active": True}],
    }
    prototype = {item["Name"]: item for item in single["prototypeQuery"]["Select"]}
    missing = [name for name in keep_names if name not in prototype]
    if missing:
        raise SystemExit(f"USA matrix prototype fields missing: {missing}")
    single["prototypeQuery"]["Select"] = [copy.deepcopy(prototype[name]) for name in keep_names]
    single["prototypeQuery"].pop("OrderBy", None)
    write_json(config_path, config)

    query_path = visual / "query.json"
    query_data = read_json(query_path)
    command = query_data["Commands"][0]["SemanticQueryDataShapeCommand"]
    query_select = {item["Name"]: item for item in command["Query"]["Select"]}
    missing = [name for name in keep_names if name not in query_select]
    if missing:
        raise SystemExit(f"USA matrix query fields missing: {missing}")
    command["Query"]["Select"] = [copy.deepcopy(query_select[name]) for name in keep_names]
    command["Binding"] = {
        "Primary": {"Groupings": [{"Projections": [0]}]},
        "Secondary": {"Groupings": [{"Projections": list(range(1, 8))}]},
        "DataReduction": {
            "DataVolume": 3,
            "Primary": {"Window": {"Count": 100}},
            "Secondary": {"Top": {"Count": 100}},
        },
        "Version": 1,
    }
    write_json(query_path, query_data)

    transform_path = visual / "dataTransforms.json"
    transforms = read_json(transform_path)
    metadata = {item["Name"]: item for item in transforms["queryMetadata"]["Select"]}
    selections = {item["queryName"]: item for item in transforms["selects"]}
    missing = [name for name in keep_names if name not in metadata or name not in selections]
    if missing:
        raise SystemExit(f"USA matrix transform fields missing: {missing}")
    transforms["queryMetadata"]["Select"] = [copy.deepcopy(metadata[name]) for name in keep_names]
    transforms["selects"] = [copy.deepcopy(selections[name]) for name in keep_names]
    for index, item in enumerate(transforms["selects"]):
        item["roles"] = {"Rows": True} if index == 0 else {"Values": True}
    transforms["projectionOrdering"] = {"Values": list(range(1, 8)), "Rows": [0]}
    transforms.pop("projectionActiveItems", None)
    transforms["visualElements"] = [
        {
            "DataRoles": [
                {"Name": "Rows", "Projection": 0, "isActive": True},
                *[
                    {"Name": "Values", "Projection": index, "isActive": False}
                    for index in range(1, 8)
                ],
            ]
        }
    ]
    write_json(transform_path, transforms)


def rebuild_usa() -> None:
    root = page_root("usa")
    keep = {
        "00000_Filtros",
        "01000_pivotTable (61544)",
        "11000_Ingresos VS %Margen Bruto por Ciudad",
        "12000_Ingresos VS C.O.G.S. por año",
    }
    for path in root.iterdir():
        if path.is_dir() and not path.name.startswith("c2c3_") and path.name not in keep:
            retire(path)

    make_shell(
        "usa",
        "GEOGRAPHIC DRILL-DOWN — USA",
        "Detalle por estado · comparación de rentabilidad · alcance fijo CountryRegionCode = US",
        "usa",
    )
    make_shape("usa", "scope_badge", x=24, y=105, width=230, height=40, z=90, fill=COLORS["soft_blue"])
    make_textbox(
        "usa",
        "scope_text",
        [paragraph(run_style("ALCANCE FIJO  ·  USA", size="10pt", text_color=COLORS["blue"], bold=True), align="center")],
        x=34,
        y=108,
        width=210,
        height=34,
        z=100,
        alt_text="El análisis geográfico está filtrado de forma fija a Estados Unidos.",
    )

    slicer = root / "00000_Filtros"
    style_data_visual(
        slicer,
        title="Métrica",
        x=1030,
        y=98,
        width=226,
        height=56,
        z=110,
        alt_text="Selector de métrica para el detalle USA.",
    )

    matrix = root / "01000_pivotTable (61544)"
    focus_usa_matrix(matrix)
    style_data_visual(
        matrix,
        title="Rendimiento por estado",
        x=24,
        y=164,
        width=1232,
        height=280,
        z=120,
        alt_text="Matriz por estado con ingresos, utilidad bruta, márgenes y COGS.",
    )
    matrix_config = read_json(matrix / "config.json")
    objects = matrix_config["singleVisual"].setdefault("objects", {})
    for object_name in ("columnHeaders", "rowHeaders", "values"):
        props = objects.setdefault(object_name, [{"properties": {}}])[0].setdefault("properties", {})
        props["fontFamily"] = literal("'''Segoe UI'''")
        props["fontSize"] = literal("9D")
    objects["columnHeaders"][0]["properties"].update(
        {"fontColor": color(COLORS["white"]), "backColor": color(COLORS["navy_2"]), "bold": literal("true")}
    )
    objects.setdefault("grid", [{"properties": {}}])[0].setdefault("properties", {}).update(
        {"gridVertical": literal("false"), "gridHorizontal": literal("true"), "gridHorizontalColor": color(COLORS["line"])}
    )
    write_json(matrix / "config.json", matrix_config)

    scatter = root / "11000_Ingresos VS %Margen Bruto por Ciudad"
    style_data_visual(
        scatter,
        title="Ingresos vs margen bruto por estado",
        x=24,
        y=464,
        width=600,
        height=232,
        z=120,
        alt_text="Dispersión de ingresos y margen bruto por estado, sin etiquetas superpuestas.",
    )
    scatter_config = read_json(scatter / "config.json")
    scatter_objects = scatter_config["singleVisual"].setdefault("objects", {})
    scatter_objects["categoryLabels"] = [{"properties": {"show": literal("false")}}]
    scatter_objects.setdefault("bubbles", [{"properties": {}}])[0].setdefault("properties", {})["bubbleSize"] = literal("-12L")
    for axis in ("categoryAxis", "valueAxis"):
        scatter_objects.setdefault(axis, [{"properties": {}}])[0].setdefault("properties", {})["gridlineThickness"] = literal("1D")
    write_json(scatter / "config.json", scatter_config)

    line = root / "12000_Ingresos VS C.O.G.S. por año"
    style_data_visual(
        line,
        title="Ingresos vs COGS por año",
        x=644,
        y=464,
        width=612,
        height=232,
        z=120,
        alt_text="Serie anual comparativa de ingresos y COGS para Estados Unidos.",
    )


def card_text(page_key: str, key: str, title: str, lines: list[tuple[str, str]], *, x: float, y: float, width: float, height: float) -> None:
    make_shape(page_key, f"{key}_card", x=x, y=y, width=width, height=height, z=90, fill=COLORS["white"])
    paragraphs = [paragraph(run_style(title, size="13pt", text_color=COLORS["blue"], bold=True))]
    for label, definition in lines:
        paragraphs.append(
            paragraph(
                run_style(f"{label}: ", size="9pt", text_color=COLORS["ink"], bold=True),
                run_style(definition, size="9pt", text_color=COLORS["muted"]),
            )
        )
    make_textbox(
        page_key,
        f"{key}_text",
        paragraphs,
        x=x + 20,
        y=y + 17,
        width=width - 40,
        height=height - 30,
        z=100,
        alt_text=f"{title}. " + " ".join(f"{a}: {b}" for a, b in lines),
    )


def rebuild_help() -> None:
    root = page_root("help")
    for path in root.iterdir():
        if path.is_dir() and not path.name.startswith("c2c3_"):
            retire(path)

    make_shell(
        "help",
        "DEFINICIONES Y FUENTES",
        "Contrato analítico, alcance, reproducibilidad y reglas de lectura",
        "help",
    )
    card_text(
        "help",
        "kpis",
        "KPIs financieros",
        [
            ("Ingresos", "suma de SalesAmount antes de costos, fletes e impuestos."),
            ("COGS", "suma de TotalProductCost asociada a las ventas."),
            ("Utilidad bruta", "Ingresos − COGS."),
            ("Utilidad neta", "Ingresos − costos totales."),
            ("Costos totales", "COGS + costos de envío + impuestos."),
        ],
        x=24,
        y=110,
        width=596,
        height=246,
    )
    card_text(
        "help",
        "margins",
        "Márgenes y variaciones",
        [
            ("Margen bruto", "Utilidad bruta / Ingresos."),
            ("Margen neto", "Utilidad neta / Ingresos."),
            ("Ratio costo operacional", "(COGS + costos de envío) / Ingresos; excluye impuestos."),
            ("LY", "mismo período del año anterior mediante SAMEPERIODLASTYEAR."),
            ("Variación pp", "diferencia absoluta entre porcentajes expresada en puntos porcentuales."),
        ],
        x=636,
        y=110,
        width=620,
        height=246,
    )
    card_text(
        "help",
        "contract",
        "Fuente y contrato temporal",
        [
            ("Fuente", "Microsoft AdventureWorksDW2019 · FactInternetSales."),
            ("Fecha analítica", "OrderDateKey relacionado activamente con DimDate[DateKey]."),
            ("Cobertura", "2010-12-29 a 2014-01-28; 2010 y 2014 son períodos parciales."),
            ("Alcance USA", "filtro fijo DimCustomer[CountryRegionCode] = US."),
        ],
        x=24,
        y=376,
        width=596,
        height=320,
    )
    card_text(
        "help",
        "quality",
        "Reproducibilidad y control de calidad",
        [
            ("Modelo", "35 medidas DAX y ruta de fechas por OrderDateKey."),
            ("Validación", "68 contextos en total, año, país, estado y categoría; residuales = 0."),
            ("Artefactos", "fuente TMDL/JSON, PBIT sin datos, PBIX con snapshot y evidencia visual."),
            ("Limitación", "el PBIX prueba el resultado embebido; el refresh requiere AdventureWorksDW2019."),
        ],
        x=636,
        y=376,
        width=620,
        height=320,
    )


def normalize_page_visuals() -> None:
    for path in REPORT.rglob("config.json"):
        config = read_json(path)
        serialized = json.dumps(config, ensure_ascii=False)
        serialized = serialized.replace("'Arial'", "'''Segoe UI'''").replace("'DIN'", "'''Segoe UI'''")
        config = json.loads(serialized)
        single = config.get("singleVisual", {}) if isinstance(config, dict) else {}
        vc = single.get("vcObjects", {})
        for name in ("dropShadow", "shadow", "glow"):
            for item in vc.get(name, []):
                item.setdefault("properties", {})["show"] = literal("false")
        write_json(path, config)


def main() -> int:
    if not REPORT.is_dir():
        raise SystemExit(f"Extracted report source not found: {REPORT}")
    for root in (page_root(key) for key in PAGES):
        for path in list(root.glob("c2c3_*")):
            shutil.rmtree(path)

    rebuild_home()
    rebuild_drivers()
    rebuild_usa()
    rebuild_help()
    normalize_page_visuals()
    print("FIN-C2/C3 dashboard redesign applied successfully.")
    print("  - consistent four-page navigation")
    print("  - KPI-first executive and driver pages")
    print("  - one country map, no gauge wall, focused USA matrix")
    print("  - accessible titles, alt text, spacing, and 16:9 fit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

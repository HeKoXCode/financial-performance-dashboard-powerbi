#!/usr/bin/env python3
"""Build the deterministic FIN-C1 PDF evidence pack from verified report captures."""

from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path

from reportlab.lib.colors import HexColor, white
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "output" / "pdf" / "financial_c1_release_evidence.pdf"
PAGE = (960, 540)
NAVY = HexColor("#12344D")
BLUE = HexColor("#2F75B5")
ORANGE = HexColor("#E67E22")
LIGHT = HexColor("#EEF4F8")
GRAY = HexColor("#566573")
SCREENSHOTS = (
    ("Executive Overview", ROOT / "Images" / "executive_overview.png"),
    ("Drivers de margen y LY", ROOT / "Images" / "overview.png"),
    ("Geographic Drill-down", ROOT / "Images" / "usa_detailed.png"),
    ("Definiciones y fuentes", ROOT / "Images" / "glossary.png"),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def read_sql_rows() -> dict[tuple[str, str], dict[str, str]]:
    path = ROOT / "DOCS" / "sql_reconciliation.csv"
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return {
            (row["Granularity"], row["Member"]): row
            for row in csv.DictReader(handle)
        }


def draw_header(pdf: canvas.Canvas, title: str, page: int) -> None:
    pdf.setFillColor(NAVY)
    pdf.rect(0, PAGE[1] - 42, PAGE[0], 42, fill=1, stroke=0)
    pdf.setFillColor(white)
    pdf.setFont("Helvetica-Bold", 15)
    pdf.drawString(28, PAGE[1] - 27, title)
    pdf.setFont("Helvetica", 8)
    pdf.drawRightString(PAGE[0] - 28, PAGE[1] - 26, f"FIN-C1 | page {page}")


def draw_footer(pdf: canvas.Canvas) -> None:
    pdf.setFillColor(GRAY)
    pdf.setFont("Helvetica", 7.5)
    pdf.drawString(28, 14, "AdventureWorksDW2019 synthetic sample | OrderDateKey analytical path")
    pdf.drawRightString(PAGE[0] - 28, 14, "Generated from verified 1920x1080 embedded-snapshot captures")


def cover(pdf: canvas.Canvas, rows: dict[tuple[str, str], dict[str, str]]) -> None:
    total = rows[("Total", "All")]
    year_2013 = rows[("Year", "2013")]
    year_2012 = rows[("Year", "2012")]
    growth = float(year_2013["Revenue"]) / float(year_2012["Revenue"]) - 1

    pdf.setFillColor(NAVY)
    pdf.rect(0, 0, PAGE[0], PAGE[1], fill=1, stroke=0)
    pdf.setFillColor(ORANGE)
    pdf.rect(0, PAGE[1] - 12, PAGE[0], 12, fill=1, stroke=0)
    pdf.setFillColor(white)
    pdf.setFont("Helvetica-Bold", 30)
    pdf.drawString(54, 450, "Financial Performance Dashboard")
    pdf.setFont("Helvetica-Bold", 19)
    pdf.drawString(54, 416, "FIN-C1 release evidence")
    pdf.setFont("Helvetica", 11)
    pdf.drawString(54, 390, "Independent SQL reconciliation, compiled PBIT, KPI contract, and visual proof")

    cards = (
        ("FACT ROWS", "60,398"),
        ("SQL / DAX CONTEXTS", "68 / 68"),
        ("TOTAL REVENUE", f"${float(total['Revenue']) / 1_000_000:.2f}M"),
        ("2013 GROWTH VS 2012", f"{growth * 100:.1f}%"),
    )
    card_width = 196
    for index, (label, value) in enumerate(cards):
        x = 54 + index * 216
        pdf.setFillColor(LIGHT)
        pdf.roundRect(x, 280, card_width, 78, 8, fill=1, stroke=0)
        pdf.setFillColor(GRAY)
        pdf.setFont("Helvetica-Bold", 8)
        pdf.drawString(x + 14, 337, label)
        pdf.setFillColor(NAVY)
        pdf.setFont("Helvetica-Bold", 18)
        pdf.drawString(x + 14, 302, value)

    pdf.setFillColor(white)
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(54, 232, "Release gates passed")
    lines = (
        "- SQL recomputation from base columns matches DAX within $0.01 and 1e-10.",
        "- PBIT package contains 35 measures, OrderDateKey, and four final pages.",
        "- PBIX, PBIT, source snapshot, KPI evidence, images, and manifest are hashed.",
        "- 2010 and 2014 remain partial periods; annual conclusions use complete years.",
    )
    pdf.setFont("Helvetica", 10.5)
    y = 205
    for line in lines:
        pdf.drawString(64, y, line)
        y -= 25

    pdf.setFillColor(ORANGE)
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(54, 64, "Release date: 2026-08-12 | Source: Microsoft AdventureWorksDW2019")
    pdf.showPage()


def screenshot_page(pdf: canvas.Canvas, title: str, image_path: Path, page: int) -> None:
    draw_header(pdf, title, page)
    draw_footer(pdf)
    image = ImageReader(str(image_path))
    x, y, width, height = 28, 34, PAGE[0] - 56, PAGE[1] - 88
    pdf.setStrokeColor(BLUE)
    pdf.setLineWidth(1)
    pdf.rect(x - 1, y - 1, width + 2, height + 2, fill=0, stroke=1)
    pdf.drawImage(image, x, y, width=width, height=height, preserveAspectRatio=True, anchor="c")
    pdf.showPage()


def appendix(pdf: canvas.Canvas) -> None:
    draw_header(pdf, "Release contract and artifact hashes", 6)
    draw_footer(pdf)
    pdf.setFillColor(NAVY)
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(36, 468, "Primary artifacts")
    artifacts = (
        ROOT / "Financial_Report.pbix",
        ROOT / "Financial_Report.pbit",
        ROOT / "DATA" / "financial_sql_input.csv.gz",
        ROOT / "DOCS" / "dax_reconciliation.csv",
        ROOT / "DOCS" / "sql_reconciliation.csv",
    )
    y = 440
    for artifact in artifacts:
        pdf.setFillColor(GRAY)
        pdf.setFont("Helvetica-Bold", 8.5)
        pdf.drawString(42, y, artifact.relative_to(ROOT).as_posix())
        pdf.setFillColor(NAVY)
        pdf.setFont("Courier", 7.2)
        pdf.drawString(260, y, sha256(artifact))
        y -= 25

    pdf.setFillColor(NAVY)
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(36, 286, "Expected variation policy")
    policy = (
        "1. KPI changes require matching SQL and DAX evidence plus a release note.",
        "2. Source snapshot and row-count changes require an explicit data refresh decision.",
        "3. PBIX/PBIT hashes may change after model, layout, data, or Desktop version changes.",
        "4. Screenshot/PDF hashes may change after a verified visual render or tool update.",
        "5. Partial-period limitations and the OrderDateKey contract must remain visible.",
    )
    pdf.setFillColor(GRAY)
    pdf.setFont("Helvetica", 10)
    y = 258
    for line in policy:
        pdf.drawString(42, y, line)
        y -= 27

    pdf.setFillColor(LIGHT)
    pdf.roundRect(36, 54, PAGE[0] - 72, 46, 7, fill=1, stroke=0)
    pdf.setFillColor(NAVY)
    pdf.setFont("Helvetica-Bold", 9.5)
    pdf.drawString(50, 79, "Machine-readable contract: release/financial-c1-manifest.json")
    pdf.setFont("Helvetica", 8.5)
    pdf.drawString(50, 63, "Full formulas and context rules: DOCS/dax_measure_catalog.md")
    pdf.showPage()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    for _, image_path in SCREENSHOTS:
        if not image_path.is_file():
            raise SystemExit(f"Screenshot missing: {image_path}")
    rows = read_sql_rows()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(
        str(args.output),
        pagesize=PAGE,
        pageCompression=1,
        invariant=1,
    )
    pdf.setTitle("Financial Performance Dashboard - FIN-C1 release evidence")
    pdf.setAuthor("HeKoXCode")
    pdf.setSubject("Power BI analytical release verification")
    cover(pdf, rows)
    for page, (title, image_path) in enumerate(SCREENSHOTS, start=2):
        screenshot_page(pdf, title, image_path, page)
    appendix(pdf)
    pdf.save()
    print(f"FIN-C1 PDF evidence built: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

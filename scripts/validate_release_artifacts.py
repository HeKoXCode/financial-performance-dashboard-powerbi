#!/usr/bin/env python3
"""Validate the committed or freshly generated FIN-C3 PDF release evidence."""

from __future__ import annotations

import argparse
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PDF = ROOT / "output" / "pdf" / "financial_c3_release_evidence.pdf"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", type=Path, default=DEFAULT_PDF)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.pdf.is_file():
        raise SystemExit(f"Release PDF missing: {args.pdf}")
    reader = PdfReader(str(args.pdf))
    if len(reader.pages) != 6:
        raise SystemExit(f"Expected 6 release-evidence pages; found {len(reader.pages)}")
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    for token in (
        "FIN-C3 release evidence",
        "60,398",
        "68 / 68",
        "Executive Overview",
        "Drivers de margen y LY",
        "Geographic Drill-down",
        "Definiciones y fuentes",
        "Expected variation policy",
        "release/financial-c3-manifest.json",
    ):
        if token not in text:
            raise SystemExit(f"Release PDF text missing: {token}")
    for page, expected in zip(reader.pages, [(960, 540)] * 6, strict=True):
        width = round(float(page.mediabox.width))
        height = round(float(page.mediabox.height))
        if (width, height) != expected:
            raise SystemExit(f"Unexpected PDF page size: {(width, height)}")
    print("FIN-C3 PDF evidence validation PASSED")
    print("  - six pages, expected headings, and 16:9 page geometry verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

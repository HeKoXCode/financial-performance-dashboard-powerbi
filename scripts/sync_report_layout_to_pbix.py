#!/usr/bin/env python3
"""Synchronize the extracted report JSON into the PBIX Report/Layout part."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "Financial_Report"
REPORT = PROJECT / "Report"
PBIX = ROOT / "Financial_Report.pbix"


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def compact(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def build_layout() -> dict[str, object]:
    layout = dict(read_json(REPORT / "report.json"))
    layout["config"] = compact(read_json(REPORT / "config.json"))
    sections: list[dict[str, object]] = []

    section_dirs = [path for path in (REPORT / "sections").iterdir() if path.is_dir()]
    section_dirs.sort(key=lambda path: int(read_json(path / "section.json")["ordinal"]))

    for section_dir in section_dirs:
        section = dict(read_json(section_dir / "section.json"))
        section["config"] = compact(read_json(section_dir / "config.json"))
        section["filters"] = compact(read_json(section_dir / "filters.json"))
        visuals: list[dict[str, object]] = []

        for visual_dir in sorted((section_dir / "visualContainers").iterdir()):
            if not visual_dir.is_dir():
                continue
            visual = dict(read_json(visual_dir / "visualContainer.json"))
            for part in ("config", "filters", "query", "dataTransforms"):
                path = visual_dir / f"{part}.json"
                if path.is_file():
                    visual[part] = compact(read_json(path))
            visuals.append(visual)

        visuals.sort(key=lambda item: float(item.get("z", 0)))
        section["visualContainers"] = visuals
        sections.append(section)

    layout["sections"] = sections
    return layout


def sync() -> None:
    if not PBIX.is_file() or PBIX.suffix.lower() != ".pbix":
        raise SystemExit(f"Expected PBIX not found: {PBIX}")
    if PBIX.parent.resolve() != ROOT.resolve():
        raise SystemExit("Refusing to update a PBIX outside the repository root")

    layout_bytes = compact(build_layout()).encode("utf-16-le")
    descriptor, temp_name = tempfile.mkstemp(prefix="Financial_Report.", suffix=".pbix.tmp", dir=ROOT)
    os.close(descriptor)
    temp_path = Path(temp_name)

    try:
        with ZipFile(PBIX, "r") as source, ZipFile(temp_path, "w", allowZip64=True) as target:
            for info in source.infolist():
                if info.filename in {"Report/Layout", "SecurityBindings"}:
                    continue
                target.writestr(info, source.read(info.filename))
            target.writestr("Report/Layout", layout_bytes, compress_type=ZIP_DEFLATED)

        with ZipFile(temp_path, "r") as check:
            if check.testzip() is not None:
                raise SystemExit("The synchronized PBIX failed its ZIP integrity check")
            parsed = json.loads(check.read("Report/Layout").decode("utf-16-le"))
            if len(parsed.get("sections", [])) != 4:
                raise SystemExit("The synchronized PBIX does not contain four report pages")

        os.replace(temp_path, PBIX)
    finally:
        if temp_path.exists():
            temp_path.unlink()

    print("PBIX report layout synchronization PASSED")
    print("  - four extracted pages embedded")
    print("  - stale SecurityBindings removed after the intentional layout change")


if __name__ == "__main__":
    sync()

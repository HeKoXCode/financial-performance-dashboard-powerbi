"""Apply the reviewed presentation-only B3 overrides after the source rebuild."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def apply_hq_presentation():
    report = ROOT / "Financial_Report/Report"
    overrides = json.loads((ROOT / "scripts/financial_hq_presentation_overrides.json").read_text(encoding="utf-8"))
    pages = {json.loads((p / "section.json").read_text(encoding="utf-8-sig"))["name"]: p for p in (report / "sections").iterdir() if p.is_dir()}
    for item in overrides["visuals"]:
        visuals = {}
        for path in (pages[item["page"]] / "visualContainers").iterdir():
            if path.is_dir():
                config = json.loads((path / "config.json").read_text(encoding="utf-8-sig"))
                visuals[config["name"]] = path
        destination = visuals[item["visual"]]
        for part, value in item["parts"].items():
            (destination / f"{part}.json").write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    apply_hq_presentation()
    print("Approved HQ presentation applied: model and data unchanged")

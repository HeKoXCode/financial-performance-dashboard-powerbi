# FIN-C2/C3 dashboard redesign verification

Audit date: **2026-08-12**

Status: **Complete locally; ready to publish**

## Result

FIN-C2 and FIN-C3 replace the legacy presentation with a four-page, decision-oriented dashboard. The redesign is implemented in the reviewable report source, synchronized into the embedded-data PBIX, compiled into the data-free PBIT, rendered in Power BI Desktop, and checked through a dedicated validator.

## What changed

| Page | Previous issue | Implemented redesign |
|---|---|---|
| Executive Overview | Decorative cover with no analytical visuals | Four KPI cards, a period trend, result/action panels, and a partial-period warning |
| Drivers de margen y LY | Four large gauges and three redundant maps | Four compact KPI cards, one comparative period chart, and one country map |
| Geographic Drill-down | Inconsistent navigation, crowded point labels, and weak scope cue | Fixed USA badge, consistent navigation, resized matrix, scatter labels disabled, and balanced lower charts |
| Definiciones y fuentes | One long textbox and excessive empty space | Four grouped cards for KPIs, margins, source/time contract, and reproducibility |

## Navigation contract

Every page exposes the same four buttons in the same position:

1. `Resumen`
2. `Drivers`
3. `USA`
4. `Definiciones`

The active page uses the orange accent. Each button is a real `PageNavigation` action with a descriptive alternative-text value; it is not a decorative label or screenshot hotspot.

## Visual-selection decisions

- **Gauges removed:** four gauges consumed 22% of the canvas and made cross-KPI comparison difficult. Compact cards now expose revenue change, current gross margin, current net margin, and operational cost ratio.
- **Maps reduced from three to one:** state-level map duplication did not add a distinct analytical question. One country map remains for global concentration; state analysis belongs on the USA page.
- **Clustered columns retained:** revenue, gross profit, and COGS share a monetary unit and require period comparison, so a common-axis column chart remains appropriate.
- **Scatter retained:** the USA scatter answers whether high-revenue states also sustain gross margin. Labels are disabled to prevent overlap; details remain available through native tooltips.
- **Line chart retained:** annual revenue and COGS use the same currency unit and benefit from a temporal comparison.
- **Detailed matrix retained:** the embedded snapshot and reviewable source expose the same seven financial measures. Its larger panel preserves traceability without forcing the charts to carry every metric.

## Layout and visual system

- Canvas: **1280×720**, captured at **1920×1080**.
- Header: navy band, orange rule, white page title, secondary subtitle.
- Canvas background: light neutral; analytical panels use white surfaces.
- Accent semantics: blue for revenue, teal for gross profit, green for net margin, orange for cost/attention, red only for negative warnings.
- Type: Segoe UI throughout; titles, KPI labels, body copy, and annotations use a repeatable hierarchy.
- Effects: no decorative bitmap backgrounds, glow, or drop shadows.
- Fit: every visible visual is contained within the 16:9 canvas.

## Reproduction and validation

Apply the deterministic transformation and run the complete checks:

```powershell
python scripts/update_financial_report_s1_s3.py
python scripts/update_financial_report_i1_i3.py
python scripts/update_financial_report_c2_c3.py
python scripts/validate_s1_s3.py
python scripts/validate_i1_i3.py
python scripts/validate_c2_c3.py
python scripts/validate_pbit_package.py Financial_Report.pbit
python scripts/run_sql_reconciliation.py
python scripts/build_release_evidence.py
python scripts/validate_release_artifacts.py
python scripts/build_release_manifest.py --check
```

`validate_c2_c3.py` checks:

- four identical navigation systems and correct page targets;
- active/inactive layout positions and full 1280×720 fit;
- four executive cards and four driver cards;
- one visible country map and zero visible gauges;
- USA slicer, detailed matrix, scatter, and line chart;
- disabled scatter labels to prevent collisions;
- alternative text for every visible non-decorative visual;
- required analytical narrative and four 1920×1080 captures.

## Render evidence

The final PBIX was opened in Power BI Desktop `2.156.951.0`. All four pages were captured after clearing selection/edit state and moving the pointer outside the report canvas. The screenshots show no cursor, tooltip, editing handle, clipped text, or overflow indicator.

The current six-page evidence pack is `output/pdf/financial_c3_release_evidence.pdf`; its machine-readable contract is `release/financial-c3-manifest.json`.

## Boundaries

- The redesign does not invent new data or change a reconciled DAX formula.
- The PBIX proves the embedded snapshot result; a fresh source refresh still requires a restored `AdventureWorksDW2019` database.
- The country map still depends on Power BI/Bing geocoding.
- The matrix keeps seven financial measures for auditability and may require horizontal scrolling at smaller-than-fit-to-page zoom levels.

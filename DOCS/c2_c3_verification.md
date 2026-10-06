# FIN-C2/C3 dashboard redesign verification

Initial audit date: **2026-08-12**. Presentation/media integration: **2026-10-06**.

Status: **Current source, PBIX, PBIT and native-PDF previews aligned**.

## Result

FIN-C2 and FIN-C3 replace the legacy presentation with a four-page, decision-oriented dashboard. The redesign is implemented in the reviewable report source, synchronized into the embedded-data PBIX, compiled into the data-free PBIT, rendered in Power BI Desktop, and checked through a dedicated validator.

## What changed

| Page | Previous issue | Implemented redesign |
|---|---|---|
| Executive Overview | Decorative cover with no analytical visuals | Four KPI cards, a period trend, result/action panels, and a partial-period warning |
| Drivers de margen y LY | Four large gauges and three redundant maps | Four compact KPI cards, one comparative period chart, and native country revenue bars |
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
- **Maps replaced with native country bars:** the revenue comparison preserves its measure and country population without requiring geocoding; state analysis belongs on the USA page.
- **Clustered columns retained:** revenue, gross profit, and COGS share a monetary unit and require period comparison, so a common-axis column chart remains appropriate.
- **Scatter retained:** the USA scatter answers whether high-revenue states also sustain gross margin. Labels are disabled to prevent overlap; details remain available through native tooltips.
- **Line chart retained:** annual revenue and COGS use the same currency unit and benefit from a temporal comparison.
- **Detailed matrix retained:** the embedded snapshot and reviewable source expose the same seven financial measures. Its larger panel preserves traceability without forcing the charts to carry every metric.

## Layout and visual system

- Canvas: **1280×720**; current previews are native-PDF renders at **2880×1620**. The optional UI capture script still produces 1920×1080, a different method from the published previews.
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
- one visible country bar chart, zero country maps and zero visible gauges;
- USA slicer, detailed matrix, scatter, and line chart;
- disabled scatter labels to prevent collisions;
- alternative text for every visible non-decorative visual;
- required analytical narrative and four 2880×1620 previews.

## Render evidence

The initial August verification used Power BI Desktop `2.156.951.0` and UI captures. The current presentation was exported natively in Desktop `2.158.1177.0` for the October multimedia update. Its four report pages are rendered at 2880×1620, without application chrome or a cursor. The PDF includes a separate vector appendix with all 22 USA states; that appendix is not a fifth interactive page.

On 2026-10-06 I compared the canonical report source, embedded-data PBIX, data-free PBIT and approved native-export source: their visual layouts agree semantically, including the country bar chart. The embedded DataModel was unchanged. The [native technical PDF](media/technical/financial_reporte_completo_hq.pdf) and current PNG previews show this edition.

The current six-page evidence pack is `output/pdf/financial_c3_release_evidence.pdf`; its machine-readable contract is `release/financial-c3-manifest.json`.

To keep that contract stable across Windows and Linux, text artifacts (`.csv`, `.sql`, and `.tmdl`) are measured and hashed after UTF-8/LF canonicalization. Binary artifacts such as PBIX, PBIT, PNG, PDF, and GZip retain exact-byte sizes and SHA-256 values. Every manifest entry declares the mode used.

The compiled PBIT gate validates page identity against the explicit `ordinal` values `0–3`. It does not depend on the physical order of the `sections` array because `pbi-tools Core` may serialize that array differently across operating systems while preserving each page's semantic ordinal.

## Boundaries

- The redesign does not invent new data or change a reconciled DAX formula.
- The PBIX proves the embedded snapshot result; a fresh source refresh still requires a restored `AdventureWorksDW2019` database.
- The current country comparison does not depend on map/geocoding services.
- The matrix keeps seven financial measures for auditability and may require horizontal scrolling at smaller-than-fit-to-page zoom levels.

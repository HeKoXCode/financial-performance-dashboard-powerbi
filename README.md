# Financial Performance Dashboard | Power BI

[![Power BI](https://img.shields.io/badge/Power%20BI-F2C811?logo=powerbi&logoColor=black)](https://powerbi.microsoft.com/)
[![Dataset](https://img.shields.io/badge/Dataset-AdventureWorksDW2019-1F4E78)](https://learn.microsoft.com/en-us/sql/samples/adventureworks-install-configure)
[![FIN C3](https://img.shields.io/badge/Portfolio%20audit-FIN--C3%20verified-2F75B5)](DOCS/c2_c3_verification.md)

I built this executive Power BI case study so you can examine revenue, product cost, freight, tax, and profitability in one reconciled financial model. When you open it, you will find a decision-first overview, margin and prior-year drivers, a strictly scoped USA drill-down, and definitions close to their DAX implementation.

> Portfolio stage: **FIN-S1 through FIN-C3 completed and validated**. I included the analytical release, the full dashboard redesign, and the evidence you need to review both.

## Dashboard preview

### Executive overview

![Executive overview](Images/executive_overview.png)

### Margin and LY drivers

![Margin and LY drivers](Images/overview.png)

### USA geographic drill-down

![USA geographic drill-down](Images/usa_detailed.png)

### Definitions and sources

![Definitions and sources](Images/glossary.png)

## Executive finding

In my analysis, the strongest complete year in the snapshot is **2013**, with **$16.4M** in revenue: **55.7%** of the full sample and **+179.9%** versus 2012. Its gross margin is **41.4%** and net margin is **30.9%**.

I recommend protecting the bicycle mix, which contributes **96.5%** of revenue, and prioritizing the United States and Australia, which together contribute **62.8%**. When you interpret 2014, do not treat it as a full-year decline: the source ends on **2014-01-28**.

## Analytical objective

I designed the report so you can answer four connected questions:

- Is revenue growth translating into stable gross and net profitability?
- How much revenue is absorbed by product cost, freight, and tax?
- Which countries, states, provinces, cities, and product categories concentrate performance?
- Are current KPIs improving or deteriorating against the same selected period last year?

## FIN-C2/C3 dashboard redesign

For FIN-C2/C3, I completely redesigned the audited legacy layout. When you navigate the report, you will find **consistent four-page navigation**, a KPI-first executive page, a restrained chart inventory, a fixed USA scope cue, and a grouped methodology page.

- I replaced four gauges with compact, directly comparable KPI cards.
- I reduced three country/state maps to one country map and kept state analysis on the USA page.
- I rebuilt the executive page around headline KPIs, a shared-unit period trend, an evidence-backed finding, a recommended action, and the partial-period warning.
- I enlarged the USA matrix for traceability and disabled scatter labels to eliminate collisions while preserving native tooltips.
- I added alternative text to every visible non-decorative visual and fitted every page to the 1280×720 canvas used for the verified 1920×1080 captures.

You can review my design decisions, before/after audit, sizing contract, and validation scope in [DOCS/c2_c3_verification.md](DOCS/c2_c3_verification.md).

## KPI contract

| Layer | Definition | Interpretation |
|---|---|---|
| Revenue | `SUM(FactInternetSales[SalesAmount])` | Sales scale in the active filter context |
| Gross profit | Revenue − COGS | Profit after product cost |
| Net profit | Revenue − COGS − Freight − Tax | Portfolio operating result |
| Gross margin | Gross profit / Revenue | Product economics |
| Net margin | Net profit / Revenue | Result after the modeled costs |
| Operational cost ratio | (COGS + Freight) / Revenue | Product and fulfillment cost pressure; excludes tax |
| LY | Same selected period one year earlier | Like-for-like time comparison through `SAMEPERIODLASTYEAR` |

I use `FactInternetSales[OrderDateKey] → DimDate[DateKey]` as the active calendar relationship. As you filter the report, all YTD and LY measures follow the business event used by the documented period: order date. You can inspect the complete 35-measure catalog in [DOCS/dax_measure_catalog.md](DOCS/dax_measure_catalog.md).

## What each page answers

| Page | Decision supported |
|---|---|
| Executive Overview | What happened, why it matters, and which action deserves priority? |
| Drivers de margen y LY | How do revenue, costs, margins, geography, and prior-year comparisons behave? |
| Geographic Drill-down | Which US states and cities drive revenue and gross margin? |
| Definiciones y fuentes | What does each KPI mean, which date controls it, and what are the data limitations? |

## Data source and scope

- **Exact source:** I used Microsoft's official `AdventureWorksDW2019.bak` data warehouse sample, documented on [Microsoft Learn — AdventureWorks sample databases](https://learn.microsoft.com/en-us/sql/samples/adventureworks-install-configure) and in the [Microsoft SQL Server samples repository](https://github.com/microsoft/sql-server-samples/tree/master/samples/databases/adventure-works).
- **Fact table:** `FactInternetSales`, with **60,398 embedded rows** in the audited PBIX.
- **Observed order-date period:** **2010-12-29 through 2014-01-28**; 2010 and 2014 are partial years.
- **Reporting currency:** I display monetary values with `$`, without exchange-rate conversion or currency normalization. Interpret them as the AdventureWorks sample reporting currency, not audited statutory USD.
- **Units:** I display monetary values in millions (`mill.`) on executive cards and ratios as percentages; detailed visuals retain their visual-specific display units.

### USA scope guarantee

On the USA page, I keep one stable page-level filter:

```text
DimCustomer[CountryRegionCode] = "US"
```

I built its visuals with `DimCustomer` geography fields so the filter acts on the effective dimension. My offline embedded-table check found 7,819 US customers across 22 state names and no records from the other five countries in that scope. You can review the full evidence in [DOCS/s1_s3_verification.md](DOCS/s1_s3_verification.md).

## DAX reconciliation

I recorded **68 evaluated contexts** in `DOCS/dax_reconciliation.csv` so you can inspect the reconciliation directly:

| Granularity | Contexts |
|---|---:|
| Total | 1 |
| Year | 5 |
| Country | 6 |
| State/province | 53 |
| Product category | 3 |

In every context, you can verify these identities with a maximum recorded residual of exactly **0**:

```text
Gross profit = Revenue − COGS
Net profit   = Revenue − COGS − Freight − Tax
Gross margin = Gross profit / Revenue
Net margin   = Net profit / Revenue
```

I also used the year-level rows to verify that each available LY value equals the preceding year's current revenue. See [DOCS/i1_i3_verification.md](DOCS/i1_i3_verification.md) for my verification record and the commands you can use to reproduce it.

## Independent SQL release gate

For FIN-C1, I added a second calculation path that does not execute DAX. The release check loads a committed, compressed, non-PII projection of the embedded PBIX snapshot into an in-memory SQLite database and uses [sql/reconcile_kpis.sql](sql/reconcile_kpis.sql) to recompute the financial identities from base columns.

- **60,398** source facts are loaded.
- **68** total, year, country, state, and category contexts are independently recomputed.
- Money must match the DAX evidence within **$0.01**; ratios within **1e-10**.
- The generated result is committed as [DOCS/sql_reconciliation.csv](DOCS/sql_reconciliation.csv).

You can use this evidence to verify agreement between SQL and the DAX outputs for the distributed snapshot. I deliberately do not present it as a connection to a production SQL Server instance.

## Reproduce the report

### Fast path: inspect the embedded result

1. Download `Financial_Report.pbix`.
2. Open it with Power BI Desktop.
3. Review the four pages and confirm the US page filter in the Filters pane.
4. Compare the visible totals with `DOCS/dax_reconciliation.csv`.

I embedded the audited snapshot in the PBIX so you can inspect the result without a database connection.

### Refreshable template

If you want to refresh the model, use `Financial_Report.pbit`, the data-free template I compiled from the reviewable source. Restore `AdventureWorksDW2019.bak`, open the template, point it to your SQL Server instance when prompted, and refresh.

I set the documented default source to `localhost\SQLEXPRESS` and load `DimCustomer` from the same database. You will not need a workstation-only Excel path.

### Repeat the source transformations and checks

```powershell
python scripts/update_financial_report_s1_s3.py
python scripts/update_financial_report_i1_i3.py
python scripts/update_financial_report_c2_c3.py
python scripts/validate_s1_s3.py
python scripts/validate_i1_i3.py
python scripts/validate_c2_c3.py
python scripts/run_sql_reconciliation.py
python scripts/validate_pbit_package.py Financial_Report.pbit
python scripts/build_release_manifest.py --check
```

With the PBIX open in Power BI Desktop on Windows, you can also regenerate the live model and reconciliation evidence:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/apply_live_model_i1.ps1
powershell -ExecutionPolicy Bypass -File scripts/export_dax_reconciliation.ps1
python scripts/sync_report_layout_to_pbix.py
```

I wrote the PowerShell scripts to discover the local Analysis Services endpoint created by the open report. I also made the Python transformations idempotent and configured the GitHub workflow to fail if the committed report source drifts from their output.

### Build the distributable evidence

Install the pinned release-only dependencies, then rebuild and validate the six-page evidence pack:

```powershell
python -m pip install -r requirements-release.txt
python scripts/build_release_evidence.py
python scripts/validate_release_artifacts.py
```

You can inspect the machine-readable release contract in [release/financial-c3-manifest.json](release/financial-c3-manifest.json). I recorded KPI values, the dashboard contract, tolerances, tool versions, artifact hashes, and expected reasons for variation there. The corresponding evidence pack is [output/pdf/financial_c3_release_evidence.pdf](output/pdf/financial_c3_release_evidence.pdf). With the PBIX open in Power BI Desktop, you can regenerate clean 1920×1080 captures of all four pages on Windows with `scripts/capture_powerbi_pages.ps1`.

I configured CI to download the pinned Linux build of `pbi-tools Core 1.2.0`, verify the installer SHA-256, compile a fresh data-free PBIT, and validate its package, model, relationships, pages, narrative, and absence of private workstation references.

## Version-control format

I use the `pbi-tools`-compatible `Financial_Report/` source as the canonical reviewable artifact: report JSON plus TMDL semantic model. I also distribute the compiled PBIT and the embedded-data PBIX so you can choose between source review, refresh, and direct inspection.

I deliberately did not fabricate a native `.pbip`. Microsoft currently documents Power BI Desktop projects as a preview feature that must be enabled in Desktop; converting only the semantic model while claiming an unverified native report project would weaken reproducibility. With the source I adopted, you still get text diffs, automated checks, a rebuildable template, and a tested PBIX. See [Power BI Desktop projects](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-overview) and [TMDL semantic model projects](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-dataset).

## Repository structure

```text
.
├── Financial_Report.pbix       # Report with embedded audited sample data
├── Financial_Report.pbit       # Refreshable, data-free template
├── Financial_Report/           # Reviewable report JSON and TMDL model source
├── Images/                     # Four verified 1920×1080 report previews
├── DOCS/
│   ├── dax_measure_catalog.md  # Formula, unit, context, and LY contract
│   ├── dax_reconciliation.csv  # Numerical evidence at five granularities
│   ├── sql_reconciliation.csv  # Independent SQL result for the same 68 contexts
│   ├── i1_i3_verification.md   # Intermediate-stage verification record
│   ├── c1_verification.md      # FIN-C1 analytical release-gate record
│   └── c2_c3_verification.md   # FIN-C2/C3 dashboard-redesign record
├── DATA/                       # Compressed non-PII SQL input projection
├── sql/                        # Independent KPI query
├── release/                    # Machine-readable release manifest and hashes
├── output/pdf/                 # Six-page distributable evidence pack
├── scripts/                    # Idempotent transforms, capture, build, and validation
└── .github/workflows/          # Automated source and evidence checks
```

## What I completed in this portfolio release

- **FIN-S1 — USA consistency:** I added a stable US page filter, an effective geography dimension, an embedded-data scope check, and an interaction review.
- **FIN-S2 — documentation:** I documented the exact source, period, row count, units, page decisions, reproduction paths, and limitations.
- **FIN-S3 — presentation:** I corrected terminology and implemented a restrained visual system, cleaner navigation, and unclipped definitions.
- **FIN-I1 — analytical model:** I corrected the active order-date relationship, normalized 35 measures, added descriptions/folders and four diagnostic identities, and reconciled 68 filter contexts.
- **FIN-I2 — versionability:** I synchronized the TMDL/report source, compiled the PBIT, added repeatable update/export scripts and automated drift checks, and documented my native-PBIP decision.
- **FIN-I3 — analytical narrative:** I rebuilt the four-page flow around result, driver, action, drill-down, and data contract, then added exact findings and partial-period warnings.
- **FIN-C1 — analytical release:** I added independent SQL/DAX reconciliation, pinned PBIT compilation in CI, artifact/KPI hashes, an expected-variation policy, automated visual capture, and a validated PDF evidence pack.
- **FIN-C2 — dashboard redevelopment:** I rebuilt the four pages around a consistent navigation shell, KPI-first hierarchy, one purposeful map, a larger USA detail surface, and grouped definitions.
- **FIN-C3 — visual release:** I verified sizing, chart selection, accessibility metadata, source/PBIX/PBIT consistency, clean captures, and a new FIN-C3 manifest/PDF evidence pack.

## Limitations you should consider

- AdventureWorks is a synthetic Microsoft sample, not a live company ledger.
- The snapshot begins on 2010-12-29 and ends on 2014-01-28; 2010 and 2014 cannot be compared as complete fiscal years.
- When you use `SAMEPERIODLASTYEAR`, remember that it follows the selected calendar window. Base annual interpretations on complete years or aligned partial periods.
- Currency conversion, budgets, forecasts, accounting-close adjustments, and scenario planning are outside the current model.
- Maps depend on Power BI geocoding. Explicit country scope reduces ambiguity but does not replace governed latitude/longitude data.
- You will find standard tooltips and page navigation, but I did not implement a dedicated tooltip page or drillthrough target.
- Native PBIP export remains outside the committed artifact for the preview/verification reason documented above.
- Use my independent SQL gate to validate the committed analytical projection; do not interpret it as evidence of source-system availability, permissions, refresh duration, or a production database SLA.

## Tools

- Power BI Desktop and DAX
- SQL Server / AdventureWorksDW2019
- TMDL and `pbi-tools`-compatible extracted source
- PowerShell live-model automation
- Python standard-library transformation and validation

## Attribution

I created the original report and analytical model as **Percy Ignacio Marzoratti Hill**. You can trace my portfolio hardening, reproducibility checks, and repository maintenance in the Git history.

# Financial Performance Dashboard | Power BI

[![Power BI](https://img.shields.io/badge/Power%20BI-F2C811?logo=powerbi&logoColor=black)](https://powerbi.microsoft.com/)
[![Dataset](https://img.shields.io/badge/Dataset-AdventureWorksDW2019-1F4E78)](https://learn.microsoft.com/en-us/sql/samples/adventureworks-install-configure)
[![FIN S1–S3](https://img.shields.io/badge/Portfolio%20audit-FIN--S1%E2%80%93S3%20complete-2F75B5)](DOCS/s1_s3_verification.md)

An executive Power BI case study that connects revenue, product cost, freight, tax, and profitability into a consistent financial performance model. The report combines a global view with a strictly scoped USA detail page and keeps every business definition close to its DAX implementation.

> Portfolio stage: **FIN-S1, FIN-S2, and FIN-S3 completed**. The next planned stage is the intermediate analytical review of DAX and KPI reconciliation.

## Dashboard preview

### Global financial overview

![Global financial overview](Images/overview.png)

### USA detail

![USA detail page](Images/usa_detailed.png)

### Financial glossary

![Financial glossary](Images/glossary.png)

## Analytical objective

The report is designed to answer four connected questions:

- Is revenue growth translating into stable gross and net profitability?
- How much revenue is absorbed by product cost and freight?
- Which countries, states, provinces, and cities concentrate performance?
- Are current KPIs improving or deteriorating against the same period last year?

The model centralizes the calculations as reusable DAX measures instead of duplicating logic in individual visuals.

## KPI framework

| Layer | Measures | Business interpretation |
|---|---|---|
| Revenue | Revenue, accumulated revenue, prior-year revenue | Scale and growth trajectory |
| Cost | COGS, freight, COGS %, operational cost ratio | Cost discipline and operating efficiency |
| Profitability | Gross profit, net profit, gross margin, net margin | Quality and sustainability of earnings |
| Comparison | Current period vs LY | Direction and magnitude of change |

Key definitions are aligned with the measures in the semantic model:

- **Gross profit** = Revenue − COGS.
- **Net profit** = Revenue − COGS − Freight − Tax.
- **Operational cost ratio** = (COGS + Freight) / Revenue.
- **LY** means the same selected period one year earlier and uses `SAMEPERIODLASTYEAR`.

## What each page answers

| Page | Decision supported |
|---|---|
| Home | Which analytical route should the reader follow: global results, USA detail, or metric help? |
| Global financial report | Are revenue, margins, and operating cost ratios moving in a healthy direction, and where is revenue concentrated? |
| USA detail | Which US states and cities drive revenue and gross margin, and how has the relationship evolved by year? |
| Help and glossary | How is each financial KPI defined and how should LY and YTD be interpreted? |

## Data source and scope

- **Exact source:** Microsoft's official `AdventureWorksDW2019.bak` data warehouse sample, documented on [Microsoft Learn — AdventureWorks sample databases](https://learn.microsoft.com/en-us/sql/samples/adventureworks-install-configure) and in the [Microsoft SQL Server samples repository](https://github.com/microsoft/sql-server-samples/tree/master/samples/databases/adventure-works).
- **Fact table:** `FactInternetSales`, with **60,398 embedded rows** in the audited PBIX.
- **Observed order-date period:** **2010-12-29 through 2014-01-28**.
- **Reporting currency:** the model displays monetary values with `$`; it does not implement exchange-rate conversion or currency normalization. Values should therefore be interpreted as the AdventureWorks sample reporting currency, not as audited statutory USD.
- **Units:** executive cards display monetary values in **millions** (`mill.`); ratios use percentages; detailed visuals retain their visual-specific display units.

### USA scope guarantee

The USA page has one stable page-level filter:

```text
DimCustomer[CountryRegionCode] = "US"
```

The page visuals use `DimCustomer` geography fields, so the filter is attached to that effective dimension. An offline check of the embedded table found 7,819 US customer rows across 22 state names. The filtered set contained no Canada, Germany, France, United Kingdom, or Australia records. Example valid members include California, Washington, Texas, Florida, and New York. Full evidence and the repeatable checks are in [DOCS/s1_s3_verification.md](DOCS/s1_s3_verification.md).

## Reproduce the report

### Fast path: inspect the embedded result

1. Download `Financial_Report.pbix`.
2. Open it with Power BI Desktop.
3. Navigate from Home to the global report, USA detail, and glossary pages.
4. Confirm the USA page filter in the Filters pane.

The PBIX contains the audited sample snapshot, so the documented result can be inspected without a database connection.

`Financial_Report.pbit` is also included as a data-free template compiled from the reviewable source. Use it when you want to connect and refresh against your own restored AdventureWorks instance instead of inspecting the embedded snapshot.

### Full refresh path

1. Install SQL Server and restore the official `AdventureWorksDW2019.bak` sample.
2. Make the restored database available at `localhost\SQLEXPRESS`, or update the source in Power BI Desktop for your SQL Server instance.
3. Open `Financial_Report.pbix`, set credentials for the local SQL Server source, and refresh.
4. Run the repository checks:

```powershell
python scripts/update_financial_report_s1_s3.py
python scripts/validate_s1_s3.py
```

The extracted `Financial_Report/` folder is the reviewable Power BI source representation. The update script is idempotent and the validator fails when the USA filter, terminology, style rules, source privacy, or documentation regress.

## Repository structure

```text
.
├── Financial_Report.pbix       # Report with embedded audited sample data
├── Financial_Report.pbit       # Data-free template compiled from source
├── Financial_Report/           # Extracted, reviewable Power BI project source
├── Images/                     # Portfolio previews for three report pages
├── DOCS/                       # Verification evidence and audit notes
├── scripts/                    # Idempotent transformation and validation
└── .github/workflows/          # Automated source checks
```

## FIN-S1 to FIN-S3 improvements

- **FIN-S1 — USA consistency:** verified one stable `US` page filter; checked the embedded geography values; reviewed maps, tooltips, and page navigation/drill behavior.
- **FIN-S2 — documentation:** identified the exact sample version, date range, row count, reporting units, business question per page, reproduction paths, and limitations.
- **FIN-S3 — presentation quality:** corrected `LI` to `LY`; aligned terminology with DAX; standardized Segoe UI and a restrained navy/blue/orange palette; disabled decorative shadows and plot-area images; hid non-informative flags, stars, arrows, and duplicate headings; rewrote the glossary to avoid clipping.

## Limitations

- AdventureWorks is a synthetic Microsoft sample, not a live company ledger.
- The embedded snapshot ends on 2014-01-28 and is intended for portfolio demonstration.
- Currency conversion, budgets, forecasts, and accounting-period close adjustments are outside the current model.
- Maps rely on Power BI geocoding; country filters reduce ambiguous state/province names, but geospatial accuracy still depends on the Power BI map service.
- The report uses standard visual tooltips and page navigation; there is no dedicated tooltip page or drillthrough target in the current scope.
- KPI logic has been checked for naming and glossary consistency in S1–S3; full numerical reconciliation is scheduled for the intermediate stage.

## Tools

- Power BI Desktop
- DAX
- SQL Server / AdventureWorksDW2019
- `pbi-tools` compatible extracted source
- Python standard-library validation

## Attribution

Original report and analytical model by **Percy Ignacio Marzoratti Hill**. Portfolio hardening, reproducibility checks, and repository maintenance are tracked in Git history.

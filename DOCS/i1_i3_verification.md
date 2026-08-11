# FIN-I1 to FIN-I3 verification record

Audit date: **2026-08-11**

Scope: **DAX reconciliation, versionable Power BI artifacts, and analytical narrative**

## Result

| Stage | Status | Verified outcome |
|---|---|---|
| FIN-I1 | Complete | Order-date model path corrected; 35 measures normalized and documented; 68 analytical contexts reconciled with zero residual |
| FIN-I2 | Complete | TMDL/report source synchronized; PBIT compiled; PBIX retained with embedded evidence; repeatable scripts and CI drift checks added |
| FIN-I3 | Complete | Four-page narrative rebuilt around executive result, drivers, geographic detail, definitions, action, and limitations |

## FIN-I1 — analytical model and DAX

### Model correction

The audited model previously related `DimDate` actively to `FactInternetSales[DueDateKey]`, although the README period and business analysis were based on order date. The active relationship is now:

```text
FactInternetSales[OrderDateKey] → DimDate[DateKey]
```

The customer relationship was also normalized to one-direction dimension-to-fact propagation. This removes unnecessary bidirectional ambiguity while preserving the USA page's effective `DimCustomer` scope.

### Measure normalization

- 35 measures are present, with no encoding-corrupted duplicates.
- Base measures reference the fact columns once and derived measures reuse those bases.
- Profit, margin, cost-ratio, YTD, LY, and variance definitions are centralized.
- Descriptions and display folders expose the business contract in the semantic model.
- Four hidden diagnostic measures make the accounting identities executable.

The full contract is documented in [dax_measure_catalog.md](dax_measure_catalog.md).

### Numerical evidence

The live Power BI model was queried through its local Analysis Services endpoint. The committed [dax_reconciliation.csv](dax_reconciliation.csv) contains:

| Granularity | Rows | Gross-profit max residual | Net-profit max residual | Gross-margin max residual | Net-margin max residual |
|---|---:|---:|---:|---:|---:|
| Total | 1 | 0 | 0 | 0 | 0 |
| Year | 5 | 0 | 0 | 0 | 0 |
| Country | 6 | 0 | 0 | 0 | 0 |
| State/province | 53 | 0 | 0 | 0 | 0 |
| Product category | 3 | 0 | 0 | 0 | 0 |
| **All contexts** | **68** | **0** | **0** | **0** | **0** |

The year rows also verify the LY chain: when a prior-year value exists, it equals the current revenue recorded for the immediately preceding year. State and category margins contain multiple distinct results, providing a control that the measures respond to row/filter context rather than repeating a single global scalar.

### Reconciled headline values

- Total revenue: **$29,358,677.22**.
- Total gross margin: **41.15%**.
- Total net margin: **30.65%**.
- 2013 revenue: **$16,351,550.34**, or **55.7%** of total.
- 2013 revenue growth versus 2012: **179.9%**.
- 2013 gross margin: **41.4%**; net margin: **30.9%**.
- United States plus Australia: **62.8%** of revenue.
- Bicycles: **96.5%** of revenue.

## FIN-I2 — versionability and reproduction

The repository now has three complementary deliverables:

1. `Financial_Report.pbix`: the inspected report with embedded AdventureWorks evidence.
2. `Financial_Report.pbit`: a refreshable, data-free template compiled from source.
3. `Financial_Report/`: text-reviewable report JSON and TMDL semantic model source.

The update scripts are idempotent, the live-model script applies the model contract to an open PBIX, the reconciliation exporter rebuilds the CSV evidence, and the PBIX synchronizer embeds the versioned report layout without replacing the data model.

### Build record

- Power BI Desktop: `2.156.951.0`.
- PBIT compiler: `pbi-tools Core 1.2.0`.
- Round-trip extractor: `pbi-tools Desktop 1.2.0`.
- `Financial_Report.pbix` SHA-256: `C4E8F36CF1892C5AEF6063E1EDA17C82BB6FAF7AB99B2756ECC5557C04E4B8B1`.
- `Financial_Report.pbit` SHA-256: `AABBF20F22A6425CF8E82D924A924A3D84E6607C7B7ACA86A140744608EDA138`.
- `dax_reconciliation.csv` SHA-256: `6D036E5570D149CE8B00A9CD2928E48DA413D8E1F8E014983131C5EE083A39BA`.

The PBIT was extracted again after compilation. The round trip preserved the 35 measures, active `OrderDateKey` relationship, four final page names, and absence of private workstation references.

### Native PBIP decision

A `.pbip` pointer was not manufactured manually. Microsoft documents Power BI Desktop projects as a preview feature that must be enabled in Desktop. This environment did not have a verified native PBIP save path enabled, and a semantic-model-only conversion would not prove that the report definition reopens correctly. The repository therefore uses the already tested TMDL/report source plus PBIT as its canonical versionable format.

References:

- [Power BI Desktop projects](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-overview)
- [TMDL semantic model projects](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-dataset)

This is an explicit reproducibility decision, not a claim that the legacy extracted folder is a native PBIP project.

## FIN-I3 — analytical narrative

The final flow is:

1. **Executive Overview** — states the strongest complete-year result, margin quality, recommended commercial focus, and partial-period warning.
2. **Drivers de margen y LY** — exposes revenue, costs, margins, geographic distribution, and prior-year comparisons.
3. **Geographic Drill-down** — keeps a stable US scope and supports state/city inspection.
4. **Definiciones y fuentes** — records formulas, active order-date relationship, source, coverage, units, and interpretive limitations.

All four committed previews are **1920×1080** and were visually inspected after synchronizing the final PBIX.

## Repeat the verification

From the repository root:

```powershell
python scripts/update_financial_report_s1_s3.py
python scripts/update_financial_report_i1_i3.py
python scripts/validate_s1_s3.py
python scripts/validate_i1_i3.py
```

For a live-model regeneration, open `Financial_Report.pbix` in Power BI Desktop and run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/apply_live_model_i1.ps1
powershell -ExecutionPolicy Bypass -File scripts/export_dax_reconciliation.ps1
```

The first script updates the relationship and measures. The second queries the active model and rewrites `DOCS/dax_reconciliation.csv`. Neither script contains credentials or a workstation-specific source path.

## Remaining boundary

FIN-I1–I3 closes the intermediate portfolio scope. The next audit item is **FIN-C1**: automate a distributable analytical release and publish the validated branch. Forecasting, budgets, FX conversion, and partial-period normalization remain deliberately outside the current business model.

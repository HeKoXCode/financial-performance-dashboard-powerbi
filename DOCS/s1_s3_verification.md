# FIN-S1 to FIN-S3 verification record

Audit date: **2026-08-11**
Scope: **USA consistency, portfolio documentation, and visual/text cleanup**

## Result

| Stage | Status | Evidence |
|---|---|---|
| FIN-S1 | Complete | Stable `DimCustomer[CountryRegionCode] = "US"` page filter, embedded-data export check, and visual interaction review |
| FIN-S2 | Complete | Exact source/version, period, row count, units, decision per page, reproduction paths, and limitations documented |
| FIN-S3 | Complete | LI/LY correction, terminology alignment, simplified style, decorative-image retirement, and compact glossary |

## FIN-S1 — USA scope

The extracted report source contains exactly one page-level filter in:

```text
Financial_Report/Report/sections/002_Detalle USA/filters.json
```

The filter targets `DimCustomer[CountryRegionCode]` and accepts only the literal `'US'`. This is the effective dimension used by the USA matrix and charts. An earlier filter on `DimGeography` did not propagate through the inactive customer-geography relationship; render verification exposed that defect and the final implementation corrects it. The USA page's visual queries contain no hard-coded `'AU'`, `'CA'`, `'DE'`, `'FR'`, or `'GB'` alternative.

### Embedded-data check

The PBIX tables were exported offline with `pbi-tools`. The resulting `DimCustomer.csv` was validated with:

```powershell
python scripts/validate_us_scope.py <export-directory>\DimCustomer.csv
```

Observed result:

```text
USA customer scope validation PASSED
  - full customer dimension: 18,484 rows
  - US scope: 7,819 rows, 22 unique state names
  - non-US rows in US scope: 0
  - sample valid members include Alabama, Arizona, California, Florida, New York, Texas, and Washington
```

Full-dimension control counts were `AU=3,591`, `CA=1,571`, `DE=1,780`, `FR=1,810`, `GB=1,913`, and `US=7,819`. This proves the customer dimension contains international records while the USA page deliberately limits its scope.

### Map, tooltip, and navigation review

- The global report retains three filled-map views: country revenue and country-constrained state/province detail for Canada and France. Their explicit country context reduces ambiguous geocoding.
- The USA page uses `DimCustomer` state/city detail under the page-level US filter; every standard tooltip inherits the same filter context.
- A final Power BI Desktop render showed only US members (for example Alabama, Arizona, California, Florida, Georgia, Illinois, Kentucky, Massachusetts, and Minnesota); Alberta, Bayern, Brandenburg, British Columbia, Charente-Maritime, England, and other former leaks were absent.
- The current report has no dedicated tooltip page and no drillthrough target. That is documented as a limitation rather than claimed as a feature.
- Action buttons provide page navigation and a back path. The USA filter remains a page-level rule and does not depend on a user's slicer selection.

## FIN-S2 — documented data contract

- Source: official Microsoft `AdventureWorksDW2019.bak` sample.
- Model mode: imported data snapshot in the audited PBIX.
- `FactInternetSales`: 60,398 rows.
- `OrderDateKey` range: 2010-12-29 to 2014-01-28.
- Monetary display: `$` format, with no FX conversion or currency normalization.
- Units: executive monetary cards in millions (`mill.`), ratios in percentages.
- Each of the four pages now states or documents the business decision it supports.
- Both inspection-only and full SQL Server refresh paths are documented in the README.

## FIN-S3 — consistency and presentation

- Corrected the gauge label `COGS % VS LI` to `COGS % vs LY`.
- Standardized visible typography on Segoe UI and reduced the palette to navy, blue, orange, red, black, and white roles.
- Disabled active shadow/glow settings and removed decorative plot-area bitmap backgrounds.
- Hid non-informative logos, stock illustrations, flags, stars, globe, static arrow icons, duplicate date/title elements, and a duplicate global heading while preserving them in source for reversibility.
- Replaced decorative headings with `REPORTE FINANCIERO` and `DETALLE USA`.
- Rebuilt the glossary with compact 11 pt definitions and a 28 pt heading to prevent its former scrollbar/text clipping.
- Corrected net profit to match DAX: `Revenue − COGS − Freight − Tax`.
- Replaced the workstation-specific SQL Server name with the documented generic `localhost\SQLEXPRESS` source.
- Replaced the workstation-only `DimCustomer.xlsx` dependency with a direct `AdventureWorksDW2019.dbo.DimCustomer` query enriched from `DimGeography`, so the distributed PBIT has one reproducible SQL Server source.

## Automated regression check

Run from the repository root:

```powershell
python scripts/update_financial_report_s1_s3.py
python scripts/validate_s1_s3.py
```

The validator checks all report JSON, the four-page topology, the exact USA filter, absence of non-US visual filters on the USA page, hidden decorative visuals, typography, plot backgrounds, shadow/glow state, terminology, SQL source privacy, and required README evidence.

## Boundary of this stage

S1–S3 establishes a credible, internally consistent portfolio baseline. It does not yet claim full financial reconciliation of every DAX result. Numerical reconciliation, time-intelligence edge cases, and KPI target design belong to the next intermediate stage.

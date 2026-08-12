# FIN-C1 analytical release verification

Audit date: **2026-08-12**

Status: **Complete locally; ready to publish**

> Historical analytical gate: FIN-C1 remains the numerical/reproducibility baseline. The current dashboard layout and current release artifacts are verified in [c2_c3_verification.md](c2_c3_verification.md), `release/financial-c3-manifest.json`, and `output/pdf/financial_c3_release_evidence.pdf`.

## Result

FIN-C1 turns the Power BI case study into a controlled analytical release. The repository now has an independent SQL calculation path, a pinned CI compilation gate for the data-free template, machine-readable KPI and artifact hashes, clean report-page evidence, and a deterministic six-page PDF handoff.

## 1. Independent SQL reconciliation

The input is `DATA/financial_sql_input.csv.gz`, a deterministic non-PII analytical projection created from the exact embedded PBIX snapshot. It contains the fact keys and base financial columns required for the audit plus only the country, state, and product-category labels needed for the published contexts.

`sql/reconcile_kpis.sql` recomputes revenue, COGS, freight, tax, gross profit, net profit, gross margin, net margin, and prior-year revenue in SQLite without evaluating DAX. `scripts/run_sql_reconciliation.py` then compares those results with the live-model DAX evidence.

| Control | Result |
|---|---:|
| Loaded fact rows | 60,398 |
| SQL contexts | 68 |
| DAX contexts | 68 |
| Money tolerance | $0.01 absolute |
| Ratio tolerance | 1e-10 absolute |
| Context mismatches | 0 |

This is an independent formula and engine path for the distributed snapshot. It does not claim to test production SQL Server connectivity, credentials, orchestration, or refresh SLAs.

## 2. Compiled template gate

The GitHub workflow downloads `pbi-tools Core 1.2.0` for Linux and verifies the release archive against SHA-256 `AC3A3434F837E49FAB1BA69A29CAC78B3FB11FC1476C91A7EE87A85EF0131D5E` before execution. It compiles `Financial_Report/` into a fresh PBIT and checks:

- the package is data-free;
- all 35 measures are present;
- the active explicit date relationship uses `OrderDateKey`;
- no relationship is bidirectional;
- the four final report pages and executive narrative are present;
- no private user path, workstation name, or `File.Contents` dependency remains.

The compiled template is uploaded as a CI artifact, while the repository keeps the locally inspected PBIT for direct use.

## 3. KPI, hash, and variation contract

`release/financial-c1-manifest.json` records:

- source identity, row count, date coverage, and partial years;
- the model contract, page/measure/context counts, and tolerances;
- headline total, 2013, geographic, and product-mix KPIs;
- Power BI, pbi-tools, Python, and SQL-engine versions;
- byte size and SHA-256 for the PBIX, PBIT, source evidence, SQL/DAX outputs, model source, images, and PDF;
- explicit cases in which each class of hash may legitimately change.

`python scripts/build_release_manifest.py --check` fails when a tracked artifact changes without rebuilding the contract.

## 4. Visual and PDF evidence

`scripts/capture_powerbi_pages.ps1` captures the rendered embedded-snapshot Power BI canvas at 1920×1080 after clearing edit/selection state and moving the cursor outside the report. The four final images were inspected for page identity, clipping, tooltips, cursor overlays, and editing controls. This is visual evidence of the distributed PBIX; source-system refresh requires the PBIT and a restored AdventureWorksDW2019 database.

`scripts/build_release_evidence.py` converts those images and the reconciled KPI evidence into `output/pdf/financial_c1_release_evidence.pdf`. The build is deterministic; the validator checks six 16:9 pages and required headings. All six rendered pages were visually inspected after generation.

## 5. Automated reproduction

From the repository root:

```powershell
python scripts/update_financial_report_s1_s3.py
python scripts/update_financial_report_i1_i3.py
python scripts/validate_s1_s3.py
python scripts/validate_i1_i3.py
python scripts/run_sql_reconciliation.py
python scripts/validate_pbit_package.py Financial_Report.pbit
python -m pip install -r requirements-release.txt
python scripts/build_release_evidence.py
python scripts/validate_release_artifacts.py
python scripts/build_release_manifest.py --check
```

The CI workflow repeats the source-drift checks, SQL/DAX reconciliation, committed release validation, and clean PBIT compilation on Ubuntu.

## Remaining limitations

- AdventureWorks is synthetic sample data and does not demonstrate a live enterprise refresh.
- SQL independence covers formulas and grouped results, not upstream availability or security.
- The PBIX is required for offline embedded-data inspection; the PBIT requires a restored AdventureWorksDW2019 database to refresh.
- Power BI Desktop is still required to render native visuals and regenerate screenshots.
- Native PBIP remains excluded for the preview and verification reason documented in the README.

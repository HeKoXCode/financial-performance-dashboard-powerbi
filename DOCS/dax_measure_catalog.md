# DAX measure catalog

Audit date: **2026-08-11**

Model table: **Tablas de Medidas**

Measure count: **35**

## Evaluation contract

- The active time path is `FactInternetSales[OrderDateKey] → DimDate[DateKey]`.
- Product, customer, geography, and date filters propagate one way from dimensions to the sales fact.
- Monetary measures use the AdventureWorks sample reporting currency displayed with `$`; no FX normalization is applied.
- Ratios are calculated from measures in the current filter context, never by averaging stored row percentages.
- `LY` means the same selected period one year earlier through `SAMEPERIODLASTYEAR(DimDate[Date])`.
- `YTD` means calendar year-to-date through `DATESYTD(DimDate[Date])`.

## Base measures

| Measure | DAX definition | Unit | Filter-context behavior |
|---|---|---|---|
| `Ingresos` | `SUM(FactInternetSales[SalesAmount])` | Currency | Additive by date, product, customer, and geography |
| `COGS` | `SUM(FactInternetSales[TotalProductCost])` | Currency | Additive product cost |
| `Costo Total Envios` | `SUM(FactInternetSales[Freight])` | Currency | Additive freight |
| `Impuestos` | `SUM(FactInternetSales[TaxAmt])` | Currency | Additive tax |
| `Cantidad vendida` | `SUM(FactInternetSales[OrderQuantity])` | Units | Additive quantity |
| `Operaciones` | `COUNTROWS(FactInternetSales)` | Rows | Sales-line count, not distinct orders |
| `Clientes únicos` | `DISTINCTCOUNT(FactInternetSales[CustomerKey])` | Customers | Fact-based so product/date/geography filters remain effective |

## Reconciled profit and cost measures

| Measure | DAX definition | Unit | Meaning |
|---|---|---|---|
| `Costo Total + Envíos` | `[COGS] + [Costo Total Envios]` | Currency | Product cost plus freight; excludes tax |
| `Costos totales` | `[COGS] + [Costo Total Envios] + [Impuestos]` | Currency | Cost basis used by net profit |
| `Utilidad bruta` | `[Ingresos] - [COGS]` | Currency | Revenue after product cost |
| `Utilidad neta` | `[Ingresos] - [Costos totales]` | Currency | Revenue after product cost, freight, and tax |
| `% Margen Bruto` | `DIVIDE([Utilidad bruta], [Ingresos])` | Percentage | Gross profit per unit of revenue |
| `% Margen Neto` | `DIVIDE([Utilidad neta], [Ingresos])` | Percentage | Net profit per unit of revenue |
| `COGS %` | `DIVIDE([COGS], [Ingresos])` | Percentage | Product-cost burden |
| `Ratio Costo Operacional %` | `DIVIDE([Costo Total + Envíos], [Ingresos])` | Percentage | COGS plus freight burden; excludes tax |

## Time intelligence and comparisons

| Measure | DAX definition | Unit | Comparison contract |
|---|---|---|---|
| `Ingresos YTD` | `CALCULATE([Ingresos], DATESYTD(DimDate[Date]))` | Currency | Current calendar YTD |
| `Ingresos Acumulados` | `[Ingresos YTD]` | Currency | Backward-compatible report alias |
| `Ingresos PA` | `CALCULATE([Ingresos], SAMEPERIODLASTYEAR(DimDate[Date]))` | Currency | Revenue for the aligned LY window |
| `Ingresos YTD LY` | `CALCULATE([Ingresos YTD], SAMEPERIODLASTYEAR(DimDate[Date]))` | Currency | Prior-year version of YTD revenue |
| `COGS PA` | `CALCULATE([COGS], SAMEPERIODLASTYEAR(DimDate[Date]))` | Currency | COGS for the aligned LY window |
| `Coste LY` | `CALCULATE([Costo Total + Envíos], SAMEPERIODLASTYEAR(DimDate[Date]))` | Currency | Product cost plus freight for LY |
| `% Margen Bruto PA` | Prior-year `% Margen Bruto` | Percentage | Compatibility name retained for existing visuals |
| `Margen Bruto % LY` | Prior-year `% Margen Bruto` | Percentage | Gross margin for LY |
| `Margen Neto % LY` | Prior-year `% Margen Neto` | Percentage | Net margin for LY |
| `COGS % LY` | Prior-year `COGS %` | Percentage | Product-cost ratio for LY |
| `Ratio Costo Operacional % LY` | Prior-year operational cost ratio | Percentage | COGS plus freight ratio for LY |
| `Ingresos vs LY` | `[Ingresos] - [Ingresos PA]` | Currency | Absolute revenue variance |
| `Ingresos vs LY %` | `DIVIDE([Ingresos vs LY], [Ingresos PA])` | Percentage | Relative revenue variance |
| `Margen bruto vs LY pp` | `[% Margen Bruto] - [Margen Bruto % LY]` | Percentage points | Gross-margin movement |
| `Margen neto vs LY pp` | `[% Margen Neto] - [Margen Neto % LY]` | Percentage points | Net-margin movement |

`PA` is preserved only in original compatibility names. User-facing copy standardizes the label to `LY`.

## Hidden diagnostics

| Measure | Expected result | Purpose |
|---|---:|---|
| `Reconciliación utilidad bruta` | 0 | Checks `Gross profit = Revenue − COGS` |
| `Reconciliación utilidad neta` | 0 | Checks `Net profit = Revenue − COGS − Freight − Tax` |
| `Reconciliación margen bruto` | 0 | Checks gross-margin derivation |
| `Reconciliación margen neto` | 0 | Checks net-margin derivation |
| `KPI_Grafico` | 0 | Hidden compatibility placeholder retained for the original layout |

The reconciliation exporter evaluates the four diagnostic measures at total, year, country, state/province, and product-category levels. Its committed output is [dax_reconciliation.csv](dax_reconciliation.csv).

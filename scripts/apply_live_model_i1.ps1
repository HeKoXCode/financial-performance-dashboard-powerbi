param(
    [int]$Port = 0
)

$ErrorActionPreference = "Stop"

function Find-PowerBIPort {
    $userProfilePath = [Environment]::GetFolderPath("UserProfile")
    $roots = @(
        (Join-Path $userProfilePath "Microsoft\Power BI Desktop Store App\AnalysisServicesWorkspaces"),
        (Join-Path $env:LOCALAPPDATA "Microsoft\Power BI Desktop\AnalysisServicesWorkspaces")
    )

    $portFile = $roots |
        Where-Object { Test-Path -LiteralPath $_ } |
        ForEach-Object { Get-ChildItem -LiteralPath $_ -Filter "msmdsrv.port.txt" -Recurse -File -ErrorAction SilentlyContinue } |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1

    if ($null -eq $portFile) {
        throw "No active Power BI Desktop semantic-model endpoint was found. Open Financial_Report.pbix first."
    }

    $value = (Get-Content -LiteralPath $portFile.FullName -Raw) -replace "`0", ""
    return [int]$value.Trim()
}

if ($Port -le 0) {
    $Port = Find-PowerBIPort
}

$powerBIPath = (Get-AppxPackage Microsoft.MicrosoftPowerBIDesktop).InstallLocation
if (-not $powerBIPath) {
    throw "The Microsoft Store edition of Power BI Desktop was not found."
}

$binPath = Join-Path $powerBIPath "bin"
Add-Type -Path (Join-Path $binPath "Microsoft.AnalysisServices.Server.Core.dll")
Add-Type -Path (Join-Path $binPath "Microsoft.AnalysisServices.Server.Tabular.dll")

$server = [Microsoft.AnalysisServices.Tabular.Server]::new()
$server.Connect("localhost:$Port")

try {
    if ($server.Databases.Count -ne 1) {
        throw "Expected one local semantic model on port $Port; found $($server.Databases.Count)."
    }

    $model = $server.Databases[0].Model
    $measureTable = $model.Tables | Where-Object Name -eq "Tablas de Medidas"
    if ($null -eq $measureTable) {
        throw "Measure table 'Tablas de Medidas' was not found."
    }

    function Set-Measure {
        param(
            [string]$Name,
            [string]$Expression,
            [string]$FormatString,
            [string]$DisplayFolder,
            [string]$Description,
            [bool]$Hidden = $false
        )

        $measure = $measureTable.Measures | Where-Object Name -eq $Name
        if ($null -eq $measure) {
            $measure = [Microsoft.AnalysisServices.Tabular.Measure]::new()
            $measure.Name = $Name
            $measureTable.Measures.Add($measure)
        }
        $measure.Expression = $Expression
        $measure.FormatString = $FormatString
        $measure.DisplayFolder = $DisplayFolder
        $measure.Description = $Description
        $measure.IsHidden = $Hidden
    }

    $currency = '$ #,0.00;-$ #,0.00;$ #,0.00'
    $percent = '0.00%;-0.00%;0.00%'
    $count = '#,0'

    Set-Measure "Cantidad vendida" 'SUM(FactInternetSales[OrderQuantity])' $count "01 Base" "Units sold in the active filter context."
    Set-Measure "Clientes únicos" 'DISTINCTCOUNT(FactInternetSales[CustomerKey])' $count "01 Base" "Distinct purchasing customers; fact-based so product and geography filters remain effective."
    Set-Measure "Operaciones" 'COUNTROWS(FactInternetSales)' $count "01 Base" "Internet-sales line count in the active filter context."
    Set-Measure "Ingresos" 'SUM(FactInternetSales[SalesAmount])' $currency "01 Base" "Revenue before product cost, freight, and tax; additive in every report context."
    Set-Measure "COGS" 'SUM(FactInternetSales[TotalProductCost])' $currency "01 Base" "Cost of goods sold from TotalProductCost; additive in every report context."
    Set-Measure "Costo Total Envios" 'SUM(FactInternetSales[Freight])' $currency "01 Base" "Freight amount associated with internet sales; additive in every report context."
    Set-Measure "Impuestos" 'SUM(FactInternetSales[TaxAmt])' $currency "01 Base" "Tax amount associated with internet sales; additive in every report context."
    Set-Measure "Costo Total + Envíos" '[COGS] + [Costo Total Envios]' $currency "02 Reconciliación" "Product cost plus freight; excludes tax by definition."
    Set-Measure "Costos totales" '[COGS] + [Costo Total Envios] + [Impuestos]' $currency "02 Reconciliación" "Product cost plus freight plus tax; reconciles directly to net profit."
    Set-Measure "Utilidad bruta" '[Ingresos] - [COGS]' $currency "02 Reconciliación" "Gross profit: Revenue minus COGS."
    Set-Measure "Utilidad neta" '[Ingresos] - [Costos totales]' $currency "02 Reconciliación" "Portfolio net profit: Revenue minus COGS, freight, and tax."
    Set-Measure "% Margen Bruto" 'DIVIDE([Utilidad bruta], [Ingresos])' $percent "02 Reconciliación" "Gross profit divided by revenue in the active filter context."
    Set-Measure "% Margen Neto" 'DIVIDE([Utilidad neta], [Ingresos])' $percent "02 Reconciliación" "Net profit divided by revenue in the active filter context."
    Set-Measure "Ratio Costo Operacional %" 'DIVIDE([Costo Total + Envíos], [Ingresos])' $percent "02 Reconciliación" "COGS plus freight divided by revenue; tax is excluded."
    Set-Measure "COGS %" 'DIVIDE([COGS], [Ingresos])' $percent "02 Reconciliación" "COGS divided by revenue in the active filter context."

    Set-Measure "Ingresos YTD" 'CALCULATE([Ingresos], DATESYTD(DimDate[Date]))' $currency "03 Inteligencia de tiempo" "Revenue accumulated from the start of the selected calendar year, using OrderDateKey."
    Set-Measure "Ingresos Acumulados" '[Ingresos YTD]' $currency "03 Inteligencia de tiempo" "Backward-compatible alias for Ingresos YTD."
    Set-Measure "Ingresos PA" 'CALCULATE([Ingresos], SAMEPERIODLASTYEAR(DimDate[Date]))' $currency "03 Inteligencia de tiempo" "Revenue for the same selected period last year (LY)."
    Set-Measure "COGS PA" 'CALCULATE([COGS], SAMEPERIODLASTYEAR(DimDate[Date]))' $currency "03 Inteligencia de tiempo" "COGS for the same selected period last year (LY)."
    Set-Measure "% Margen Bruto PA" 'CALCULATE([% Margen Bruto], SAMEPERIODLASTYEAR(DimDate[Date]))' $percent "03 Inteligencia de tiempo" "Gross margin for the same selected period last year (LY)."
    Set-Measure "Coste LY" 'CALCULATE([Costo Total + Envíos], SAMEPERIODLASTYEAR(DimDate[Date]))' $currency "03 Inteligencia de tiempo" "COGS plus freight for the same selected period last year."
    Set-Measure "Ingresos YTD LY" 'CALCULATE([Ingresos YTD], SAMEPERIODLASTYEAR(DimDate[Date]))' $currency "03 Inteligencia de tiempo" "Year-to-date revenue evaluated one year earlier."
    Set-Measure "Ratio Costo Operacional % LY" 'CALCULATE([Ratio Costo Operacional %], SAMEPERIODLASTYEAR(DimDate[Date]))' $percent "03 Inteligencia de tiempo" "Operational cost ratio for the same selected period last year."
    Set-Measure "Margen Bruto % LY" 'CALCULATE([% Margen Bruto], SAMEPERIODLASTYEAR(DimDate[Date]))' $percent "03 Inteligencia de tiempo" "Gross margin for the same selected period last year."
    Set-Measure "Margen Neto % LY" 'CALCULATE([% Margen Neto], SAMEPERIODLASTYEAR(DimDate[Date]))' $percent "03 Inteligencia de tiempo" "Net margin for the same selected period last year."
    Set-Measure "COGS % LY" 'CALCULATE([COGS %], SAMEPERIODLASTYEAR(DimDate[Date]))' $percent "03 Inteligencia de tiempo" "COGS ratio for the same selected period last year."
    Set-Measure "Ingresos vs LY" '[Ingresos] - [Ingresos PA]' $currency "04 Variaciones" "Absolute revenue variance against the same selected period last year."
    Set-Measure "Ingresos vs LY %" 'DIVIDE([Ingresos vs LY], [Ingresos PA])' $percent "04 Variaciones" "Relative revenue variance against the same selected period last year."
    Set-Measure "Margen bruto vs LY pp" '[% Margen Bruto] - [Margen Bruto % LY]' $percent "04 Variaciones" "Gross-margin change versus LY, expressed in percentage points."
    Set-Measure "Margen neto vs LY pp" '[% Margen Neto] - [Margen Neto % LY]' $percent "04 Variaciones" "Net-margin change versus LY, expressed in percentage points."

    Set-Measure "Reconciliación utilidad bruta" '[Utilidad bruta] - ([Ingresos] - [COGS])' $currency "99 Diagnóstico" "Expected to equal zero at every supported granularity." $true
    Set-Measure "Reconciliación utilidad neta" '[Utilidad neta] - ([Ingresos] - [COGS] - [Costo Total Envios] - [Impuestos])' $currency "99 Diagnóstico" "Expected to equal zero at every supported granularity." $true
    Set-Measure "Reconciliación margen bruto" '[% Margen Bruto] - DIVIDE([Utilidad bruta], [Ingresos])' $percent "99 Diagnóstico" "Expected to equal zero at every supported granularity." $true
    Set-Measure "Reconciliación margen neto" '[% Margen Neto] - DIVIDE([Utilidad neta], [Ingresos])' $percent "99 Diagnóstico" "Expected to equal zero at every supported granularity." $true
    Set-Measure "KPI_Grafico" '0' $currency "99 Diagnóstico" "Compatibility placeholder retained for the original report layout." $true

    # Windows PowerShell 5.1 reads UTF-8 scripts correctly only when a BOM is
    # present. Remove any mojibake duplicates left by a wrongly encoded run.
    $corruptedMeasures = @($measureTable.Measures | Where-Object { $_.Name.Contains("Ã") })
    foreach ($corruptedMeasure in $corruptedMeasures) {
        [void]$measureTable.Measures.Remove($corruptedMeasure)
    }

    $dateRelationship = $model.Relationships | Where-Object Name -eq "0c3fceec-47aa-42b4-bac3-7c71da7dbdd2"
    if ($null -eq $dateRelationship) {
        throw "The audited FactInternetSales-to-DimDate relationship was not found."
    }
    $dateRelationship.FromColumn = ($model.Tables | Where-Object Name -eq "FactInternetSales").Columns | Where-Object Name -eq "OrderDateKey"

    $customerRelationship = $model.Relationships | Where-Object Name -eq "9592c573-2056-de10-107a-bee53a6e77c1"
    if ($null -ne $customerRelationship) {
        $customerRelationship.CrossFilteringBehavior = [Microsoft.AnalysisServices.Tabular.CrossFilteringBehavior]::OneDirection
    }

    # Relationship metadata changes require a calculation pass, but not a
    # source refresh; the embedded import snapshot remains untouched.
    $model.RequestRefresh([Microsoft.AnalysisServices.Tabular.RefreshType]::Calculate)
    $model.SaveChanges()
    Write-Output "FIN-I1 live semantic-model update PASSED on localhost:$Port"
    Write-Output "  - time relationship: FactInternetSales[OrderDateKey] -> DimDate[DateKey]"
    Write-Output "  - reconciled base, LY, variance, and diagnostic measures applied"
    Write-Output "  - customer relationship normalized to one-direction star-schema filtering"
}
finally {
    $server.Disconnect()
}

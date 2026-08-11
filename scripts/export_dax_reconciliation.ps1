param(
    [int]$Port = 0,
    [string]$OutputPath = ""
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
        throw "No active Power BI Desktop endpoint was found. Open Financial_Report.pbix first."
    }
    $value = (Get-Content -LiteralPath $portFile.FullName -Raw) -replace "`0", ""
    return [int]$value.Trim()
}

if ($Port -le 0) { $Port = Find-PowerBIPort }
if ([string]::IsNullOrWhiteSpace($OutputPath)) {
    $OutputPath = Join-Path (Split-Path $PSScriptRoot -Parent) "DOCS\dax_reconciliation.csv"
}

$powerBIPath = (Get-AppxPackage Microsoft.MicrosoftPowerBIDesktop).InstallLocation
if (-not $powerBIPath) { throw "Power BI Desktop was not found." }
Add-Type -Path (Join-Path $powerBIPath "bin\Microsoft.PowerBI.AdomdClient.dll")

$query = @'
DEFINE
VAR TotalRows =
    ROW(
        "Granularity", "Total", "Member", "All",
        "Revenue", [Ingresos], "COGS", [COGS], "Shipping", [Costo Total Envios], "Tax", [Impuestos],
        "GrossProfit", [Utilidad bruta], "NetProfit", [Utilidad neta],
        "GrossMargin", [% Margen Bruto], "NetMargin", [% Margen Neto], "RevenueLY", [Ingresos PA],
        "RevenueDeltaLY", [Ingresos vs LY], "RevenueDeltaLYPct", [Ingresos vs LY %],
        "GrossMarginDeltaLY", [Margen bruto vs LY pp], "NetMarginDeltaLY", [Margen neto vs LY pp],
        "GrossResidual", [Reconciliación utilidad bruta], "NetResidual", [Reconciliación utilidad neta],
        "GrossMarginResidual", [Reconciliación margen bruto], "NetMarginResidual", [Reconciliación margen neto]
    )
VAR YearRows =
    SELECTCOLUMNS(
        SUMMARIZECOLUMNS('DimDate'[CalendarYear],
            "Revenue", [Ingresos], "COGS", [COGS], "Shipping", [Costo Total Envios], "Tax", [Impuestos],
            "GrossProfit", [Utilidad bruta], "NetProfit", [Utilidad neta],
            "GrossMargin", [% Margen Bruto], "NetMargin", [% Margen Neto], "RevenueLY", [Ingresos PA],
            "RevenueDeltaLY", [Ingresos vs LY], "RevenueDeltaLYPct", [Ingresos vs LY %],
            "GrossMarginDeltaLY", [Margen bruto vs LY pp], "NetMarginDeltaLY", [Margen neto vs LY pp],
            "GrossResidual", [Reconciliación utilidad bruta], "NetResidual", [Reconciliación utilidad neta],
            "GrossMarginResidual", [Reconciliación margen bruto], "NetMarginResidual", [Reconciliación margen neto]),
        "Granularity", "Year", "Member", FORMAT('DimDate'[CalendarYear], "0"),
        "Revenue", [Revenue], "COGS", [COGS], "Shipping", [Shipping], "Tax", [Tax],
        "GrossProfit", [GrossProfit], "NetProfit", [NetProfit], "GrossMargin", [GrossMargin], "NetMargin", [NetMargin], "RevenueLY", [RevenueLY],
        "RevenueDeltaLY", [RevenueDeltaLY], "RevenueDeltaLYPct", [RevenueDeltaLYPct],
        "GrossMarginDeltaLY", [GrossMarginDeltaLY], "NetMarginDeltaLY", [NetMarginDeltaLY],
        "GrossResidual", [GrossResidual], "NetResidual", [NetResidual], "GrossMarginResidual", [GrossMarginResidual], "NetMarginResidual", [NetMarginResidual]
    )
VAR CountryRows =
    SELECTCOLUMNS(
        SUMMARIZECOLUMNS('DimCustomer'[CountryRegionCode],
            "Revenue", [Ingresos], "COGS", [COGS], "Shipping", [Costo Total Envios], "Tax", [Impuestos],
            "GrossProfit", [Utilidad bruta], "NetProfit", [Utilidad neta],
            "GrossMargin", [% Margen Bruto], "NetMargin", [% Margen Neto], "RevenueLY", [Ingresos PA],
            "RevenueDeltaLY", [Ingresos vs LY], "RevenueDeltaLYPct", [Ingresos vs LY %],
            "GrossMarginDeltaLY", [Margen bruto vs LY pp], "NetMarginDeltaLY", [Margen neto vs LY pp],
            "GrossResidual", [Reconciliación utilidad bruta], "NetResidual", [Reconciliación utilidad neta],
            "GrossMarginResidual", [Reconciliación margen bruto], "NetMarginResidual", [Reconciliación margen neto]),
        "Granularity", "Country", "Member", 'DimCustomer'[CountryRegionCode],
        "Revenue", [Revenue], "COGS", [COGS], "Shipping", [Shipping], "Tax", [Tax],
        "GrossProfit", [GrossProfit], "NetProfit", [NetProfit], "GrossMargin", [GrossMargin], "NetMargin", [NetMargin], "RevenueLY", [RevenueLY],
        "RevenueDeltaLY", [RevenueDeltaLY], "RevenueDeltaLYPct", [RevenueDeltaLYPct],
        "GrossMarginDeltaLY", [GrossMarginDeltaLY], "NetMarginDeltaLY", [NetMarginDeltaLY],
        "GrossResidual", [GrossResidual], "NetResidual", [NetResidual], "GrossMarginResidual", [GrossMarginResidual], "NetMarginResidual", [NetMarginResidual]
    )
VAR StateRows =
    SELECTCOLUMNS(
        SUMMARIZECOLUMNS('DimCustomer'[CountryRegionCode], 'DimCustomer'[StateProvinceName],
            "Revenue", [Ingresos], "COGS", [COGS], "Shipping", [Costo Total Envios], "Tax", [Impuestos],
            "GrossProfit", [Utilidad bruta], "NetProfit", [Utilidad neta],
            "GrossMargin", [% Margen Bruto], "NetMargin", [% Margen Neto], "RevenueLY", [Ingresos PA],
            "RevenueDeltaLY", [Ingresos vs LY], "RevenueDeltaLYPct", [Ingresos vs LY %],
            "GrossMarginDeltaLY", [Margen bruto vs LY pp], "NetMarginDeltaLY", [Margen neto vs LY pp],
            "GrossResidual", [Reconciliación utilidad bruta], "NetResidual", [Reconciliación utilidad neta],
            "GrossMarginResidual", [Reconciliación margen bruto], "NetMarginResidual", [Reconciliación margen neto]),
        "Granularity", "State", "Member", 'DimCustomer'[CountryRegionCode] & " / " & 'DimCustomer'[StateProvinceName],
        "Revenue", [Revenue], "COGS", [COGS], "Shipping", [Shipping], "Tax", [Tax],
        "GrossProfit", [GrossProfit], "NetProfit", [NetProfit], "GrossMargin", [GrossMargin], "NetMargin", [NetMargin], "RevenueLY", [RevenueLY],
        "RevenueDeltaLY", [RevenueDeltaLY], "RevenueDeltaLYPct", [RevenueDeltaLYPct],
        "GrossMarginDeltaLY", [GrossMarginDeltaLY], "NetMarginDeltaLY", [NetMarginDeltaLY],
        "GrossResidual", [GrossResidual], "NetResidual", [NetResidual], "GrossMarginResidual", [GrossMarginResidual], "NetMarginResidual", [NetMarginResidual]
    )
VAR CategoryRows =
    SELECTCOLUMNS(
        SUMMARIZECOLUMNS('DimProduct'[Category Name],
            "Revenue", [Ingresos], "COGS", [COGS], "Shipping", [Costo Total Envios], "Tax", [Impuestos],
            "GrossProfit", [Utilidad bruta], "NetProfit", [Utilidad neta],
            "GrossMargin", [% Margen Bruto], "NetMargin", [% Margen Neto], "RevenueLY", [Ingresos PA],
            "RevenueDeltaLY", [Ingresos vs LY], "RevenueDeltaLYPct", [Ingresos vs LY %],
            "GrossMarginDeltaLY", [Margen bruto vs LY pp], "NetMarginDeltaLY", [Margen neto vs LY pp],
            "GrossResidual", [Reconciliación utilidad bruta], "NetResidual", [Reconciliación utilidad neta],
            "GrossMarginResidual", [Reconciliación margen bruto], "NetMarginResidual", [Reconciliación margen neto]),
        "Granularity", "Category", "Member", 'DimProduct'[Category Name],
        "Revenue", [Revenue], "COGS", [COGS], "Shipping", [Shipping], "Tax", [Tax],
        "GrossProfit", [GrossProfit], "NetProfit", [NetProfit], "GrossMargin", [GrossMargin], "NetMargin", [NetMargin], "RevenueLY", [RevenueLY],
        "RevenueDeltaLY", [RevenueDeltaLY], "RevenueDeltaLYPct", [RevenueDeltaLYPct],
        "GrossMarginDeltaLY", [GrossMarginDeltaLY], "NetMarginDeltaLY", [NetMarginDeltaLY],
        "GrossResidual", [GrossResidual], "NetResidual", [NetResidual], "GrossMarginResidual", [GrossMarginResidual], "NetMarginResidual", [NetMarginResidual]
    )
EVALUATE UNION(TotalRows, YearRows, CountryRows, StateRows, CategoryRows)
ORDER BY [Granularity], [Member]
'@

$connection = [Microsoft.AnalysisServices.AdomdClient.AdomdConnection]::new("Data Source=localhost:$Port")
$connection.Open()
try {
    $command = $connection.CreateCommand()
    $command.CommandText = $query
    $adapter = [Microsoft.AnalysisServices.AdomdClient.AdomdDataAdapter]::new($command)
    $table = [System.Data.DataTable]::new()
    [void]$adapter.Fill($table)
}
finally {
    $connection.Close()
}

$invariant = [System.Globalization.CultureInfo]::InvariantCulture
$headers = @($table.Columns | ForEach-Object { $_.ColumnName.Trim('[', ']') })
$outputDirectory = Split-Path $OutputPath -Parent
if (-not (Test-Path -LiteralPath $outputDirectory)) {
    [void](New-Item -ItemType Directory -Path $outputDirectory)
}

function Convert-CsvField([object]$Value) {
    if ($null -eq $Value -or $Value -eq [DBNull]::Value) { return '""' }
    if ($Value -is [double] -or $Value -is [decimal] -or $Value -is [single]) {
        $text = [System.Convert]::ToDouble($Value).ToString('G17', $invariant)
    }
    else {
        $text = [string]$Value
    }
    return '"' + $text.Replace('"', '""') + '"'
}

$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
$writer = [System.IO.StreamWriter]::new($OutputPath, $false, $utf8NoBom)
try {
    $writer.WriteLine(($headers | ForEach-Object { Convert-CsvField $_ }) -join ',')
    foreach ($row in $table.Rows) {
        $writer.WriteLine((0..($table.Columns.Count - 1) | ForEach-Object { Convert-CsvField $row[$_] }) -join ',')
    }
}
finally {
    $writer.Dispose()
}

Write-Output "DAX reconciliation export PASSED"
Write-Output "  - endpoint: localhost:$Port"
Write-Output "  - rows: $($table.Rows.Count)"
Write-Output "  - output: $OutputPath"

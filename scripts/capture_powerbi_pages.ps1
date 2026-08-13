param(
    [string]$WindowTitle = "Financial_Report",
    [string]$OutputDirectory = "Images"
)

$ErrorActionPreference = "Stop"

Add-Type -AssemblyName System.Drawing
Add-Type @'
using System;
using System.Runtime.InteropServices;

public static class FinancialCaptureWin32 {
    [StructLayout(LayoutKind.Sequential)]
    public struct RECT {
        public int Left;
        public int Top;
        public int Right;
        public int Bottom;
    }

    [DllImport("user32.dll")]
    public static extern bool GetWindowRect(IntPtr hWnd, out RECT rect);

    [DllImport("user32.dll")]
    public static extern bool PrintWindow(IntPtr hWnd, IntPtr hdcBlt, uint flags);

    [DllImport("user32.dll")]
    public static extern bool ShowWindowAsync(IntPtr hWnd, int command);

    [DllImport("user32.dll")]
    public static extern bool SetForegroundWindow(IntPtr hWnd);

    [DllImport("user32.dll")]
    public static extern void SwitchToThisWindow(IntPtr hWnd, bool altTab);

    [DllImport("user32.dll")]
    public static extern bool SetCursorPos(int x, int y);

    [DllImport("user32.dll", SetLastError = true)]
    public static extern bool PostMessage(IntPtr hWnd, uint message, UIntPtr wParam, IntPtr lParam);

    [DllImport("user32.dll")]
    public static extern void mouse_event(uint flags, uint dx, uint dy, uint data, UIntPtr extraInfo);

    [DllImport("user32.dll")]
    public static extern uint GetDpiForWindow(IntPtr hWnd);
}
'@

$ReferenceWindowWidth = 2578.0
$ReferenceWindowHeight = 1458.0
$ReferenceCropX = 60.0
$ReferenceCropY = 225.0
$ReferenceCropWidth = 2016.0
$ReferenceCropHeight = 1134.0

function Get-PowerBIProcess {
    $matches = @(Get-Process -Name "PBIDesktop" -ErrorAction SilentlyContinue | Where-Object {
        $_.MainWindowHandle -ne 0 -and $_.MainWindowTitle -like "*$WindowTitle*"
    })
    if ($matches.Count -ne 1) {
        throw "Expected one Power BI window matching '$WindowTitle'; found $($matches.Count)."
    }
    return $matches[0]
}

function Save-ReportCanvas {
    param(
        [IntPtr]$WindowHandle,
        [string]$Path
    )

    $rect = New-Object FinancialCaptureWin32+RECT
    if (-not [FinancialCaptureWin32]::GetWindowRect($WindowHandle, [ref]$rect)) {
        throw "GetWindowRect failed."
    }
    $logicalWidth = $rect.Right - $rect.Left
    $logicalHeight = $rect.Bottom - $rect.Top
    $dpi = [FinancialCaptureWin32]::GetDpiForWindow($WindowHandle)
    if ($dpi -le 0) { $dpi = 96 }
    $windowWidth = [int][Math]::Round($logicalWidth * $dpi / 96.0)
    $windowHeight = [int][Math]::Round($logicalHeight * $dpi / 96.0)

    $windowBitmap = New-Object System.Drawing.Bitmap($windowWidth, $windowHeight)
    $windowBitmap.SetResolution($dpi, $dpi)
    $graphics = [System.Drawing.Graphics]::FromImage($windowBitmap)
    $deviceContext = $graphics.GetHdc()
    try {
        if (-not [FinancialCaptureWin32]::PrintWindow($WindowHandle, $deviceContext, 2)) {
            throw "PrintWindow failed."
        }
    }
    finally {
        $graphics.ReleaseHdc($deviceContext)
        $graphics.Dispose()
    }

    $crop = New-Object System.Drawing.Rectangle(
        [int][Math]::Round($ReferenceCropX * $windowWidth / $ReferenceWindowWidth),
        [int][Math]::Round($ReferenceCropY * $windowHeight / $ReferenceWindowHeight),
        [int][Math]::Round($ReferenceCropWidth * $windowWidth / $ReferenceWindowWidth),
        [int][Math]::Round($ReferenceCropHeight * $windowHeight / $ReferenceWindowHeight)
    )
    if ($crop.Right -gt $windowBitmap.Width -or $crop.Bottom -gt $windowBitmap.Height) {
        $windowBitmap.Dispose()
        throw "Calculated report crop exceeds the captured window."
    }

    $canvasBitmap = New-Object System.Drawing.Bitmap(1920, 1080)
    $canvasGraphics = [System.Drawing.Graphics]::FromImage($canvasBitmap)
    try {
        $canvasGraphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
        $canvasGraphics.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
        $canvasGraphics.DrawImage(
            $windowBitmap,
            (New-Object System.Drawing.Rectangle(0, 0, 1920, 1080)),
            $crop,
            [System.Drawing.GraphicsUnit]::Pixel
        )
        $canvasBitmap.Save($Path, [System.Drawing.Imaging.ImageFormat]::Png)
    }
    finally {
        $canvasGraphics.Dispose()
        $canvasBitmap.Dispose()
        $windowBitmap.Dispose()
    }
}

function Send-Key {
    param(
        [IntPtr]$WindowHandle,
        [int]$VirtualKey
    )
    $wParam = [UIntPtr]::new([UInt64]$VirtualKey)
    if (-not [FinancialCaptureWin32]::PostMessage($WindowHandle, 0x0100, $wParam, [IntPtr]::Zero)) {
        throw "PostMessage key-down failed for virtual key $VirtualKey."
    }
    if (-not [FinancialCaptureWin32]::PostMessage($WindowHandle, 0x0101, $wParam, [IntPtr]::Zero)) {
        throw "PostMessage key-up failed for virtual key $VirtualKey."
    }
}

function Invoke-TabClick {
    param(
        [IntPtr]$WindowHandle,
        [double]$RelativeX
    )
    $navigationRect = New-Object FinancialCaptureWin32+RECT
    if (-not [FinancialCaptureWin32]::GetWindowRect($WindowHandle, [ref]$navigationRect)) {
        throw "GetWindowRect failed before tab navigation."
    }
    [FinancialCaptureWin32]::ShowWindowAsync($WindowHandle, 3) | Out-Null
    [FinancialCaptureWin32]::SwitchToThisWindow($WindowHandle, $true)
    [FinancialCaptureWin32]::SetForegroundWindow($WindowHandle) | Out-Null
    Start-Sleep -Milliseconds 250
    $windowWidth = $navigationRect.Right - $navigationRect.Left
    $windowHeight = $navigationRect.Bottom - $navigationRect.Top
    # SetCursorPos is virtualized to this PowerShell process' DPI awareness.
    # GetWindowRect already supplies coordinates in the same logical space.
    $screenX = [int][Math]::Round($navigationRect.Left + $RelativeX * $windowWidth)
    $screenY = [int][Math]::Round($navigationRect.Top + 0.960 * $windowHeight)
    if (-not [FinancialCaptureWin32]::SetCursorPos($screenX, $screenY)) {
        throw "SetCursorPos failed before tab navigation."
    }
    [FinancialCaptureWin32]::mouse_event(0x0002, 0, 0, 0, [UIntPtr]::Zero)
    [FinancialCaptureWin32]::mouse_event(0x0004, 0, 0, 0, [UIntPtr]::Zero)
    Start-Sleep -Milliseconds 1500
}

$process = Get-PowerBIProcess
$handle = $process.MainWindowHandle
[FinancialCaptureWin32]::ShowWindowAsync($handle, 3) | Out-Null
[FinancialCaptureWin32]::SetForegroundWindow($handle) | Out-Null
Start-Sleep -Milliseconds 1400

$resolvedOutput = [System.IO.Path]::GetFullPath((Join-Path (Get-Location) $OutputDirectory))
New-Item -ItemType Directory -Path $resolvedOutput -Force | Out-Null

$rect = New-Object FinancialCaptureWin32+RECT
[FinancialCaptureWin32]::GetWindowRect($handle, [ref]$rect) | Out-Null

function Capture-CurrentPage {
    param([string]$Name, [string]$Label)
    [FinancialCaptureWin32]::SetForegroundWindow($handle) | Out-Null
    for ($index = 0; $index -lt 3; $index++) {
        Send-Key -WindowHandle $handle -VirtualKey 0x1B
        Start-Sleep -Milliseconds 120
    }
    [FinancialCaptureWin32]::SetCursorPos(
        [int][Math]::Round($rect.Left + 8),
        [int][Math]::Round($rect.Top + 8)
    ) | Out-Null
    Start-Sleep -Milliseconds 1600
    $target = Join-Path $resolvedOutput $Name
    Save-ReportCanvas -WindowHandle $handle -Path $target
    Write-Output "Captured ${Label}: $target"
}

$pages = @(
    @{ Name = "executive_overview.png"; Label = "Executive Overview"; TabX = 0.118 },
    @{ Name = "overview.png"; Label = "Drivers de margen y LY"; TabX = 0.194 },
    @{ Name = "usa_detailed.png"; Label = "Geographic Drill-down"; TabX = 0.268 },
    @{ Name = "glossary.png"; Label = "Definiciones y fuentes"; TabX = 0.347 }
)

for ($index = 0; $index -lt $pages.Count; $index++) {
    $page = $pages[$index]
    # The first click may only activate Power BI when another process owned focus.
    # Repeating the same idempotent tab click makes unattended capture reliable.
    Invoke-TabClick -WindowHandle $handle -RelativeX $page.TabX
    Invoke-TabClick -WindowHandle $handle -RelativeX $page.TabX
    Capture-CurrentPage -Name $page.Name -Label $page.Label
}

Write-Output "Power BI page capture completed."

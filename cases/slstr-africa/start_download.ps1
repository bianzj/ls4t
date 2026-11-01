param(
    [ValidateRange(2017, 2025)][int]$StartYear = 2017,
    [ValidateRange(2017, 2025)][int]$EndYear = 2020,
    [ValidateSet('earthdata', 'cdse')][string]$Provider = 'earthdata'
)
$ErrorActionPreference = 'Stop'
if ($StartYear -gt $EndYear) { throw 'StartYear must not exceed EndYear' }
$pythonExe = 'C:\work\miniconda\python.exe'
$downloadRoot = if ($Provider -eq 'earthdata') {
    "D:\data\sentinel3\africa_rainforest_day_${StartYear}_${EndYear}_earthdata"
} else { 'D:\data\sentinel3\africa_rainforest_day_2017_2025' }
New-Item -ItemType Directory -Path $downloadRoot -Force | Out-Null
if ($Provider -eq 'earthdata') {
    $regionFile = Join-Path $downloadRoot 'africa_tropical_moist_forests.geojson'
    $existingRegion = 'D:\data\sentinel3\africa_rainforest_day_2017_2025\africa_tropical_moist_forests.geojson'
    if (!(Test-Path -LiteralPath $regionFile) -and (Test-Path -LiteralPath $existingRegion)) {
        Copy-Item -LiteralPath $existingRegion -Destination $regionFile
    }
}
$env:PYTHONUTF8 = '1'
# Earthdata: EARTHDATA_TOKEN, LAADS_TOKEN, EARTHDATA_USERNAME/PASSWORD,
# ~/.config/ls4t/earthdata.json, .netrc, or Earthdata Download's saved token.
$downloadProcess = Start-Process -FilePath $pythonExe -ArgumentList @(
    '-u', "$PSScriptRoot\download_daytime.py", '--download', '--root', $downloadRoot,
    '--start-year', $StartYear, '--end-year', $EndYear, '--provider', $Provider
) -WindowStyle Hidden -PassThru `
    -RedirectStandardOutput "$downloadRoot\download.log" `
    -RedirectStandardError "$downloadRoot\download.err.log"
$downloadProcess.Id | Set-Content "$downloadRoot\process.pid"
Write-Output "PID=$($downloadProcess.Id)"
Write-Output "$downloadRoot\status.json"

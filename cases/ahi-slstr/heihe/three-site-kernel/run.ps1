param(
    [string]$Python = 'C:\work\miniconda\python.exe',
    [string]$Config = (Join-Path $PSScriptRoot 'config.json'),
    [string]$Replay = ''
)
$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $Python)) { throw "Python not found: $Python" }
$gdalData = Join-Path (Split-Path $Python) 'Library\share\gdal'
if (Test-Path -LiteralPath $gdalData) { $env:GDAL_DATA = $gdalData }
if ($Replay) {
    & $Python (Join-Path $PSScriptRoot 'run.py') --replay $Replay
} else {
    & $Python (Join-Path $PSScriptRoot 'run.py') --config $Config
}
exit $LASTEXITCODE

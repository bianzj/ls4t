param([string]$Python='C:\work\miniconda\python.exe',[string]$Replay='')
$ErrorActionPreference='Stop'
$gdalData=Join-Path (Split-Path $Python) 'Library\share\gdal'
if (Test-Path -LiteralPath $gdalData) { $env:GDAL_DATA=$gdalData }
if ($Replay) { & $Python (Join-Path $PSScriptRoot 'run.py') --replay $Replay }
else { & $Python (Join-Path $PSScriptRoot 'run.py') --config (Join-Path $PSScriptRoot 'config.json') }
exit $LASTEXITCODE

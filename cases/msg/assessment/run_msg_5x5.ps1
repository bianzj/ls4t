param(
    [string]$StartMonth = '201708',
    [string]$EndMonth = '202512',
    [int[]]$Hours = @(12,10,11,13,14,15,16)
)
$ErrorActionPreference = 'Stop'
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONPATH = 'C:\Users\jiank\Documents\ChatGPT\ls4tmsg\tmp\retrieval_test_20261008\vendor'
$env:MPLBACKEND = 'Agg'
$env:OMP_NUM_THREADS = '4'
$env:OPENBLAS_NUM_THREADS = '4'
$python = 'C:\work\miniconda\python.exe'
$output = 'E:\PRODUCTS\LSCT\MSG_5X5_PHYSICAL_V1'
# Reusing a collection requires identical ancillary and implementation inputs.
$manifest = Join-Path $output 'static_source_manifest.json'
if (Test-Path -LiteralPath $manifest) {
    $previous = Get-Content -LiteralPath $manifest -Raw | ConvertFrom-Json
    foreach ($entry in $previous.files.PSObject.Properties) {
        $actual = (Get-FileHash -LiteralPath $entry.Name -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($actual -ne $entry.Value.sha256) { throw "Source changed; do not mix collection: $($entry.Name)" }
    }
}
& $python (Join-Path $PSScriptRoot 'verify_msg_5x5.py')
if ($LASTEXITCODE -ne 0) { throw '5x5 solver verification failed' }
& $python (Join-Path $PSScriptRoot 'produce_msg_5x5.py') --output $output --start-month $StartMonth --end-month $EndMonth --hours @Hours
if ($LASTEXITCODE -ne 0) { throw 'Production interrupted; inspect status.json before resuming' }

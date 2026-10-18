param(
    [string]$StartMonth = '201708',
    [string]$EndMonth = '202512',
    [int[]]$Hours = @(12, 10, 11, 13, 14, 15, 16),
    [int]$Workers = 8,
    [string]$Output = 'E:\PRODUCTS\LSCT\MSG_LS4T_H025_5X5_DECLARED_V1',
    [string]$Python = 'C:\work\miniconda\python.exe'
)
$ErrorActionPreference = 'Stop'
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONPATH = 'C:\Users\jiank\Documents\ChatGPT\ls4tmsg\tmp\retrieval_test_20261008\vendor'
$env:MPLBACKEND = 'Agg'
$env:OMP_NUM_THREADS = '1'
$env:OPENBLAS_NUM_THREADS = '1'
$env:MKL_NUM_THREADS = '1'
$env:NUMEXPR_NUM_THREADS = '1'
& $Python (Join-Path $PSScriptRoot 'verify_msg_ls4t.py') --output (Join-Path $PSScriptRoot 'verification.json')
if ($LASTEXITCODE -ne 0) { throw 'LS4T numerical verification failed.' }
& $Python (Join-Path $PSScriptRoot 'produce_msg_ls4t.py') --output $Output --start-month $StartMonth --end-month $EndMonth --hours @Hours --workers $Workers
# Nonzero terminal status preserves unresolved input geolocation and source failures.
exit $LASTEXITCODE

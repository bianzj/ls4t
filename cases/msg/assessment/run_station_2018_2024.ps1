param([int]$Workers = 4)
$ErrorActionPreference = 'Stop'
$pythonExecutable = 'C:\work\miniconda\python.exe'
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONPATH = 'C:\Users\jiank\Documents\ChatGPT\ls4tmsg\tmp\retrieval_test_20261008\vendor'
$env:MPLBACKEND = 'Agg'
$env:OMP_NUM_THREADS = '2'
$env:OPENBLAS_NUM_THREADS = '2'

# 只读取站点5×5输入；已完成分区按协议和哈希复用，不恢复区域生产。
& $pythonExecutable (Join-Path $PSScriptRoot 'run_station_full_2018_2024.py') --workers $Workers
if ($LASTEXITCODE -ne 0) { throw 'Station inversion failed; completed checkpoints are retained.' }
foreach ($script in @('analyze_station_full_2018_2024.py','audit_station_original_parameters.py','audit_station_replay_extremes.py',
                     'audit_station_landcover.py','report_station_full_2018_2024.py')) {
    & $pythonExecutable (Join-Path $PSScriptRoot $script)
    if ($LASTEXITCODE -ne 0) { throw "Station analysis failed: $script" }
}
Write-Output (Join-Path $PSScriptRoot '..\results\production_assessment\msg_5x5\station_direct_2018_2024')

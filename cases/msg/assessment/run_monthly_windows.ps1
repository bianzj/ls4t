$ErrorActionPreference = 'Stop'
$runtimePython = 'C:\Users\jiank\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$runtimeGit = 'C:\Users\jiank\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\git\cmd\git.exe'
$engineScript = Join-Path $PSScriptRoot 'msg_monthly_composites.py'
$exportScript = Join-Path $PSScriptRoot 'export_monthly_hour_compatible.py'
$outputRoot = 'E:\PRODUCTS\MONTHLY_COMPOSITES'
$lockPath = Join-Path $outputRoot 'run.lock'
if (Test-Path -LiteralPath $lockPath) {
    $previousPid = [int](Get-Content -LiteralPath $lockPath -Raw)
    if (Get-Process -Id $previousPid -ErrorAction SilentlyContinue) {
        throw "Monthly computation is already running, PID $previousPid"
    }
    Remove-Item -LiteralPath $lockPath
}
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONPATH = 'C:\Users\jiank\Documents\ChatGPT\ls4tmsg\tmp\revision_20261007\vendor'
$env:OMP_NUM_THREADS = '1'
$env:OPENBLAS_NUM_THREADS = '1'
$env:GDAL_NUM_THREADS = '1'
$manifest = [ordered]@{
    StartedUtc = [DateTime]::UtcNow.ToString('o')
    Engine = $engineScript
    EngineSha256 = (Get-FileHash -LiteralPath $engineScript -Algorithm SHA256).Hash
    Python = $runtimePython
    CoreCommit = (& $runtimeGit -C 'C:\work\ls4t' rev-parse HEAD)
    MsgCaseCommit = (& $runtimeGit -C 'C:\work\ls4t-msg' rev-parse HEAD)
    OutputRoot = $outputRoot
    InputManifestSha256 = (Get-FileHash -LiteralPath (Join-Path $outputRoot 'input_manifest.json') -Algorithm SHA256).Hash
    PilotVerification = '2018-01 12 UTC: 40 pixel/group scalar checks passed; 18 nonempty; tolerance 0.00004 K'
}
$process = Start-Process -FilePath $runtimePython -ArgumentList @('-u', $engineScript) `
    -WorkingDirectory 'C:\work\ls4t-msg' -WindowStyle Hidden `
    -RedirectStandardOutput (Join-Path $outputRoot 'run.stdout.log') `
    -RedirectStandardError (Join-Path $outputRoot 'run.stderr.log') -PassThru
$manifest['Pid'] = $process.Id
if (Test-Path -LiteralPath $exportScript) {
    $exportLock = Join-Path $outputRoot 'compatible_export.lock'
    $exportAlreadyRunning = $false
    if (Test-Path -LiteralPath $exportLock) {
        $exportPreviousPid = [int](Get-Content -LiteralPath $exportLock -Raw)
        $exportAlreadyRunning = [bool](Get-Process -Id $exportPreviousPid -ErrorAction SilentlyContinue)
        if (-not $exportAlreadyRunning) { Remove-Item -LiteralPath $exportLock }
    }
    if (-not $exportAlreadyRunning) {
        $exportProcess = Start-Process -FilePath $runtimePython -ArgumentList @('-u', $exportScript, '--follow') `
            -WorkingDirectory 'C:\work\ls4t-msg' -WindowStyle Hidden `
            -RedirectStandardOutput (Join-Path $outputRoot 'compatible_export.stdout.log') `
            -RedirectStandardError (Join-Path $outputRoot 'compatible_export.stderr.log') -PassThru
        $manifest['CompatibleExportPid'] = $exportProcess.Id
        $manifest['CompatibleExportScriptSha256'] = (Get-FileHash -LiteralPath $exportScript -Algorithm SHA256).Hash
    } else {
        $manifest['CompatibleExportPid'] = $exportPreviousPid
    }
}
$manifest | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $outputRoot 'run_manifest.json') -Encoding utf8
Write-Output "Started monthly computation: PID $($process.Id), output $outputRoot"

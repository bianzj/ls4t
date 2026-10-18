param([switch]$IncludeAssessment)
$ErrorActionPreference = 'Stop'
$paperRoot = [IO.Path]::GetFullPath('C:\BaiduSyncdisk\research\ls4t_msg')
$caseRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$resultsRoot = Join-Path $caseRoot 'results'
$archiveRoot = Join-Path $caseRoot 'manuscript_history'
New-Item -ItemType Directory -Path $resultsRoot,$archiveRoot -Force | Out-Null
$recordPath = Join-Path $resultsRoot 'storage_migration_20261009.json'
$records = [Collections.Generic.List[object]]::new()
if (Test-Path -LiteralPath $recordPath) {
    foreach ($record in (Get-Content -LiteralPath $recordPath -Raw | ConvertFrom-Json)) { $records.Add($record) }
}
function Check-Target([string]$src,[string]$dst) {
    $src = [IO.Path]::GetFullPath($src); $dst = [IO.Path]::GetFullPath($dst)
    if (-not $src.StartsWith($paperRoot + '\',[StringComparison]::OrdinalIgnoreCase)) { throw "Invalid source: $src" }
    if (-not $dst.StartsWith($caseRoot + '\',[StringComparison]::OrdinalIgnoreCase)) { throw "Invalid target: $dst" }
    $item = Get-Item -LiteralPath $src -Force
    if ($item.LinkType -in @('SymbolicLink','Junction')) { throw "Do not traverse links: $src" }
}
function Move-Merged([string]$src,[string]$dst) {
    Check-Target $src $dst
    if (-not (Test-Path -LiteralPath $dst)) {
        New-Item -ItemType Directory -Path (Split-Path -Parent $dst) -Force | Out-Null
        Move-Item -LiteralPath $src -Destination $dst
        return
    }
    $item=Get-Item -LiteralPath $src -Force
    if ($item.PSIsContainer) {
        foreach ($child in Get-ChildItem -LiteralPath $src -Force) {
            Move-Merged $child.FullName (Join-Path $dst $child.Name)
        }
        if (@(Get-ChildItem -LiteralPath $src -Force).Count -ne 0) { throw "Source not empty: $src" }
        # Non-recursive removal only after every child has been verified and moved.
        Remove-Item -LiteralPath $src -Force
    } else {
        if ((Get-FileHash -LiteralPath $src).Hash -ne (Get-FileHash -LiteralPath $dst).Hash) { throw "Conflicting target: $dst" }
        Remove-Item -LiteralPath $src -Force
    }
}
function Move-Recorded([string]$src,[string]$dst) {
    if (-not (Test-Path -LiteralPath $src)) { return }
    Check-Target $src $dst
    $item=Get-Item -LiteralPath $src -Force
    $files=if ($item.PSIsContainer) { @(Get-ChildItem -LiteralPath $src -File -Recurse -Force) } else { @($item) }
    $manifest=@(foreach ($file in $files) {
        $relative=if ($item.PSIsContainer) { $file.FullName.Substring($src.Length+1) } else { '' }
        @{relative=$relative; bytes=$file.Length; sha256=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLower()}
    })
    Move-Merged $src $dst
    foreach ($file in $manifest) {
        $target=if ($file.relative) { Join-Path $dst $file.relative } else { $dst }
        if ((Get-Item -LiteralPath $target).Length -ne $file.bytes -or (Get-FileHash -LiteralPath $target).Hash.ToLower() -ne $file.sha256) {
            throw "Verification failed: $target"
        }
    }
    $records.Add(@{source=$src;destination=$dst;files=$manifest;verified_utc=[DateTime]::UtcNow.ToString('o')})
    $records | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $recordPath -Encoding utf8
    Write-Output "MOVED $($files.Count) files: $dst"
}
foreach ($name in @('figure_reproduction','retrieval_test','noda_submission')) {
    Move-Recorded (Join-Path $paperRoot $name) (Join-Path $resultsRoot $name)
}
if ($IncludeAssessment) {
    $statusFile=Join-Path $paperRoot 'production_assessment\msg_5x5\station_direct_2018_2024\progress.json'
    if (Test-Path -LiteralPath $statusFile) {
        $status=Get-Content -LiteralPath $statusFile -Raw | ConvertFrom-Json
        if ($status.status -ne 'completed') { throw 'Wait for the active station computation to complete before moving its output.' }
    }
    Move-Recorded (Join-Path $paperRoot 'production_assessment') (Join-Path $resultsRoot 'production_assessment')
}
# Maintain the current v6 manuscript, current feedback, cover letter and review in research.
$keep=@('LS4T-MSG-v6-revised.docx','LS4T-MSG-v6-修改说明与退回生产端意见.docx',
        'LS4T-MSG-v6-修订落实说明.md','LS4T-MSG_Cover_Letter.docx','LS4T-MSG_审稿意见.docx')
foreach ($file in Get-ChildItem -LiteralPath $paperRoot -File -Force) {
    if ($file.Name -notin $keep) { Move-Recorded $file.FullName (Join-Path $archiveRoot $file.Name) }
}

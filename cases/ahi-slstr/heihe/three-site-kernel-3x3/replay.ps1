param(
    [string]$Python='C:\work\miniconda\python.exe',
    [string]$OutputParent='D:\cases\ls4t\ahi-slstr-three-site-kernel-3x3'
)
$ErrorActionPreference='Stop'
# 使用随代码保存的固定案例数据，无需访问 H: 原始卫星盘。
& $Python (Join-Path $PSScriptRoot 'run.py') `
    --replay (Join-Path $PSScriptRoot 'data\2019-05-12-s3b') `
    --output-parent $OutputParent
exit $LASTEXITCODE

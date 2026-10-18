$ErrorActionPreference = 'Stop'
$root = 'C:\work\ls4t-msg\cases\official\results\production_assessment\manuscript_validation_update'
$qa = Join-Path $root 'qa'
New-Item -ItemType Directory -Path $qa -Force | Out-Null
$source = Join-Path $root 'revised\LS4T-MSG-v6-revised.docx'
$pdf = Join-Path $qa 'LS4T-MSG-v6-revised.pdf'
$word = $null
$doc = $null
try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $doc = $word.Documents.Open($source, $false, $true)
    $doc.Repaginate()
    $doc.ExportAsFixedFormat($pdf, 17)
    Write-Output "PDF exported: $pdf"
} finally {
    if ($null -ne $doc) { $doc.Close(0) }
    if ($null -ne $word) { $word.Quit() }
}
$poppler = 'C:\Users\jiank\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\poppler\Library\bin'
& (Join-Path $poppler 'pdfinfo.exe') $pdf
& (Join-Path $poppler 'pdftoppm.exe') -scale-to 1800 -png $pdf (Join-Path $qa 'page')
if ($LASTEXITCODE -ne 0) { throw 'PDF rendering failed' }

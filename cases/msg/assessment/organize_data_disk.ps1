$ErrorActionPreference = 'Stop'
$driveRoot = 'E:\'
$catalogRoot = 'E:\_CATALOG'
$expectedVolume = '\\?\Volume{67afcfe0-97a5-4fc3-83c6-5943ef55f0a3}\'
$volume = Get-Volume -DriveLetter E
if ($volume.UniqueId -ne $expectedVolume -or $volume.FileSystem -ne 'NTFS') {
    throw 'The mounted E: volume does not match the inspected MSG research disk.'
}
New-Item -ItemType Directory -Path $catalogRoot -Force | Out-Null
$journalPath = Join-Path $catalogRoot 'layout_changes.jsonl'
$reportPath = Join-Path $catalogRoot 'organization_report.json'
$records = [System.Collections.Generic.List[object]]::new()
$registry = [System.Collections.Generic.List[object]]::new()
$started = [DateTime]::UtcNow.ToString('o')

function Assert-DataPath([string]$Path) {
    $absolute = [System.IO.Path]::GetFullPath($Path)
    if (-not $absolute.StartsWith($driveRoot, [StringComparison]::OrdinalIgnoreCase) -or $absolute -eq $driveRoot) {
        throw "Path outside the explicitly authorized E: data disk: $Path"
    }
    if ($absolute -match '^E:\\(\$RECYCLE\.BIN|System Volume Information|\$UGM)(\\|$)') {
        throw "Protected filesystem path: $Path"
    }
    return $absolute
}

function Record-Change($Record) {
    $Record | Add-Member -NotePropertyName Utc -NotePropertyValue ([DateTime]::UtcNow.ToString('o')) -Force
    $records.Add($Record)
    $Record | ConvertTo-Json -Depth 10 -Compress | Add-Content -LiteralPath $journalPath -Encoding utf8
}

function Ensure-Parent([string]$Path) {
    $parent = Split-Path -Parent (Assert-DataPath $Path)
    New-Item -ItemType Directory -Path $parent -Force | Out-Null
}

function Set-SourceHidden([string]$Path, [bool]$Pilot = $false) {
    $absolute = Assert-DataPath $Path
    $item = Get-Item -LiteralPath $absolute -Force
    $before = [int]$item.Attributes
    if ($Pilot) { $before = $before -band (-bnot [int][System.IO.FileAttributes]::Hidden) }
    if (($item.Attributes -band [System.IO.FileAttributes]::Hidden) -eq 0 -or $Pilot) {
        $item.Attributes = $item.Attributes -bor [System.IO.FileAttributes]::Hidden
        Record-Change ([pscustomobject]@{ Action='SetHidden'; Path=$absolute; BeforeAttributes=$before; Pilot=$Pilot })
    }
}

function Add-DirectoryView([string]$Source, [string]$View, [string]$Purpose) {
    $Source = Assert-DataPath $Source
    $View = Assert-DataPath $View
    $sourceItem = Get-Item -LiteralPath $Source -Force
    if (-not $sourceItem.PSIsContainer) { throw "Expected data directory: $Source" }
    Ensure-Parent $View
    if (Test-Path -LiteralPath $View) {
        $existing = Get-Item -LiteralPath $View -Force
        if ($existing.LinkType -ne 'Junction' -or ([System.IO.Path]::GetFullPath([string]$existing.Target)) -ne $Source) {
            throw "Conflicting existing category entry: $View"
        }
        if ($Source -eq 'E:\map') {
            Record-Change ([pscustomobject]@{ Action='CreateJunction'; Path=$View; Source=$Source; Pilot=$true })
        }
    } else {
        New-Item -ItemType Junction -Path $View -Target $Source | Out-Null
        Record-Change ([pscustomobject]@{ Action='CreateJunction'; Path=$View; Source=$Source })
    }
    $registry.Add([pscustomobject]@{ Category=$Purpose; BrowsePath=$View; OriginalPath=$Source; EntryType='Junction' })
    Set-SourceHidden $Source ($Source -eq 'E:\map')
    $linkItem = Get-Item -LiteralPath $View -Force
    if ($linkItem.Attributes -band [System.IO.FileAttributes]::Hidden) { throw "Category entry unexpectedly hidden: $View" }
}

function Add-FileView([string]$Source, [string]$View, [string]$Purpose) {
    $Source = Assert-DataPath $Source
    $View = Assert-DataPath $View
    $sourceItem = Get-Item -LiteralPath $Source -Force
    if ($sourceItem.PSIsContainer) { throw "Expected a file: $Source" }
    Ensure-Parent $View
    if (-not (Test-Path -LiteralPath $View)) {
        New-Item -ItemType HardLink -Path $View -Target $Source | Out-Null
        Record-Change ([pscustomobject]@{ Action='CreateHardLink'; Path=$View; Source=$Source; Bytes=$sourceItem.Length })
    }
    $registry.Add([pscustomobject]@{ Category=$Purpose; BrowsePath=$View; OriginalPath=$Source; EntryType='HardLink' })
}

function Move-LooseFile([string]$Source, [string]$Destination, [string]$Purpose) {
    $Source = Assert-DataPath $Source
    $Destination = Assert-DataPath $Destination
    if ($Source -match '^E:\\PRODUCTS\\(MSG|MSG-IODC|LSCT|MONTHLY_COMPOSITES)(\\|$)') {
        throw "Active scientific product path cannot be relocated: $Source"
    }
    $item = Get-Item -LiteralPath $Source -Force
    if ($item.PSIsContainer) { throw 'This operation moves only explicitly selected loose files.' }
    if (Test-Path -LiteralPath $Destination) { throw "Refusing to overwrite an existing file: $Destination" }
    Ensure-Parent $Destination
    $hash = (Get-FileHash -LiteralPath $Source -Algorithm SHA256).Hash
    $length = $item.Length
    # Both absolute paths are checked within E: before the native file move.
    Move-Item -LiteralPath $Source -Destination $Destination -ErrorAction Stop
    Record-Change ([pscustomobject]@{ Action='MoveFile'; Source=$Source; Path=$Destination; Bytes=$length; Sha256=$hash })
    if ((Get-Item -LiteralPath $Destination).Length -ne $length -or
        (Get-FileHash -LiteralPath $Destination -Algorithm SHA256).Hash -ne $hash) {
        throw "Integrity verification failed after moving: $Destination"
    }
    $registry.Add([pscustomobject]@{ Category=$Purpose; BrowsePath=$Destination; OriginalPath=$Source; EntryType='MovedFile' })
}

$directoryViews = @(
    @('E:\Static','E:\AUXILIARY\GEOMETRY','Geometry and viewing angles'),
    @('E:\map','E:\AUXILIARY\LAND_COVER','Land-cover input'),
    @('E:\lse','E:\AUXILIARY\EMISSIVITY','Emissivity input'),
    @('E:\field','E:\OBSERVATIONS\FIELD','Ground observations'),
    @('E:\results','E:\VALIDATION\HISTORY\results','Historical station extraction set 1'),
    @('E:\results2','E:\VALIDATION\HISTORY\results2','Historical station extraction set 2'),
    @('E:\PRODUCTS\SITE','E:\VALIDATION\SITE_EXTRACTS','Satellite station extractions'),
    @('E:\PRODUCTS\Comparison','E:\FIGURES\COMPARISONS\LEGACY_PAIR','Historical comparison figures'),
    @('E:\PRODUCTS\FUSION_RESULTS','E:\EXPERIMENTS\FUSION_RESULTS','Historical fusion results'),
    @('E:\PRODUCTS\OUTPUT_300m','E:\EXPERIMENTS\OUTPUT_300m','300 m derived comparison'),
    @('E:\TEST','E:\EXPERIMENTS\TEST_RUNS','LS4T test runs'),
    @('E:\temp','E:\EXPERIMENTS\STAGING','Mixed-project staging and historical intermediate data'),
    @('E:\MSG','E:\EXPERIMENTS\HISTORICAL_ROOT\MSG','Historical MSG placeholder; not the production root')
)
foreach ($view in $directoryViews) { Add-DirectoryView $view[0] $view[1] $view[2] }

# The existing analysis bundle stays accessible to scripts at its original path.
# Categorized hard links reference the same NTFS file, not another data version.
$analysisSource='E:\PRODUCTS\VALIDATION'
foreach ($file in (Get-ChildItem -LiteralPath $analysisSource -File -Force)) {
    $name=$file.Name
    $destination=$null
    if ($file.Extension -eq '.csv') {
        $category = if ($name -match '^top|_top\d+') { 'RANKING_TABLES' }
            elseif ($name -match 'hour_separate') { 'MONTHLY_BY_UTC' }
            elseif ($name -match 'matched') { 'MATCHED_PAIRS' }
            elseif ($name -match 'summary|statistics|^monthly_rmse|scale_metrics') { 'SUMMARY_METRICS' }
            elseif ($name -match 'monthly') { 'MONTHLY_SITE_VALUES' }
            elseif ($name -match 'timestep|valid_timestep') { 'TIMESTEP_SITE_VALUES' }
            elseif ($name -match 'site_validation') { 'SITE_METRICS' }
            else { 'OTHER_TABLES' }
        $destination = Join-Path (Join-Path 'E:\VALIDATION\TABLES' $category) $name
    } elseif ($file.Extension -in @('.png','.jpg','.jpeg','.pdf')) {
        $destination = Join-Path 'E:\FIGURES\STATION_VALIDATION' $name
        $category='Station validation figures'
    } elseif ($file.Extension -in @('.txt','.md')) {
        $destination = Join-Path 'E:\DOCUMENTS\VALIDATION_REPORTS' $name
        $category='Historical validation reports'
    }
    if ($destination) { Add-FileView $file.FullName $destination $category }
}
Set-SourceHidden $analysisSource

foreach ($file in (Get-ChildItem -LiteralPath 'E:\PRODUCTS' -File -Force)) {
    if ($file.Name -like 'LSCT_Site_Results*.csv' -or $file.Name -eq 'ALL_SITES_LST_FITTING_RESULTS.csv') {
        Add-FileView $file.FullName (Join-Path 'E:\VALIDATION\STATION_SUMMARIES' $file.Name) 'Station extraction summary'
    } elseif ($file.Name -eq 'LSCT_Validation_Stats_Evora.csv') {
        Add-FileView $file.FullName (Join-Path 'E:\VALIDATION\EVORA' $file.Name) 'Evora validation statistics'
    } elseif ($file.Name -eq 'Validation_Stats_Comparison.csv') {
        Add-FileView $file.FullName (Join-Path 'E:\VALIDATION\COMPARISON_METRICS' $file.Name) 'Historical comparison statistics'
    } elseif ($file.Extension -in @('.png','.jpg','.jpeg')) {
        $category=if ($file.Name -match 'Evora') { 'EVORA' } else { 'COMPARISONS' }
        Move-LooseFile $file.FullName (Join-Path (Join-Path 'E:\FIGURES' $category) $file.Name) $category
    } elseif ($file.Name -like '.~*') {
        Move-LooseFile $file.FullName (Join-Path 'E:\EXPERIMENTS\LEGACY_OFFICE_LOCKS' $file.Name) 'Preserved historical Office lock marker'
    }
}

foreach ($file in (Get-ChildItem -LiteralPath 'E:\' -File -Force)) {
    if ($file.Name -match '^(LC\d\d_L2SP_\d{6}_\d{8}_\d{8}_\d{2}_T\d)_') {
        $scene=$Matches[1]
        Move-LooseFile $file.FullName (Join-Path (Join-Path 'E:\AUXILIARY\LANDSAT' $scene) $file.Name) 'Landsat reference bands'
    } elseif ($file.Name -like 'MLST_MONTH_*.h5') {
        Move-LooseFile $file.FullName (Join-Path 'E:\EXPERIMENTS\HISTORICAL_MONTHLY_SAMPLES' $file.Name) 'Historical root-level monthly samples'
    } elseif ($file.Name -like 'fast_spatial_plot*.png') {
        Move-LooseFile $file.FullName (Join-Path 'E:\FIGURES\MONTHLY_PREVIEWS' $file.Name) 'Historical monthly preview figure'
    } elseif ($file.Name -eq 'RESULTS.ppt') {
        Move-LooseFile $file.FullName (Join-Path 'E:\DOCUMENTS\PRESENTATIONS' $file.Name) 'Historical presentation'
    } elseif ($file.Name -eq '.~RESULTS.ppt') {
        Move-LooseFile $file.FullName (Join-Path 'E:\EXPERIMENTS\LEGACY_OFFICE_LOCKS' $file.Name) 'Preserved historical Office lock marker'
    } elseif ($file.Name -eq 'DATA_PROCESSING_README.md') {
        Move-LooseFile $file.FullName 'E:\DOCUMENTS\DATA_PROCESSING_README_historical.md' 'Historical processing documentation'
    }
}

# Cross-platform metadata is retained; only its Explorer visibility changes.
foreach ($metadata in @('E:\.fseventsd','E:\.TemporaryItems','E:\.Trash-1000','E:\.Trashes')) {
    if (Test-Path -LiteralPath $metadata) { Set-SourceHidden $metadata }
}

$monthlyViews=@(
    @('E:\PRODUCTS\LSCT\MLST_COMPONENT\MONTHLY_HOUR_TOPLEVEL_2018-2025','E:\PRODUCTS\MONTHLY\LSCT_4COMPONENTS','Four-component monthly product; stored K x 100'),
    @('E:\PRODUCTS\MSG\MLST\MONTHLY_HOUR_TOPLEVEL_2018-2025','E:\PRODUCTS\MONTHLY\LST_EURO','EURO bulk LST monthly product; stored K x 100'),
    @('E:\PRODUCTS\MSG-IODC\MLST\MONTHLY_HOUR_TOPLEVEL_2018-2025','E:\PRODUCTS\MONTHLY\LST_IODC','IODC bulk LST monthly product; stored K x 100'),
    @('E:\PRODUCTS\MONTHLY_COMPOSITES','E:\PRODUCTS\MONTHLY\PAIRED_WITH_COUNTS','Current native and paired means, valid counts and flags; stored K')
)
foreach ($view in $monthlyViews) {
    # Unlike legacy roots, the running products remain visible at both locations.
    Ensure-Parent $view[1]
    if (-not (Test-Path -LiteralPath $view[1])) {
        New-Item -ItemType Junction -Path $view[1] -Target $view[0] | Out-Null
        Record-Change ([pscustomobject]@{ Action='CreateJunction'; Path=$view[1]; Source=$view[0] })
    }
    $registry.Add([pscustomobject]@{ Category=$view[2]; BrowsePath=$view[1]; OriginalPath=$view[0]; EntryType='Junction' })
}

$registry | Export-Csv -LiteralPath (Join-Path $catalogRoot 'path_index.csv') -NoTypeInformation -Encoding utf8BOM
$registry | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $catalogRoot 'path_index.json') -Encoding utf8
$report=[ordered]@{
    Status='organized'; StartedUtc=$started; FinishedUtc=[DateTime]::UtcNow.ToString('o')
    VolumeUniqueId=$volume.UniqueId; FileSystem=$volume.FileSystem
    DiskSizeBytes=$volume.Size; AvailableBytes=$volume.SizeRemaining
    DirectoryViewsCreated=@($records | Where-Object Action -eq 'CreateJunction').Count
    FileViewsCreated=@($records | Where-Object Action -eq 'CreateHardLink').Count
    LooseFilesMoved=@($records | Where-Object Action -eq 'MoveFile').Count
    DirectoryPhysicalSourcePathsPreserved=$true; ActiveTemperatureProductPathsPreserved=$true; FileDeletions=0
    ScientificArrayCopies=0; MovedFileSha256Verification='all passed'
    MonthlyStatus=(Get-Content -LiteralPath 'E:\PRODUCTS\MONTHLY_COMPOSITES\status.json' -Raw | ConvertFrom-Json)
    CompatibleExportStatus=(Get-Content -LiteralPath 'E:\PRODUCTS\MONTHLY_COMPOSITES\compatible_export_status.json' -Raw | ConvertFrom-Json)
}
$report | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $reportPath -Encoding utf8
$report | ConvertTo-Json -Depth 3

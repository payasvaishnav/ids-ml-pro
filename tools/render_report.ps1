$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$inputDoc = Join-Path $root 'deliverables/IDS_Project_Report.docx'
$outputPdf = Join-Path $root 'deliverables/IDS_Project_Report.pdf'
$wordApp = $null
$wordDoc = $null
try {
    $wordApp = New-Object -ComObject Word.Application
    $wordApp.Visible = $false
    $wordApp.DisplayAlerts = 0
    $wordDoc = $wordApp.Documents.Open($inputDoc, $false, $true)
    $wordDoc.Repaginate()
    $wordDoc.ExportAsFixedFormat($outputPdf, 17)
    Write-Output "PDF rendered with Microsoft Word: $outputPdf"
} finally {
    if ($null -ne $wordDoc) { $wordDoc.Close(0) }
    if ($null -ne $wordApp) { $wordApp.Quit() }
}

$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (-not (Test-Path '.venv/Scripts/python.exe')) {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Could not create virtual environment.' }
}
& .venv/Scripts/python.exe -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
if (-not (Test-Path 'reference/data/CICIDS2017_sample.csv')) {
    if (Test-Path 'reference') { throw 'Reference folder is incomplete. Check the README troubleshooting section.' }
    git clone --depth 1 https://github.com/Western-OC2-Lab/Intrusion-Detection-System-Using-Machine-Learning.git reference
    if ($LASTEXITCODE -ne 0) { throw 'Dataset download failed.' }
}
& .venv/Scripts/python.exe train.py
if ($LASTEXITCODE -ne 0) { throw 'Training failed.' }
Write-Host 'Ready. Run launch.ps1 to open the dashboard.'

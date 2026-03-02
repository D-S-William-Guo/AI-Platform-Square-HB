# backend/scripts/dev/bootstrap_venv.ps1
$ErrorActionPreference = "Stop"

$backendDir = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $backendDir

Write-Host "[bootstrap] backend dir: $backendDir"

if (-not (Test-Path "requirements.txt")) {
  Write-Error "[bootstrap] requirements.txt not found in $backendDir"
  exit 1
}

if (-not (Test-Path ".venv")) {
  Write-Host "[bootstrap] creating .venv"
  python -m venv .venv
  if ($LASTEXITCODE -ne 0) { throw "failed to create .venv" }
} else {
  Write-Host "[bootstrap] reusing existing .venv"
}

$VenvPython = Join-Path $backendDir ".venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) { throw "venv python not found: $VenvPython" }

Write-Host "[bootstrap] installing requirements"
& $VenvPython -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw "pip install -r requirements.txt failed" }

Write-Host "[bootstrap] installing editable package"
& $VenvPython -m pip install -e .
if ($LASTEXITCODE -ne 0) { throw "pip install -e . failed" }

Write-Host "[bootstrap] done"

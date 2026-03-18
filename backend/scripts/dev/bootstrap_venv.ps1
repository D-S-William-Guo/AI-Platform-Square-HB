# backend/scripts/dev/bootstrap_venv.ps1
$ErrorActionPreference = "Stop"

$rootDir = Resolve-Path (Join-Path $PSScriptRoot "..\..\..")
$backendDir = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$venvDir = Join-Path $rootDir.Path ".venv"
Set-Location $backendDir

Write-Host "[bootstrap] backend dir: $backendDir"
Write-Host "[bootstrap] repo root: $rootDir"

if (-not (Test-Path "requirements.txt")) {
  Write-Error "[bootstrap] requirements.txt not found in $backendDir"
  exit 1
}

if (-not (Test-Path $venvDir)) {
  Write-Host "[bootstrap] creating $venvDir"
  python -m venv $venvDir
  if ($LASTEXITCODE -ne 0) { throw "failed to create .venv" }
} else {
  Write-Host "[bootstrap] reusing existing $venvDir"
}

$VenvPython = Join-Path $venvDir "Scripts\python.exe"
if (-not (Test-Path $VenvPython)) { throw "venv python not found: $VenvPython" }

Write-Host "[bootstrap] installing requirements"
& $VenvPython -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw "pip install -r requirements.txt failed" }

Write-Host "[bootstrap] installing editable package"
& $VenvPython -m pip install -e .
if ($LASTEXITCODE -ne 0) { throw "pip install -e . failed" }

Write-Host "[bootstrap] done"

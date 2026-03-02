# backend/scripts/dev/doctor.ps1
$ErrorActionPreference = "Stop"

function Section($t){ Write-Host "`n==================== $t ====================`n" }

Section "1) Python & pip"
python --version
python -c "import sys; print(sys.executable)"
python -m pip -V

Section "2) Editable import"
python -c "import app; import app.main; print('import app ok')"

Section "3) pip check"
python -m pip check

Section "4) Pytest"
Set-Location "$PSScriptRoot\..\..\"   # -> backend/
pytest -q tests
Write-Host "✅ DONE"

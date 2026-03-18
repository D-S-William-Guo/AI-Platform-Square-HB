# backend/scripts/dev/doctor.ps1
$ErrorActionPreference = "Stop"

if (-not $env:TEST_DATABASE_URL) {
  $env:TEST_DATABASE_URL = "mysql+pymysql://ai_app_user:ai_app_password@127.0.0.1:13306/ai_app_square_test?charset=utf8mb4"
}
if (-not $env:DATABASE_URL) {
  $env:DATABASE_URL = $env:TEST_DATABASE_URL
}

function Section($t){ Write-Host "`n==================== $t ====================`n" }

Section "1) Python & pip"
python --version
python -c "import sys; print(sys.executable)"
python -m pip -V

Section "2) Editable import"
python -c "import app; import app.main; print('import app ok')"

Section "3) pip check"
python -m pip check

Section "4) Alembic + bootstrap"
Set-Location "$PSScriptRoot\..\..\"   # -> backend/
python -m alembic upgrade head
python -m app.bootstrap init-base

Section "5) Pytest"
python -m pytest -q tests
Write-Host "✅ DONE"

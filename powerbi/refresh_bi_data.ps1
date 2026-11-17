# ==============================================================================
# ClearRoute Power BI Analytical Data Refresh Pipeline (PowerShell)
# ==============================================================================
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ExportsScript = Join-Path $ScriptDir "exports\generate_bi_exports.py"
$TestsScript = Join-Path $ScriptDir "tests\test_powerbi_exports.py"

Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host "ClearRoute Power BI Analytical Data Refresh Pipeline" -ForegroundColor Cyan
Write-Host "==================================================================" -ForegroundColor Cyan

Write-Host "Regenerating exports from Gold master dataset..." -ForegroundColor Yellow
python $ExportsScript
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Export regeneration failed." -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "`nRunning validation tests..." -ForegroundColor Yellow
pytest $TestsScript
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Validation tests failed." -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "`n==================================================================" -ForegroundColor Green
Write-Host "[SUCCESS] All Power BI analytical tables refreshed and verified!" -ForegroundColor Green
Write-Host "In Power BI Desktop, click Home -> Refresh to update all visuals." -ForegroundColor Green
Write-Host "==================================================================" -ForegroundColor Green

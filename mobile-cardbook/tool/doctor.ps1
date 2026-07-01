$ErrorActionPreference = "Continue"

Write-Host "Cardbook mobile doctor" -ForegroundColor Cyan
Write-Host ""

function Test-Command($Name) {
    $cmd = Get-Command $Name -ErrorAction SilentlyContinue
    if ($cmd) {
        Write-Host "[OK] $Name" -ForegroundColor Green
        & $Name --version
    }
    else {
        Write-Host "[FALTA] $Name no esta en PATH" -ForegroundColor Red
    }
    Write-Host ""
}

Test-Command "flutter"
Test-Command "dart"

if ($env:ANDROID_HOME) {
    Write-Host "[OK] ANDROID_HOME=$env:ANDROID_HOME" -ForegroundColor Green
}
else {
    Write-Host "[FALTA] ANDROID_HOME no esta configurado" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Cuando Flutter este instalado ejecuta:" -ForegroundColor Cyan
Write-Host "flutter doctor"

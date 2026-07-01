param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path,
    [string]$PublicBaseUrl = "https://cardbook-45cf0409dc07.herokuapp.com",
    [switch]$SkipCollectstatic
)

$ErrorActionPreference = "Stop"

function Step($Message) {
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

Push-Location $ProjectRoot
try {
    Step "Django system check"
    python manage.py check
    if ($LASTEXITCODE -ne 0) {
        throw "python manage.py check fallo"
    }

    if (-not $SkipCollectstatic) {
        Step "Collectstatic"
        python manage.py collectstatic --noinput
        if ($LASTEXITCODE -ne 0) {
            throw "collectstatic fallo"
        }
    }

    Step "Release audit"
    $auditScript = Join-Path $ProjectRoot "mobile-cardbook\tool\release_audit.ps1"
    powershell -ExecutionPolicy Bypass -File $auditScript -ProjectRoot $ProjectRoot -PublicBaseUrl $PublicBaseUrl
    if ($LASTEXITCODE -ne 0) {
        throw "release_audit fallo"
    }

    Step "Predeploy listo"
    Write-Host "Puedes desplegar con:" -ForegroundColor Green
    Write-Host "  git push heroku main"
    Write-Host "  heroku run python manage.py migrate --app cardbook"
    Write-Host "  heroku open --app cardbook"
}
finally {
    Pop-Location
}


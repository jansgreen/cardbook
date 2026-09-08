param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [string]$PublicBaseUrl = "https://incardbook.com",
    [switch]$SkipCollectstatic,
    [switch]$SkipFlutter,
    [switch]$SkipSmoke
)

$ErrorActionPreference = "Stop"

function Step($Message) {
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Invoke-Checked([scriptblock]$Command, [string]$FailureMessage) {
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw $FailureMessage
    }
}

function Get-FlutterCommand {
    $flutter = Get-Command flutter -ErrorAction SilentlyContinue
    if ($flutter) { return $flutter.Source }

    if ($env:FLUTTER_HOME) {
        $fromHome = Join-Path $env:FLUTTER_HOME "bin\flutter.bat"
        if (Test-Path $fromHome) { return $fromHome }
    }

    foreach ($path in @("C:\src\flutter\bin\flutter.bat", "$env:LOCALAPPDATA\flutter\bin\flutter.bat")) {
        if ($path -and (Test-Path $path)) { return $path }
    }

    return ""
}

Push-Location $ProjectRoot
try {
    Step "Django system check"
    Invoke-Checked { .\cb_env\Scripts\python.exe manage.py check } "manage.py check fallo"

    Step "Migration drift check"
    Invoke-Checked { .\cb_env\Scripts\python.exe manage.py makemigrations --dry-run --check } "Hay migraciones pendientes"

    Step "Critical Django tests"
    Invoke-Checked {
        .\cb_env\Scripts\python.exe manage.py test `
            cardbookweb `
            mobile `
            accesscontrol `
            ai_agents `
            financial_analytics `
            forms_builder `
            websitebuilder `
            web.tests_mvp_flow
    } "Tests criticos fallaron"

    Step "Operational snapshot"
    Invoke-Checked { .\cb_env\Scripts\python.exe manage.py ops_snapshot --json } "ops_snapshot fallo"

    if (-not $SkipCollectstatic) {
        Step "Collectstatic"
        Invoke-Checked { .\cb_env\Scripts\python.exe manage.py collectstatic --noinput } "collectstatic fallo"
    }

    if (-not $SkipFlutter) {
        $flutter = Get-FlutterCommand
        if (-not $flutter) {
            throw "Flutter no esta disponible. Instala Flutter o define FLUTTER_HOME."
        }

        Push-Location (Join-Path $ProjectRoot "mobile-cardbook")
        try {
            Step "Flutter dependencies"
            Invoke-Checked { & $flutter pub get } "flutter pub get fallo"

            Step "Flutter analyze"
            Invoke-Checked { & $flutter analyze } "flutter analyze fallo"

            Step "Flutter tests"
            Invoke-Checked { & $flutter test } "flutter test fallo"
        }
        finally {
            Pop-Location
        }
    }

    if (-not $SkipSmoke) {
        $smokeScript = Join-Path $ProjectRoot "mobile-cardbook\tool\smoke_heroku.ps1"
        if (Test-Path $smokeScript) {
            Step "Remote smoke test"
            Invoke-Checked {
                powershell -ExecutionPolicy Bypass -File $smokeScript -PublicBaseUrl $PublicBaseUrl -AllowDeploymentPending
            } "smoke test fallo"
        }
    }

    Step "Production gate listo"
    Write-Host "Validacion completada. Para desplegar desde esta rama:" -ForegroundColor Green
    Write-Host "  git push heroku stable/cardbook-core:main"
    Write-Host "  heroku run --app cardbook --exit-code --no-tty -- python manage.py migrate"
    Write-Host "  heroku open --app cardbook"
}
finally {
    Pop-Location
}

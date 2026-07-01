param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path,
    [string]$PublicBaseUrl = "https://cardbook-45cf0409dc07.herokuapp.com"
)

$ErrorActionPreference = "Continue"
$failures = New-Object System.Collections.Generic.List[string]
$warnings = New-Object System.Collections.Generic.List[string]

function Pass($Message) {
    Write-Host "[OK] $Message" -ForegroundColor Green
}

function Warn($Message) {
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
    $warnings.Add($Message) | Out-Null
}

function Fail($Message) {
    Write-Host "[FAIL] $Message" -ForegroundColor Red
    $failures.Add($Message) | Out-Null
}

function Test-PathRequired($Path, $Label) {
    if (Test-Path $Path) {
        Pass $Label
    }
    else {
        Fail "$Label no existe: $Path"
    }
}

Write-Host "Cardbook release audit" -ForegroundColor Cyan
Write-Host "Project root: $ProjectRoot"
Write-Host ""

$mobileRoot = Join-Path $ProjectRoot "mobile-cardbook"

Test-PathRequired (Join-Path $mobileRoot "pubspec.yaml") "pubspec.yaml"
Test-PathRequired (Join-Path $mobileRoot "release_config.example.json") "release_config.example.json"
Test-PathRequired (Join-Path $mobileRoot "store\google-play\publishing_checklist.md") "Google Play checklist"
Test-PathRequired (Join-Path $mobileRoot "store\google-play\data_safety.md") "Data Safety draft"
Test-PathRequired (Join-Path $mobileRoot "store\google-play\es-419\full_description.txt") "Store listing ES"
Test-PathRequired (Join-Path $mobileRoot "store\google-play\en-US\full_description.txt") "Store listing EN"
Test-PathRequired (Join-Path $ProjectRoot "templates\web\privacy.html") "Privacy page template"
Test-PathRequired (Join-Path $ProjectRoot "templates\web\terms.html") "Terms page template"

Write-Host ""
Write-Host "Django check" -ForegroundColor Cyan
Push-Location $ProjectRoot
try {
    python manage.py check
    if ($LASTEXITCODE -eq 0) {
        Pass "Django system check"
    }
    else {
        Fail "Django system check fallo"
    }
}
catch {
    Fail "No se pudo ejecutar python manage.py check: $($_.Exception.Message)"
}
finally {
    Pop-Location
}

Write-Host ""
Write-Host "Flutter environment" -ForegroundColor Cyan
if (Get-Command flutter -ErrorAction SilentlyContinue) {
    Pass "flutter en PATH"
    Push-Location $mobileRoot
    try {
        flutter --version
        flutter pub get
        flutter analyze
        if ($LASTEXITCODE -ne 0) {
            Fail "flutter analyze fallo"
        }
        else {
            Pass "flutter analyze"
        }
        flutter test
        if ($LASTEXITCODE -ne 0) {
            Fail "flutter test fallo"
        }
        else {
            Pass "flutter test"
        }
    }
    finally {
        Pop-Location
    }
}
else {
    Warn "Flutter no esta en PATH. Instala Flutter antes del build real."
}

if (Get-Command dart -ErrorAction SilentlyContinue) {
    Pass "dart en PATH"
}
else {
    Warn "Dart no esta en PATH."
}

if ($env:ANDROID_HOME) {
    Pass "ANDROID_HOME configurado"
}
else {
    Warn "ANDROID_HOME no esta configurado."
}

Write-Host ""
Write-Host "Public endpoints" -ForegroundColor Cyan
foreach ($path in @("/health/", "/health/ready/", "/privacy/", "/terms/", "/android/version/")) {
    $url = "$($PublicBaseUrl.TrimEnd('/'))$path"
    try {
        $response = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 15
        if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 400) {
            Pass "$url -> $($response.StatusCode)"
        }
        else {
            Warn "$url -> $($response.StatusCode)"
        }
    }
    catch {
        Warn "No se pudo consultar ${url}: $($_.Exception.Message)"
    }
}

Write-Host ""
Write-Host "Summary" -ForegroundColor Cyan
Write-Host "Failures: $($failures.Count)"
Write-Host "Warnings: $($warnings.Count)"

if ($failures.Count -gt 0) {
    exit 1
}

exit 0

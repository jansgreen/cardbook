param(
    [string]$ApiBaseUrl = "https://cardbook-45cf0409dc07.herokuapp.com",
    [switch]$BuildDebug,
    [switch]$BuildRelease,
    [switch]$InstallOnDevice,
    [switch]$SkipRemoteSmoke
)

$ErrorActionPreference = "Continue"
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$MobileRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
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

function Invoke-Step($Label, [scriptblock]$Command) {
    Write-Host ""
    Write-Host $Label -ForegroundColor Cyan
    try {
        & $Command
        if ($LASTEXITCODE -ne 0) {
            Fail "$Label fallo con codigo $LASTEXITCODE"
        }
        else {
            Pass $Label
        }
    }
    catch {
        Fail "$Label fallo: $($_.Exception.Message)"
    }
}

function Test-JsonEndpoint($Path, $Label) {
    $url = "$($ApiBaseUrl.TrimEnd('/'))$Path"
    try {
        $response = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 20
        if ($response.StatusCode -lt 200 -or $response.StatusCode -ge 400) {
            Fail "$Label respondio $($response.StatusCode)"
            return $null
        }
        Pass "$Label -> $($response.StatusCode)"
        return $response.Content | ConvertFrom-Json
    }
    catch {
        Fail "$Label no respondio: $($_.Exception.Message)"
        return $null
    }
}

Write-Host "Cardbook Mobile QA" -ForegroundColor Cyan
Write-Host "Project: $ProjectRoot"
Write-Host "Mobile:  $MobileRoot"
Write-Host "API:     $ApiBaseUrl"

$flutter = Get-FlutterCommand
if (-not $flutter) {
    Fail "Flutter no esta disponible. Instala Flutter o define FLUTTER_HOME."
}
else {
    Pass "Flutter disponible: $flutter"
}

Push-Location $ProjectRoot
try {
    Invoke-Step "Django system check" { .\cb_env\Scripts\python.exe manage.py check }
    Invoke-Step "Mobile BFF tests" { .\cb_env\Scripts\python.exe manage.py test mobile }
    Invoke-Step "Cards API tests" { .\cb_env\Scripts\python.exe manage.py test cards }
    Invoke-Step "White Card Job tests" { .\cb_env\Scripts\python.exe manage.py test jobcards }
    Invoke-Step "Support API tests" { .\cb_env\Scripts\python.exe manage.py test support }
    Invoke-Step "Push API tests" { .\cb_env\Scripts\python.exe manage.py test pushnotifications }
}
finally {
    Pop-Location
}

if (-not $SkipRemoteSmoke) {
    Write-Host ""
    Write-Host "Remote smoke" -ForegroundColor Cyan
    $health = Test-JsonEndpoint "/health/" "health"
    if ($health -and $health.status -ne "ok") {
        Fail "health status inesperado: $($health.status)"
    }
    $config = Test-JsonEndpoint "/api/v1/mobile/config/" "mobile config"
    if ($config -and -not $config.data.mobile.dashboard) {
        Fail "mobile config no expone dashboard"
    }
    $android = Test-JsonEndpoint "/android/version/" "android version"
    if ($android) {
        if ($android.latest_version_code -lt 1) { Fail "android version code invalido" }
        if (-not $android.download_url) { Fail "android download_url vacio" }
        if ($android.release_signed -ne $true) {
            Warn "APK publicado no tiene firma release real. Correcto para prueba interna, no para Play Store."
        }
    }
}

if ($flutter) {
    Push-Location $MobileRoot
    try {
        Invoke-Step "Flutter pub get" { & $flutter pub get }
        Invoke-Step "Flutter analyze" { & $flutter analyze --no-fatal-infos }
        Invoke-Step "Flutter tests" { & $flutter test }
        Invoke-Step "Flutter devices" { & $flutter devices }

        if ($BuildDebug -or $InstallOnDevice) {
            Invoke-Step "Flutter debug build" {
                & $flutter build apk --debug --dart-define="CARDBOOK_API_BASE_URL=$ApiBaseUrl"
            }
        }

        if ($BuildRelease) {
            Invoke-Step "Flutter release APK build" {
                powershell -ExecutionPolicy Bypass -File .\tool\build_release.ps1 -ApiBaseUrl $ApiBaseUrl
            }
            Invoke-Step "Verify release artifact" {
                powershell -ExecutionPolicy Bypass -File .\tool\verify_release_signing.ps1
            }
        }

        if ($InstallOnDevice) {
            $apkPath = Join-Path $MobileRoot "build\app\outputs\flutter-apk\app-debug.apk"
            if (Test-Path $apkPath) {
                Invoke-Step "Install debug APK on connected Android device" {
                    & $flutter install --debug
                }
            }
            else {
                Fail "No existe APK debug para instalar: $apkPath"
            }
        }
    }
    finally {
        Pop-Location
    }
}

Write-Host ""
Write-Host "QA summary" -ForegroundColor Cyan
Write-Host "Failures: $($failures.Count)"
Write-Host "Warnings: $($warnings.Count)"

if ($warnings.Count -gt 0) {
    Write-Host ""
    Write-Host "Warnings detail" -ForegroundColor Yellow
    $warnings | ForEach-Object { Write-Host "- $_" -ForegroundColor Yellow }
}

if ($failures.Count -gt 0) {
    Write-Host ""
    Write-Host "Failures detail" -ForegroundColor Red
    $failures | ForEach-Object { Write-Host "- $_" -ForegroundColor Red }
    exit 1
}

exit 0

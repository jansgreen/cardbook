param(
    [string]$ApiBaseUrl = "https://incardbook.com"
)

$ErrorActionPreference = "Stop"
$MobileRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$KeyPropertiesPath = Join-Path $MobileRoot "android\key.properties"

function Test-ReleaseSigningConfig {
    $hasKeyProperties = Test-Path $KeyPropertiesPath
    $hasEnvSigning = $env:CARDBOOK_UPLOAD_STORE_FILE -and
        $env:CARDBOOK_UPLOAD_STORE_PASSWORD -and
        $env:CARDBOOK_UPLOAD_KEY_ALIAS -and
        $env:CARDBOOK_UPLOAD_KEY_PASSWORD

    if (-not $hasKeyProperties -and -not $hasEnvSigning) {
        throw "No hay firma release real. Crea android\key.properties o define CARDBOOK_UPLOAD_*."
    }
}

Push-Location $MobileRoot
try {
    Write-Host "Cardbook production mobile build" -ForegroundColor Cyan
    Write-Host "This command requires a real Android release signing configuration." -ForegroundColor Yellow

    Test-ReleaseSigningConfig

    & (Join-Path $PSScriptRoot "build_release.ps1") -ApiBaseUrl $ApiBaseUrl -RequireReleaseSigning
    if ($LASTEXITCODE -ne 0) {
        throw "El build APK release firmado fallo."
    }

    & (Join-Path $PSScriptRoot "build_release.ps1") -ApiBaseUrl $ApiBaseUrl -AppBundle -RequireReleaseSigning
    if ($LASTEXITCODE -ne 0) {
        throw "El build AAB release firmado fallo."
    }

    & (Join-Path $PSScriptRoot "verify_release_signing.ps1") -RequireReleaseSigning
    if ($LASTEXITCODE -ne 0) {
        throw "La verificacion final del APK firmado fallo."
    }

    Write-Host "Build de produccion completado: APK + AAB firmados." -ForegroundColor Green
}
finally {
    Pop-Location
}

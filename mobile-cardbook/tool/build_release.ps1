param(
    [string]$ApiBaseUrl = "https://cardbook-45cf0409dc07.herokuapp.com",
    [switch]$AppBundle
)

$ErrorActionPreference = "Stop"
$MobileRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$DownloadDir = Join-Path $ProjectRoot "static\downloads"
$PublishedApk = Join-Path $DownloadDir "cardbook.apk"
$PublishedMetadata = Join-Path $DownloadDir "cardbook.apk.json"
$MinFlutterApkSize = 5 * 1024 * 1024

if (-not (Get-Command flutter -ErrorAction SilentlyContinue)) {
    throw "Flutter no esta instalado o no esta en PATH."
}

Push-Location $MobileRoot
try {
    if (-not (Test-Path "android")) {
        flutter create .
    }

    flutter pub get
    if ($LASTEXITCODE -ne 0) { throw "flutter pub get fallo" }

    flutter analyze --no-fatal-infos
    if ($LASTEXITCODE -ne 0) { throw "flutter analyze fallo" }

    flutter test
    if ($LASTEXITCODE -ne 0) { throw "flutter test fallo" }

    if ($AppBundle) {
        flutter build appbundle --release --dart-define="CARDBOOK_API_BASE_URL=$ApiBaseUrl"
        if ($LASTEXITCODE -ne 0) { throw "flutter build appbundle fallo" }
    }
    else {
        flutter build apk --release --dart-define="CARDBOOK_API_BASE_URL=$ApiBaseUrl"
        if ($LASTEXITCODE -ne 0) { throw "flutter build apk fallo" }
        $flutterApk = Join-Path $MobileRoot "build\app\outputs\flutter-apk\app-release.apk"
        if (-not (Test-Path $flutterApk)) {
            throw "No se encontro el APK Flutter esperado: $flutterApk"
        }

        $apkSize = (Get-Item $flutterApk).Length
        if ($apkSize -lt $MinFlutterApkSize) {
            throw "El APK generado pesa menos de 5 MB. No parece ser un APK Flutter valido."
        }

        New-Item -ItemType Directory -Force -Path $DownloadDir | Out-Null
        Copy-Item $flutterApk $PublishedApk -Force

        $versionLine = Select-String -Path (Join-Path $MobileRoot "pubspec.yaml") -Pattern "^version:\s*(.+)$" | Select-Object -First 1
        $version = if ($versionLine) { $versionLine.Matches[0].Groups[1].Value.Trim() } else { "0.1.0+1" }
        $versionParts = $version -split "\+"
        $metadata = [ordered]@{
            source = "flutter"
            package = "com.cardbook.app"
            version_name = $versionParts[0]
            version_code = if ($versionParts.Count -gt 1) { [int]$versionParts[1] } else { 1 }
            api_base_url = $ApiBaseUrl
            apk_size = $apkSize
            built_at = (Get-Date).ToUniversalTime().ToString("o")
        }
        $metadata | ConvertTo-Json | Set-Content -Path $PublishedMetadata -Encoding UTF8
        Write-Host "APK Flutter publicado en $PublishedApk" -ForegroundColor Green
    }
}
finally {
    Pop-Location
}

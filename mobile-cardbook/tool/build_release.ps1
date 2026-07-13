param(
    [string]$ApiBaseUrl = "https://cardbook-45cf0409dc07.herokuapp.com",
    [switch]$AppBundle,
    [switch]$RequireReleaseSigning
)

$ErrorActionPreference = "Stop"
$MobileRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$DownloadDir = Join-Path $ProjectRoot "static\downloads"
$PublishedApk = Join-Path $DownloadDir "cardbook.apk"
$PublishedMetadata = Join-Path $DownloadDir "cardbook.apk.json"
$PublishedAab = Join-Path $DownloadDir "cardbook.aab"
$PublishedAabMetadata = Join-Path $DownloadDir "cardbook.aab.json"
$MinFlutterApkSize = 5 * 1024 * 1024
$MinFlutterAabSize = 5 * 1024 * 1024

function Get-FlutterCommand {
    $flutter = Get-Command flutter -ErrorAction SilentlyContinue
    if ($flutter) { return $flutter.Source }

    if ($env:FLUTTER_HOME) {
        $fromHome = Join-Path $env:FLUTTER_HOME "bin\flutter.bat"
        if (Test-Path $fromHome) { return $fromHome }
    }

    $knownPaths = @(
        "C:\src\flutter\bin\flutter.bat",
        "$env:LOCALAPPDATA\flutter\bin\flutter.bat"
    )
    foreach ($path in $knownPaths) {
        if ($path -and (Test-Path $path)) { return $path }
    }

    throw "Flutter no esta instalado o no esta en PATH. Instala Flutter o define FLUTTER_HOME."
}

function Get-ReleaseSigningStatus {
    $keyPropertiesPath = Join-Path $MobileRoot "android\key.properties"
    $hasKeyProperties = Test-Path $keyPropertiesPath
    $hasEnvSigning = $env:CARDBOOK_UPLOAD_STORE_FILE -and
        $env:CARDBOOK_UPLOAD_STORE_PASSWORD -and
        $env:CARDBOOK_UPLOAD_KEY_ALIAS -and
        $env:CARDBOOK_UPLOAD_KEY_PASSWORD

    if ($hasKeyProperties) {
        return "release:key.properties"
    }
    if ($hasEnvSigning) {
        return "release:environment"
    }
    return "debug:fallback"
}

$Flutter = Get-FlutterCommand
$SigningStatus = Get-ReleaseSigningStatus

if ($RequireReleaseSigning -and $SigningStatus -eq "debug:fallback") {
    throw "No hay firma release configurada. Crea mobile-cardbook\android\key.properties o define CARDBOOK_UPLOAD_*."
}

Push-Location $MobileRoot
$PreviousRequireSigning = $env:CARDBOOK_REQUIRE_RELEASE_SIGNING
try {
    if ($RequireReleaseSigning) {
        $env:CARDBOOK_REQUIRE_RELEASE_SIGNING = "true"
    }

    if (-not (Test-Path "android")) {
        & $Flutter create .
    }

    & $Flutter pub get
    if ($LASTEXITCODE -ne 0) { throw "flutter pub get fallo" }

    & $Flutter analyze --no-fatal-infos
    if ($LASTEXITCODE -ne 0) { throw "flutter analyze fallo" }

    & $Flutter test
    if ($LASTEXITCODE -ne 0) { throw "flutter test fallo" }

    New-Item -ItemType Directory -Force -Path $DownloadDir | Out-Null

    $versionLine = Select-String -Path (Join-Path $MobileRoot "pubspec.yaml") -Pattern "^version:\s*(.+)$" | Select-Object -First 1
    $version = if ($versionLine) { $versionLine.Matches[0].Groups[1].Value.Trim() } else { "0.1.0+1" }
    $versionParts = $version -split "\+"

    function New-ArtifactMetadata($ArtifactPath, $ArtifactType) {
        $artifactSize = (Get-Item $ArtifactPath).Length
        $sha256 = (Get-FileHash -Path $ArtifactPath -Algorithm SHA256).Hash.ToLowerInvariant()
        return [ordered]@{
            source = "flutter"
            artifact_type = $ArtifactType
            build_type = "release"
            signing = $SigningStatus
            release_signed = $SigningStatus -ne "debug:fallback"
            package = "com.cardbook.app"
            version_name = $versionParts[0]
            version_code = if ($versionParts.Count -gt 1) { [int]$versionParts[1] } else { 1 }
            api_base_url = $ApiBaseUrl
            artifact_size = $artifactSize
            apk_size = if ($ArtifactType -eq "apk") { $artifactSize } else { 0 }
            aab_size = if ($ArtifactType -eq "aab") { $artifactSize } else { 0 }
            sha256 = $sha256
            built_at = (Get-Date).ToUniversalTime().ToString("o")
        }
    }

    if ($AppBundle) {
        & $Flutter build appbundle --release --dart-define="CARDBOOK_API_BASE_URL=$ApiBaseUrl"
        if ($LASTEXITCODE -ne 0) { throw "flutter build appbundle fallo" }
        $flutterAab = Join-Path $MobileRoot "build\app\outputs\bundle\release\app-release.aab"
        if (-not (Test-Path $flutterAab)) {
            throw "No se encontro el AAB Flutter esperado: $flutterAab"
        }

        $aabSize = (Get-Item $flutterAab).Length
        if ($aabSize -lt $MinFlutterAabSize) {
            throw "El AAB generado pesa menos de 5 MB. No parece ser un AAB Flutter valido."
        }

        Copy-Item $flutterAab $PublishedAab -Force
        New-ArtifactMetadata $PublishedAab "aab" | ConvertTo-Json | Set-Content -Path $PublishedAabMetadata -Encoding UTF8
        Write-Host "AAB Flutter publicado en $PublishedAab" -ForegroundColor Green
    }
    else {
        & $Flutter build apk --release --dart-define="CARDBOOK_API_BASE_URL=$ApiBaseUrl"
        if ($LASTEXITCODE -ne 0) { throw "flutter build apk fallo" }
        $flutterApk = Join-Path $MobileRoot "build\app\outputs\flutter-apk\app-release.apk"
        if (-not (Test-Path $flutterApk)) {
            throw "No se encontro el APK Flutter esperado: $flutterApk"
        }

        $apkSize = (Get-Item $flutterApk).Length
        if ($apkSize -lt $MinFlutterApkSize) {
            throw "El APK generado pesa menos de 5 MB. No parece ser un APK Flutter valido."
        }

        Copy-Item $flutterApk $PublishedApk -Force

        New-ArtifactMetadata $PublishedApk "apk" | ConvertTo-Json | Set-Content -Path $PublishedMetadata -Encoding UTF8
        Write-Host "APK Flutter publicado en $PublishedApk" -ForegroundColor Green
    }
}
finally {
    $env:CARDBOOK_REQUIRE_RELEASE_SIGNING = $PreviousRequireSigning
    Pop-Location
}

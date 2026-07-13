param(
    [string]$ArtifactPath = "",
    [switch]$RequireReleaseSigning
)

$ErrorActionPreference = "Stop"
$MobileRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path

if (-not $ArtifactPath) {
    $ArtifactPath = Join-Path $ProjectRoot "static\downloads\cardbook.apk"
}

$ArtifactPath = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($ArtifactPath)
if (-not (Test-Path $ArtifactPath)) {
    throw "No existe el artefacto: $ArtifactPath"
}

$MetadataPath = Join-Path (Split-Path -Parent $ArtifactPath) "cardbook.apk.json"
$SigningStatus = "unknown"
if (Test-Path $MetadataPath) {
    $metadata = Get-Content $MetadataPath -Raw | ConvertFrom-Json
    $SigningStatus = [string]$metadata.signing
}

Write-Host "Artefacto: $ArtifactPath" -ForegroundColor Cyan
Write-Host "Tamano: $((Get-Item $ArtifactPath).Length) bytes"
Write-Host "SHA256: $((Get-FileHash -Path $ArtifactPath -Algorithm SHA256).Hash.ToLowerInvariant())"
Write-Host "Metadata signing: $SigningStatus"

if ($ArtifactPath.ToLowerInvariant().EndsWith(".apk")) {
    $apkSignerCandidates = @()
    if ($env:ANDROID_HOME) {
        $apkSignerCandidates += Get-ChildItem -Path (Join-Path $env:ANDROID_HOME "build-tools") -Filter "apksigner.bat" -Recurse -ErrorAction SilentlyContinue
    }
    $apkSignerCandidates += Get-ChildItem -Path "$env:LOCALAPPDATA\Android\Sdk\build-tools" -Filter "apksigner.bat" -Recurse -ErrorAction SilentlyContinue
    $apkSigner = $apkSignerCandidates | Sort-Object FullName -Descending | Select-Object -First 1

    if ($apkSigner) {
        & $apkSigner.FullName verify --verbose --print-certs $ArtifactPath
        if ($LASTEXITCODE -ne 0) {
            throw "apksigner reporto una firma APK invalida."
        }
    }
    else {
        Write-Host "apksigner no encontrado; se valido solo metadata y hash." -ForegroundColor Yellow
    }
}

if ($RequireReleaseSigning -and ($SigningStatus -eq "debug:fallback" -or $SigningStatus -eq "unknown")) {
    throw "El artefacto no tiene firma release real segun metadata."
}

Write-Host "Verificacion completada." -ForegroundColor Green

param(
    [string]$Alias = "cardbook-upload",
    [string]$KeystorePath = "",
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$MobileRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$AndroidRoot = Join-Path $MobileRoot "android"
$KeyPropertiesPath = Join-Path $AndroidRoot "key.properties"

function Get-KeytoolCommand {
    $keytool = Get-Command keytool -ErrorAction SilentlyContinue
    if ($keytool) { return $keytool.Source }

    if ($env:JAVA_HOME) {
        $fromJavaHome = Join-Path $env:JAVA_HOME "bin\keytool.exe"
        if (Test-Path $fromJavaHome) { return $fromJavaHome }
    }

    foreach ($path in @(
        "C:\Program Files\Android\Android Studio\jbr\bin\keytool.exe",
        "C:\Program Files\Java\jdk-21\bin\keytool.exe",
        "C:\Program Files\Java\jdk-17\bin\keytool.exe"
    )) {
        if (Test-Path $path) { return $path }
    }

    throw "No se encontro keytool. Instala Android Studio/JDK o configura JAVA_HOME."
}

function ConvertTo-PlainText([securestring]$SecureValue) {
    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($SecureValue)
    try {
        return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
    }
    finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
    }
}

if (-not $KeystorePath) {
    $SecureDir = Join-Path $HOME "cardbook-secure"
    $KeystorePath = Join-Path $SecureDir "cardbook-upload-key.jks"
}

$KeystorePath = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($KeystorePath)
$KeystoreDir = Split-Path -Parent $KeystorePath
New-Item -ItemType Directory -Force -Path $KeystoreDir | Out-Null

if ((Test-Path $KeystorePath) -and -not $Force) {
    throw "El keystore ya existe: $KeystorePath. Usa -Force solo si quieres reemplazarlo."
}

if ((Test-Path $KeyPropertiesPath) -and -not $Force) {
    throw "android\key.properties ya existe. Usa -Force solo si quieres reemplazarlo."
}

$storePassword = ConvertTo-PlainText (Read-Host "Store password" -AsSecureString)
$keyPassword = ConvertTo-PlainText (Read-Host "Key password" -AsSecureString)

if ($storePassword.Length -lt 8 -or $keyPassword.Length -lt 8) {
    throw "Las contrasenas deben tener al menos 8 caracteres."
}

$keytool = Get-KeytoolCommand

& $keytool -genkeypair `
    -v `
    -keystore $KeystorePath `
    -storetype JKS `
    -keyalg RSA `
    -keysize 2048 `
    -validity 10000 `
    -alias $Alias `
    -storepass $storePassword `
    -keypass $keyPassword `
    -dname "CN=Cardbook, OU=Mobile, O=Cardbook, L=Paterson, S=NJ, C=US"

if ($LASTEXITCODE -ne 0) {
    throw "keytool no pudo generar el keystore."
}

$escapedPath = $KeystorePath -replace "\\", "\\\\"
$content = @"
storePassword=$storePassword
keyPassword=$keyPassword
keyAlias=$Alias
storeFile=$escapedPath
"@

Set-Content -Path $KeyPropertiesPath -Value $content -Encoding UTF8

Write-Host "Upload keystore creado en $KeystorePath" -ForegroundColor Green
Write-Host "Archivo android\key.properties creado. No lo subas a Git." -ForegroundColor Yellow
Write-Host "Build Play Store:" -ForegroundColor Cyan
Write-Host ".\tool\build_release.ps1 -AppBundle -RequireReleaseSigning"

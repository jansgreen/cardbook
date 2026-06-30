$ErrorActionPreference = "Stop"

function Invoke-Step($Label, $Executable, [string[]]$Arguments) {
    Write-Host "== $Label =="
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Label failed with exit code $LASTEXITCODE"
    }
}

$Project = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $Project
$Sdk = Join-Path $env:LOCALAPPDATA "Android\Sdk"
$Platform = Join-Path $Sdk "platforms\android-35\android.jar"
$BuildTools = Join-Path $Sdk "build-tools\35.0.0"
$Aapt2 = Join-Path $BuildTools "aapt2.exe"
$D8 = Join-Path $BuildTools "d8.bat"
$Zipalign = Join-Path $BuildTools "zipalign.exe"
$Apksigner = Join-Path $BuildTools "apksigner.bat"
$JavaHome = "C:\Program Files\Android\Android Studio\jbr"
$Javac = Join-Path $JavaHome "bin\javac.exe"
$Jar = Join-Path $JavaHome "bin\jar.exe"
$Keytool = Join-Path $JavaHome "bin\keytool.exe"

foreach ($RequiredPath in @($Platform, $Aapt2, $D8, $Zipalign, $Apksigner, $Javac, $Jar, $Keytool)) {
    if (-not (Test-Path $RequiredPath)) {
        throw "Required Android build tool not found: $RequiredPath"
    }
}

$Out = Join-Path $Project "manual-build"
$ResZip = Join-Path $Out "resources.zip"
$Gen = Join-Path $Out "gen"
$Classes = Join-Path $Out "classes"
$Dex = Join-Path $Out "dex"
$Linked = Join-Path $Out "linked.apk"
$Unsigned = Join-Path $Out "unsigned.apk"
$Aligned = Join-Path $Out "aligned.apk"
$Signed = Join-Path $Out "cardbook-debug.apk"
$Keystore = Join-Path $Project "debug.keystore"
$FinalApk = Join-Path $RepoRoot "static\downloads\cardbook.apk"

Remove-Item $Out -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force $Out, $Gen, $Classes, $Dex | Out-Null
New-Item -ItemType Directory -Force (Split-Path -Parent $FinalApk) | Out-Null

Invoke-Step "aapt2 compile" $Aapt2 ([string[]]@(
    "compile",
    "--dir", (Join-Path $Project "app\src\main\res"),
    "-o", $ResZip
))

Invoke-Step "aapt2 link" $Aapt2 ([string[]]@(
    "link",
    "-o", $Linked,
    "-I", $Platform,
    "--manifest", (Join-Path $Project "app\src\main\AndroidManifest.xml"),
    "--java", $Gen,
    "--auto-add-overlay",
    $ResZip
))

$JavaFiles = [string[]]@(
    (Join-Path $Gen "com\cardbook\app\R.java"),
    (Join-Path $Project "app\src\main\java\com\cardbook\app\MainActivity.java")
)
$JavacArgs = [System.Collections.Generic.List[string]]::new()
$JavacArgs.AddRange([string[]]@(
    "-encoding", "UTF-8",
    "-source", "8",
    "-target", "8",
    "-bootclasspath", $Platform,
    "-d", $Classes
))
$JavacArgs.AddRange($JavaFiles)
Invoke-Step "javac" $Javac ([string[]]$JavacArgs.ToArray())

$ClassFiles = [string[]](Get-ChildItem $Classes -Recurse -Filter *.class | ForEach-Object { $_.FullName })
$D8Args = [System.Collections.Generic.List[string]]::new()
$D8Args.AddRange([string[]]@("--min-api", "26", "--output", $Dex))
$D8Args.AddRange($ClassFiles)
Invoke-Step "d8" $D8 ([string[]]$D8Args.ToArray())

Copy-Item $Linked $Unsigned -Force
Invoke-Step "jar add dex" $Jar ([string[]]@("uf", $Unsigned, "-C", $Dex, "classes.dex"))
Invoke-Step "zipalign" $Zipalign ([string[]]@("-f", "4", $Unsigned, $Aligned))

if (-not (Test-Path $Keystore)) {
    Invoke-Step "keytool debug keystore" $Keytool ([string[]]@(
        "-genkeypair",
        "-v",
        "-keystore", $Keystore,
        "-storepass", "android",
        "-alias", "androiddebugkey",
        "-keypass", "android",
        "-keyalg", "RSA",
        "-keysize", "2048",
        "-validity", "10000",
        "-dname", "CN=Android Debug,O=Android,C=US"
    ))
}

Invoke-Step "apksigner sign" $Apksigner ([string[]]@(
    "sign",
    "--ks", $Keystore,
    "--ks-pass", "pass:android",
    "--key-pass", "pass:android",
    "--out", $Signed,
    $Aligned
))
Invoke-Step "apksigner verify" $Apksigner ([string[]]@("verify", $Signed))

Copy-Item $Signed $FinalApk -Force
Get-Item $FinalApk | Select-Object FullName, Length, LastWriteTime

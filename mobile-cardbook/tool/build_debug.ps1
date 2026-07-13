param(
    [string]$ApiBaseUrl = "https://cardbook-45cf0409dc07.herokuapp.com"
)

$ErrorActionPreference = "Stop"

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

$Flutter = Get-FlutterCommand

Push-Location (Join-Path $PSScriptRoot "..")
try {
    & $Flutter pub get
    & $Flutter analyze --no-fatal-infos
    & $Flutter test
    & $Flutter build apk --debug --dart-define="CARDBOOK_API_BASE_URL=$ApiBaseUrl"
}
finally {
    Pop-Location
}

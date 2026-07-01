param(
    [string]$ApiBaseUrl = "https://cardbook-45cf0409dc07.herokuapp.com",
    [switch]$AppBundle
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command flutter -ErrorAction SilentlyContinue)) {
    throw "Flutter no esta instalado o no esta en PATH."
}

Push-Location (Join-Path $PSScriptRoot "..")
try {
    flutter pub get
    flutter analyze
    flutter test

    if ($AppBundle) {
        flutter build appbundle --release --dart-define="CARDBOOK_API_BASE_URL=$ApiBaseUrl"
    }
    else {
        flutter build apk --release --dart-define="CARDBOOK_API_BASE_URL=$ApiBaseUrl"
    }
}
finally {
    Pop-Location
}

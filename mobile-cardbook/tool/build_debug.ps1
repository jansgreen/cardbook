param(
    [string]$ApiBaseUrl = "https://cardbook-45cf0409dc07.herokuapp.com"
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command flutter -ErrorAction SilentlyContinue)) {
    throw "Flutter no esta instalado o no esta en PATH."
}

Push-Location (Join-Path $PSScriptRoot "..")
try {
    flutter pub get
    flutter analyze --no-fatal-infos
    flutter test
    flutter build apk --debug --dart-define="CARDBOOK_API_BASE_URL=$ApiBaseUrl"
}
finally {
    Pop-Location
}

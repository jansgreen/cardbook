#!/usr/bin/env bash
set -euo pipefail

API_BASE_URL="${1:-https://cardbook-45cf0409dc07.herokuapp.com}"
BUILD_TARGET="${2:-apk}"

if ! command -v flutter >/dev/null 2>&1; then
  echo "Flutter no esta instalado o no esta en PATH." >&2
  exit 1
fi

cd "$(dirname "$0")/.."

flutter pub get
flutter analyze
flutter test

if [ "$BUILD_TARGET" = "aab" ]; then
  flutter build appbundle --release --dart-define="CARDBOOK_API_BASE_URL=$API_BASE_URL"
else
  flutter build apk --release --dart-define="CARDBOOK_API_BASE_URL=$API_BASE_URL"
fi

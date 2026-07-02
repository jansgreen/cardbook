#!/usr/bin/env bash
set -euo pipefail

API_BASE_URL="${1:-https://cardbook-45cf0409dc07.herokuapp.com}"
BUILD_TARGET="${2:-apk}"

if ! command -v flutter >/dev/null 2>&1; then
  echo "Flutter no esta instalado o no esta en PATH." >&2
  exit 1
fi

cd "$(dirname "$0")/.."
MOBILE_ROOT="$(pwd)"
PROJECT_ROOT="$(cd .. && pwd)"

if [ ! -d "android" ]; then
  flutter create .
fi

flutter pub get
flutter analyze --no-fatal-infos
flutter test

if [ "$BUILD_TARGET" = "aab" ]; then
  flutter build appbundle --release --dart-define="CARDBOOK_API_BASE_URL=$API_BASE_URL"
else
  flutter build apk --release --dart-define="CARDBOOK_API_BASE_URL=$API_BASE_URL"
  FLUTTER_APK="$MOBILE_ROOT/build/app/outputs/flutter-apk/app-release.apk"
  PUBLISHED_DIR="$PROJECT_ROOT/static/downloads"
  PUBLISHED_APK="$PUBLISHED_DIR/cardbook.apk"
  PUBLISHED_METADATA="$PUBLISHED_DIR/cardbook.apk.json"
  APK_SIZE="$(wc -c < "$FLUTTER_APK")"
  if [ "$APK_SIZE" -lt 5242880 ]; then
    echo "El APK generado pesa menos de 5 MB. No parece ser un APK Flutter valido." >&2
    exit 1
  fi
  mkdir -p "$PUBLISHED_DIR"
  cp "$FLUTTER_APK" "$PUBLISHED_APK"
  VERSION="$(grep '^version:' pubspec.yaml | head -n 1 | sed 's/version:[[:space:]]*//')"
  VERSION_NAME="${VERSION%%+*}"
  VERSION_CODE="${VERSION##*+}"
  cat > "$PUBLISHED_METADATA" <<EOF
{
  "source": "flutter",
  "package": "com.cardbook.app",
  "version_name": "$VERSION_NAME",
  "version_code": $VERSION_CODE,
  "api_base_url": "$API_BASE_URL",
  "apk_size": $APK_SIZE,
  "built_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
}
EOF
  echo "APK Flutter publicado en $PUBLISHED_APK"
fi

#!/usr/bin/env bash
set -euo pipefail

API_BASE_URL="${1:-https://cardbook-45cf0409dc07.herokuapp.com}"
BUILD_TARGET="${2:-apk}"
REQUIRE_RELEASE_SIGNING="${3:-false}"

if command -v flutter >/dev/null 2>&1; then
  FLUTTER_BIN="flutter"
elif [ -n "${FLUTTER_HOME:-}" ] && [ -x "$FLUTTER_HOME/bin/flutter" ]; then
  FLUTTER_BIN="$FLUTTER_HOME/bin/flutter"
elif [ -x "/c/src/flutter/bin/flutter" ]; then
  FLUTTER_BIN="/c/src/flutter/bin/flutter"
else
  echo "Flutter no esta instalado o no esta en PATH. Instala Flutter o define FLUTTER_HOME." >&2
  exit 1
fi

cd "$(dirname "$0")/.."
MOBILE_ROOT="$(pwd)"
PROJECT_ROOT="$(cd .. && pwd)"

if [ -f "$MOBILE_ROOT/android/key.properties" ]; then
  SIGNING_STATUS="release:key.properties"
elif [ -n "${CARDBOOK_UPLOAD_STORE_FILE:-}" ] \
  && [ -n "${CARDBOOK_UPLOAD_STORE_PASSWORD:-}" ] \
  && [ -n "${CARDBOOK_UPLOAD_KEY_ALIAS:-}" ] \
  && [ -n "${CARDBOOK_UPLOAD_KEY_PASSWORD:-}" ]; then
  SIGNING_STATUS="release:environment"
else
  SIGNING_STATUS="debug:fallback"
fi

if [ "$REQUIRE_RELEASE_SIGNING" = "true" ] && [ "$SIGNING_STATUS" = "debug:fallback" ]; then
  echo "No hay firma release configurada. Crea android/key.properties o define CARDBOOK_UPLOAD_*." >&2
  exit 1
fi

if [ "$REQUIRE_RELEASE_SIGNING" = "true" ]; then
  export CARDBOOK_REQUIRE_RELEASE_SIGNING=true
fi

if [ ! -d "android" ]; then
  "$FLUTTER_BIN" create .
fi

"$FLUTTER_BIN" pub get
"$FLUTTER_BIN" analyze --no-fatal-infos
"$FLUTTER_BIN" test

if [ "$BUILD_TARGET" = "aab" ]; then
  "$FLUTTER_BIN" build appbundle --release --dart-define="CARDBOOK_API_BASE_URL=$API_BASE_URL"
else
  "$FLUTTER_BIN" build apk --release --dart-define="CARDBOOK_API_BASE_URL=$API_BASE_URL"
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
  SHA256="$(sha256sum "$PUBLISHED_APK" | awk '{print $1}')"
  cat > "$PUBLISHED_METADATA" <<EOF
{
  "source": "flutter",
  "build_type": "release",
  "signing": "$SIGNING_STATUS",
  "release_signed": $([ "$SIGNING_STATUS" = "debug:fallback" ] && echo "false" || echo "true"),
  "package": "com.cardbook.app",
  "version_name": "$VERSION_NAME",
  "version_code": $VERSION_CODE,
  "api_base_url": "$API_BASE_URL",
  "apk_size": $APK_SIZE,
  "sha256": "$SHA256",
  "built_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
}
EOF
  echo "APK Flutter publicado en $PUBLISHED_APK"
fi

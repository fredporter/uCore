#!/bin/bash
# Install the pinned, reviewed NanoCoder build beneath UDOS_HOME.

set -euo pipefail

VERSION="1.30.0"
PACKAGE="@nanocollective/nanocoder@$VERSION"
EXPECTED_SHA256="ba9323207bd2d2b4d5ac9d7c77f08f7c2405415d73e8fe0b8929e7366df6dccc"
UCORE_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PATCH_FILE="$UCORE_ROOT/vendor/patches/nanocoder-1.30.0-task-store.patch"

if [[ -z "${UDOS_HOME:-}" ]]; then
  echo "UDOS_HOME must be set" >&2
  exit 2
fi

INSTALL_ROOT="$UDOS_HOME/tools/nanocoder/$VERSION"
ARCHIVE_DIR="$UDOS_HOME/vendor/artifacts/nanocoder"
ARCHIVE="$ARCHIVE_DIR/nanocollective-nanocoder-$VERSION.tgz"
STAGING="$INSTALL_ROOT.staging"

mkdir -p "$ARCHIVE_DIR" "$(dirname "$INSTALL_ROOT")"
npm pack "$PACKAGE" --pack-destination "$ARCHIVE_DIR" >/dev/null

ACTUAL_SHA256="$(shasum -a 256 "$ARCHIVE" | awk '{print $1}')"
if [[ "$ACTUAL_SHA256" != "$EXPECTED_SHA256" ]]; then
  echo "NanoCoder artifact hash mismatch" >&2
  exit 1
fi

if [[ -e "$STAGING" ]]; then
  echo "Staging path already exists: $STAGING" >&2
  exit 1
fi

mkdir -p "$STAGING"
cd "$STAGING"
npm install "$PACKAGE" --ignore-scripts --no-audit --no-fund --save-exact
patch -p1 < "$PATCH_FILE"

INSTALLED_VERSION="$(./node_modules/.bin/nanocoder --version)"
if [[ "$INSTALLED_VERSION" != "$VERSION" ]]; then
  echo "Unexpected installed NanoCoder version: $INSTALLED_VERSION" >&2
  exit 1
fi

if [[ -e "$INSTALL_ROOT" ]]; then
  echo "Install already exists: $INSTALL_ROOT" >&2
  exit 1
fi
mv "$STAGING" "$INSTALL_ROOT"
echo "$INSTALL_ROOT/node_modules/.bin/nanocoder"

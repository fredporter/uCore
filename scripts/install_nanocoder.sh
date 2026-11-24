#!/bin/bash
# Install the pinned, reviewed NanoCoder build beneath UDOS_HOME.
#
# The archive under UDOS_HOME/vendor/artifacts/nanocoder is the delivery
# artifact. It is verified against EXPECTED_SHA256 before use, the installed
# package is compared byte-for-byte with that archive, and only then are the
# reviewed patches from uCore Git (vendor/patches) applied.
#
# Lifecycle:
#   scripts/install_nanocoder.sh              install when absent
#   scripts/install_nanocoder.sh --replace    rebuild, replacing the install
#   scripts/install_nanocoder.sh --uninstall  retire the install (reversible)
#   scripts/install_nanocoder.sh --offline    never touch the network
#   scripts/install_nanocoder.sh --purge-retired
#                                             delete the retired copy instead of
#                                             keeping it for rollback

set -euo pipefail

VERSION="1.30.0"
PACKAGE="@nanocollective/nanocoder@$VERSION"
EXPECTED_SHA256="ba9323207bd2d2b4d5ac9d7c77f08f7c2405415d73e8fe0b8929e7366df6dccc"
UCORE_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PATCH_FILES="nanocoder-1.30.0-task-store.patch nanocoder-1.30.0-acp-permissions.patch"
PACKAGE_REL="node_modules/@nanocollective/nanocoder"

ACTION="install"
OFFLINE="0"
PURGE_RETIRED="0"

usage() {
  sed -n '2,16p' "$0" | sed 's/^# \{0,1\}//'
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --uninstall) ACTION="uninstall" ;;
    --replace) ACTION="replace" ;;
    --offline) OFFLINE="1" ;;
    --purge-retired) PURGE_RETIRED="1" ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
  shift
done

if [ -z "${UDOS_HOME:-}" ]; then
  echo "UDOS_HOME must be set" >&2
  exit 2
fi
case "$UDOS_HOME" in
  /*) ;;
  *) echo "UDOS_HOME must be an absolute path" >&2; exit 2 ;;
esac

INSTALL_ROOT="$UDOS_HOME/tools/nanocoder/$VERSION"
ARCHIVE_DIR="$UDOS_HOME/vendor/artifacts/nanocoder"
ARCHIVE="$ARCHIVE_DIR/nanocollective-nanocoder-$VERSION.tgz"
STAGING="$INSTALL_ROOT.staging"
RETIRED_ROOT="$UDOS_HOME/tmp/nanocoder-retired"
RETIRED_PATH=""

verify_archive() {
  actual="$(shasum -a 256 "$ARCHIVE" | awk '{print $1}')"
  if [ "$actual" != "$EXPECTED_SHA256" ]; then
    echo "NanoCoder artifact hash mismatch" >&2
    echo "  expected: $EXPECTED_SHA256" >&2
    echo "  actual:   $actual" >&2
    echo "  archive:  $ARCHIVE" >&2
    echo "Refusing to install from an unverified artifact. Remove it to re-fetch." >&2
    exit 1
  fi
}

ensure_archive() {
  if [ -f "$ARCHIVE" ]; then
    verify_archive
    echo "Using verified artifact: $ARCHIVE" >&2
    return 0
  fi
  if [ "$OFFLINE" = "1" ]; then
    echo "Offline install requested but the pinned artifact is missing: $ARCHIVE" >&2
    echo "Seed it with: npm pack $PACKAGE --pack-destination \"$ARCHIVE_DIR\"" >&2
    exit 3
  fi
  mkdir -p "$ARCHIVE_DIR"
  npm pack "$PACKAGE" --pack-destination "$ARCHIVE_DIR" >/dev/null
  verify_archive
}

retire_install() {
  if [ ! -e "$INSTALL_ROOT" ]; then
    return 0
  fi
  stamp="$(date -u +%Y%m%dT%H%M%SZ)"
  retired="$RETIRED_ROOT/$VERSION-$stamp"
  mkdir -p "$RETIRED_ROOT"
  if [ -e "$retired" ]; then
    echo "Retired path already exists: $retired" >&2
    exit 1
  fi
  mv "$INSTALL_ROOT" "$retired"
  RETIRED_PATH="$retired"
  if [ "$PURGE_RETIRED" = "1" ]; then
    rm -rf "$retired"
    RETIRED_PATH=""
    echo "Uninstalled NanoCoder $VERSION (retired copy purged)."
  else
    echo "Uninstalled NanoCoder $VERSION; retired copy kept at $retired"
    echo "Rollback: mv \"$retired\" \"$INSTALL_ROOT\""
  fi
}

if [ "$ACTION" = "uninstall" ]; then
  retire_install
  exit 0
fi

if [ -e "$INSTALL_ROOT" ] && [ "$ACTION" = "install" ]; then
  echo "Install already exists: $INSTALL_ROOT" >&2
  echo "Use --replace to rebuild it or --uninstall to retire it." >&2
  exit 1
fi

ensure_archive

if [ -e "$STAGING" ]; then
  echo "Staging path already exists: $STAGING" >&2
  exit 1
fi

cleanup() {
  rm -rf "$STAGING"
}
trap cleanup EXIT

mkdir -p "$(dirname "$INSTALL_ROOT")" "$STAGING"
cd "$STAGING"
printf '{\n  "name": "nanocoder-install",\n  "private": true\n}\n' > package.json

if [ "$OFFLINE" = "1" ]; then
  npm install "$PACKAGE" --save-exact --ignore-scripts --no-audit --no-fund --offline
else
  npm install "$PACKAGE" --save-exact --ignore-scripts --no-audit --no-fund
fi

if [ ! -d "$PACKAGE_REL" ]; then
  echo "Installed package directory is missing: $STAGING/$PACKAGE_REL" >&2
  exit 1
fi

mkdir -p ".artifact-check"
tar -xzf "$ARCHIVE" -C ".artifact-check"
if ! diff -r ".artifact-check/package" "$PACKAGE_REL" >/dev/null 2>&1; then
  echo "Installed package does not match the verified artifact: $ARCHIVE" >&2
  diff -r ".artifact-check/package" "$PACKAGE_REL" 2>&1 | head -20 >&2
  exit 1
fi
rm -rf ".artifact-check"

for patch_name in $PATCH_FILES; do
  patch -p1 < "$UCORE_ROOT/vendor/patches/$patch_name"
done

grep -q 'UCORE_ACP_GOVERNED' "$PACKAGE_REL/dist/acp/acp-conversation.js" || {
  echo "ACP permissions patch did not apply" >&2
  exit 1
}
grep -q 'NANOCODER_TASKS_DIR' "$PACKAGE_REL/dist/tools/tasks/storage.js" || {
  echo "Task store patch did not apply" >&2
  exit 1
}

INSTALLED_VERSION="$(./node_modules/.bin/nanocoder --version)"
if [ "$INSTALLED_VERSION" != "$VERSION" ]; then
  echo "Unexpected installed NanoCoder version: $INSTALLED_VERSION" >&2
  exit 1
fi

cd /
if [ -e "$INSTALL_ROOT" ]; then
  retire_install
fi

if ! mv "$STAGING" "$INSTALL_ROOT"; then
  if [ -n "$RETIRED_PATH" ] && [ -d "$RETIRED_PATH" ]; then
    mv "$RETIRED_PATH" "$INSTALL_ROOT"
    echo "Install swap failed; previous install restored." >&2
  fi
  exit 1
fi
trap - EXIT

echo "Installed NanoCoder $VERSION"
echo "Artifact:  $ARCHIVE"
echo "SHA-256:   $EXPECTED_SHA256"
if [ -n "$RETIRED_PATH" ]; then
  echo "Retired:   $RETIRED_PATH"
fi
echo "$INSTALL_ROOT/node_modules/.bin/nanocoder"

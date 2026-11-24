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
#   scripts/install_nanocoder.sh --deps PATH  use this npm cache bundle or dir
#   scripts/install_nanocoder.sh --build-deps PATH
#                                             build the pinned dependency
#                                             bundle from a clean install
#   scripts/install_nanocoder.sh --rebuild-deps
#                                             re-resolve the lock and rebuild an
#                                             existing dependency bundle
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
REBUILD_DEPS="0"
DEPS_INPUT=""
BUILD_DEPS_TARGET=""
NPM_CACHE=""
CACHE_TMP=""

usage() {
  sed -n '2,/^$/p' "$0" | sed 's/^# \{0,1\}//'
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --uninstall) ACTION="uninstall" ;;
    --replace) ACTION="replace" ;;
    --offline) OFFLINE="1" ;;
    --purge-retired) PURGE_RETIRED="1" ;;
    --rebuild-deps) REBUILD_DEPS="1" ;;
    --deps)
      shift
      if [ "$#" -eq 0 ]; then echo "--deps needs a path" >&2; exit 2; fi
      DEPS_INPUT="$1"
      ;;
    --build-deps)
      shift
      if [ "$#" -eq 0 ]; then echo "--build-deps needs a path" >&2; exit 2; fi
      BUILD_DEPS_TARGET="$1"
      ;;
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
DEPS_BUNDLE="$ARCHIVE_DIR/nanocoder-$VERSION-npm-cache.tar.gz"
DEPS_LOCK="$ARCHIVE_DIR/nanocoder-$VERSION-deps-lock.json"
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

verify_deps_bundle() {
  bundle="$1"
  sidecar="$bundle.sha256"
  if [ ! -f "$sidecar" ]; then
    echo "Dependency bundle has no digest sidecar: $sidecar" >&2
    echo "Rebuild it with: $0 --build-deps \"$bundle\"" >&2
    exit 1
  fi
  expected="$(awk '{print $1}' "$sidecar")"
  actual="$(shasum -a 256 "$bundle" | awk '{print $1}')"
  if [ "$actual" != "$expected" ]; then
    echo "Dependency bundle hash mismatch" >&2
    echo "  expected: $expected" >&2
    echo "  actual:   $actual" >&2
    echo "  bundle:   $bundle" >&2
    exit 1
  fi
  echo "Dependency bundle verified: sha256 $actual" >&2
}

resolve_cache_dir() {
  cache_source=""
  if [ -n "$DEPS_INPUT" ]; then
    cache_source="$DEPS_INPUT"
  elif [ -f "$DEPS_BUNDLE" ]; then
    cache_source="$DEPS_BUNDLE"
    echo "Using dependency bundle: $DEPS_BUNDLE" >&2
  fi

  if [ -z "$cache_source" ]; then
    return 0
  fi
  if [ ! -e "$cache_source" ]; then
    echo "Dependency bundle not found: $cache_source" >&2
    exit 1
  fi
  if [ -d "$cache_source" ]; then
    echo "Warning: unverified dependency directory: $cache_source" >&2
    NPM_CACHE="$cache_source"
    return 0
  fi

  verify_deps_bundle "$cache_source"

  CACHE_TMP="$(mktemp -d "${TMPDIR:-/tmp}/nanocoder-cache.XXXXXX")"
  tar -xzf "$cache_source" -C "$CACHE_TMP"
  if [ -d "$CACHE_TMP/cache" ]; then
    NPM_CACHE="$CACHE_TMP/cache"
  else
    NPM_CACHE="$CACHE_TMP"
  fi
  echo "Dependency bundle unpacked: $cache_source" >&2
}

build_deps() {
  target="$1"

  if [ -f "$target" ] && [ "$REBUILD_DEPS" != "1" ]; then
    echo "Dependency bundle already exists: $target" >&2
    echo "Pass --rebuild-deps to regenerate it (and re-resolve the lock)." >&2
    exit 1
  fi

  work="$(mktemp -d "${TMPDIR:-/tmp}/nanocoder-deps.XXXXXX")"
  mkdir -p "$work/project"
  cd "$work/project"
  printf '{\n  "name": "nanocoder-deps",\n  "private": true,\n  "dependencies": {\n    "@nanocollective/nanocoder": "%s"\n  }\n}\n' "$VERSION" > package.json

  if [ -f "$DEPS_LOCK" ] && [ "$REBUILD_DEPS" != "1" ]; then
    cp "$DEPS_LOCK" package-lock.json
    echo "Using pinned dependency lock: $DEPS_LOCK" >&2
  else
    npm install --package-lock-only --ignore-scripts --no-audit --no-fund \
      --cache "$work/cache"
    mkdir -p "$(dirname "$DEPS_LOCK")"
    cp package-lock.json "$DEPS_LOCK"
    echo "Dependency lock written: $DEPS_LOCK" >&2
  fi

  npm ci --ignore-scripts --no-audit --no-fund --cache "$work/cache"

  mkdir -p "$work/check"
  tar -xzf "$ARCHIVE" -C "$work/check"
  if ! diff -r "$work/check/package" "$work/project/node_modules/@nanocollective/nanocoder" >/dev/null 2>&1; then
    echo "Locked registry package differs from the pinned artifact" >&2
    exit 1
  fi

  mkdir -p "$(dirname "$target")"
  tar -czf "$target" -C "$work" cache
  shasum -a 256 "$target" | awk '{print $1}' > "$target.sha256"

  cd /
  rm -rf "$work"
  echo "Dependency bundle: $target"
  echo "Lock:              $DEPS_LOCK"
  echo "SHA-256:           $(awk '{print $1}' "$target.sha256")"
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

if [ -n "$BUILD_DEPS_TARGET" ]; then
  ensure_archive
  build_deps "$BUILD_DEPS_TARGET"
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
  if [ -n "${CACHE_TMP:-}" ]; then
    rm -rf "$CACHE_TMP"
  fi
}
trap cleanup EXIT

resolve_cache_dir
if [ "$OFFLINE" = "1" ] && [ -z "$NPM_CACHE" ]; then
  echo "Offline install requires the pinned dependency bundle:" >&2
  echo "  $DEPS_BUNDLE" >&2
  echo "Build it once online with: $0 --build-deps \"$DEPS_BUNDLE\"" >&2
  exit 3
fi

mkdir -p "$(dirname "$INSTALL_ROOT")" "$STAGING"
cd "$STAGING"
printf '{\n  "name": "nanocoder-install",\n  "private": true\n}\n' > package.json

set -- "$ARCHIVE" --no-save --no-package-lock --ignore-scripts --no-audit --no-fund
if [ -n "$NPM_CACHE" ]; then
  set -- "$@" --cache "$NPM_CACHE"
fi
if [ "$OFFLINE" = "1" ]; then
  set -- "$@" --offline
fi
npm install "$@"

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

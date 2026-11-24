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
DEPS_LOCK="$UCORE_ROOT/vendor/nanocoder-$VERSION-deps-lock.json"
CATALOGUE_SEED="${SONIC_CATALOGUE_SEED:-$HOME/Public/global-knowledge/datasets/distribution_catalogue.json}"
EXPECTED_DEPS_SHA256="d7c9223d4faf67332cf5da7ded5b4d59f42433c8317f025b334cd002864871ff"
EXPECTED_DEPS_BYTES="79618918"
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

catalogue_bundle_digest() {
  seed="$CATALOGUE_SEED"
  if [ ! -f "$seed" ]; then
    return 0
  fi
  python3 -c 'import json,sys
data = json.load(open(sys.argv[1], encoding="utf-8"))
for title in data.get("titles", []):
    for edition in title.get("editions", []):
        for capsule in edition.get("capsules", []):
            if capsule.get("id") == "nanocoder-npm-cache":
                print(capsule.get("sha256", ""))
                raise SystemExit(0)
raise SystemExit(0)' "$seed" 2>/dev/null || true
}

verify_deps_bundle() {
  bundle="$1"
  sidecar="$bundle.sha256"
  actual="$(shasum -a 256 "$bundle" | awk '{print $1}')"
  size="$(wc -c < "$bundle" | tr -d ' ')"

  # The reviewed pin is the trust anchor. A sidecar beside the bundle can be
  # replaced together with it, so it may only confirm the pin, never define it.
  if [ "$actual" != "$EXPECTED_DEPS_SHA256" ]; then
    echo "Dependency bundle does not match the pinned release digest" >&2
    echo "  pinned: $EXPECTED_DEPS_SHA256" >&2
    echo "  actual: $actual" >&2
    echo "  bundle: $bundle" >&2
    exit 1
  fi
  if [ "$size" != "$EXPECTED_DEPS_BYTES" ]; then
    echo "Dependency bundle size mismatch" >&2
    echo "  pinned: $EXPECTED_DEPS_BYTES bytes" >&2
    echo "  actual: $size bytes" >&2
    exit 1
  fi

  if [ -f "$sidecar" ]; then
    sidecar_digest="$(awk '{print $1}' "$sidecar")"
    if [ "$sidecar_digest" != "$EXPECTED_DEPS_SHA256" ]; then
      echo "Dependency bundle sidecar disagrees with the pinned release digest" >&2
      echo "  sidecar: $sidecar_digest" >&2
      echo "  pinned:  $EXPECTED_DEPS_SHA256" >&2
      exit 1
    fi
  else
    echo "Note: no digest sidecar beside the bundle; the pinned release digest was enforced." >&2
  fi

  catalogue_digest="$(catalogue_bundle_digest)"
  if [ -n "$catalogue_digest" ] && [ "$catalogue_digest" != "$EXPECTED_DEPS_SHA256" ]; then
    echo "Layer 0 catalogue and installer disagree on the dependency bundle digest" >&2
    echo "  catalogue: $catalogue_digest" >&2
    echo "  installer: $EXPECTED_DEPS_SHA256" >&2
    exit 1
  fi

  echo "Dependency bundle verified against the pinned release digest: $actual" >&2
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

  if [ -f "$DEPS_LOCK" ]; then
    if [ "$REBUILD_DEPS" != "1" ]; then
      cp "$DEPS_LOCK" package-lock.json
      echo "Using versioned dependency lock: $DEPS_LOCK" >&2
    else
      npm install --package-lock-only --ignore-scripts --no-audit --no-fund \
        --cache "$work/cache"
      cp package-lock.json "$DEPS_LOCK"
      echo "Dependency lock rewritten for review: $DEPS_LOCK" >&2
    fi
  else
    if [ "$REBUILD_DEPS" != "1" ]; then
      echo "Versioned dependency lock is missing: $DEPS_LOCK" >&2
      echo "Run once with --rebuild-deps, review the new lock, and commit it." >&2
      exit 1
    fi
    npm install --package-lock-only --ignore-scripts --no-audit --no-fund \
      --cache "$work/cache"
    cp package-lock.json "$DEPS_LOCK"
    echo "Dependency lock created for review: $DEPS_LOCK" >&2
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
  built_digest="$(awk '{print $1}' "$target.sha256")"
  built_bytes="$(wc -c < "$target" | tr -d ' ')"

  cd /
  rm -rf "$work"
  echo "Dependency bundle: $target"
  echo "Lock:              $DEPS_LOCK"
  echo "SHA-256:           $built_digest"
  if [ "$built_digest" != "$EXPECTED_DEPS_SHA256" ] || [ "$built_bytes" != "$EXPECTED_DEPS_BYTES" ]; then
    echo "Review needed: set EXPECTED_DEPS_SHA256=$built_digest and EXPECTED_DEPS_BYTES=$built_bytes," >&2
    echo "then update the Layer 0 catalogue pin to match." >&2
  fi
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

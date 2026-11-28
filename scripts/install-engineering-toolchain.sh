#!/bin/bash
# install-engineering-toolchain.sh — Advanced Users / Engineering
#
# Reports or installs the toolchain documented in docs/ENGINEERING_TOOLCHAIN.md:
# Node.js 22+, pnpm 9+, Cline CLI, Cline Kanban, fzf, Playwright browsers and
# (optionally) mkcert with its local CA.
#
# Usage: bash scripts/install-engineering-toolchain.sh [--check] [--dry-run] [--no-https]
#
# Effects: npm global installs, one Homebrew/apt package install, Playwright
# browser downloads into the user cache, and — only when mkcert is not already
# trusted — `mkcert -install`, which needs administrator approval. It never
# edits a repository, writes credentials, or adds a launchd job.

set -euo pipefail

CHECK_ONLY=false
DRY_RUN=false
WITH_HTTPS=true

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info() { echo -e "${BLUE}[INFO]${NC}  $1"; }
ok()   { echo -e "${GREEN}[OK]${NC}    $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC}  $1"; }
err()  { echo -e "${RED}[ERROR]${NC} $1"; }

usage() {
    cat <<'EOF'
Engineering toolchain installer — Advanced Users / Engineering

Usage: bash scripts/install-engineering-toolchain.sh [OPTIONS]

Options:
  --check      Report only; exit non-zero when a required tool is missing
  --dry-run    Print the commands that would run, without running them
  --no-https   Skip mkcert and the local CA (no standalone web app)
  --help       Show this help

Required: Node.js 22+, pnpm 9+, Cline CLI, Cline Kanban, fzf, Playwright
(WebKit + Chromium). Optional: mkcert + local CA for the Safari standalone app.
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --check) CHECK_ONLY=true ;;
        --dry-run) DRY_RUN=true ;;
        --no-https) WITH_HTTPS=false ;;
        --help|-h) usage; exit 0 ;;
        *) err "Unknown option: $1"; usage; exit 2 ;;
    esac
    shift
done

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="$REPO_ROOT/frontend-vue"
OS_NAME="$(uname -s)"
MISSING=()
INSTALLED=()

have() { command -v "$1" >/dev/null 2>&1; }

run() {
    if $DRY_RUN; then
        printf '        would run: %s\n' "$*"
    else
        "$@"
    fi
}

# Compare dotted versions: version_ge 22.1.0 22
version_ge() {
    local have_version="${1#v}" want="${2#v}"
    local IFS=.
    local -a a b
    read -r -a a <<<"$have_version"
    read -r -a b <<<"$want"
    local i
    for i in 0 1 2; do
        local ai="${a[$i]:-0}" bi="${b[$i]:-0}"
        ai="${ai%%[!0-9]*}"; bi="${bi%%[!0-9]*}"
        ai="${ai:-0}"; bi="${bi:-0}"
        if ((10#$ai > 10#$bi)); then return 0; fi
        if ((10#$ai < 10#$bi)); then return 1; fi
    done
    return 0
}

record() {
    if [[ "$2" == "ok" ]]; then
        INSTALLED+=("$1")
        ok "$1"
    else
        MISSING+=("$1")
        warn "$1 — $2"
    fi
}

package_manager_install() {
    local brew_formula="$1" apt_package="$2"
    if [[ "$OS_NAME" == "Darwin" ]]; then
        have brew || { err "Homebrew is required to install ${brew_formula}"; return 1; }
        run brew install "$brew_formula"
    elif have apt-get; then
        run sudo apt-get update
        run sudo apt-get install -y "$apt_package"
    else
        err "No supported package manager for ${brew_formula}; install it manually"
        return 1
    fi
}


info "Engineering toolchain — $([[ $CHECK_ONLY == true ]] && echo 'report only' || echo 'install missing')"
[[ $DRY_RUN == true ]] && warn "Dry run: no commands will execute"
echo

# ─── Node.js ─────────────────────────────────────────────────────────
if have node && version_ge "$(node -v)" 22; then
    record "Node.js $(node -v)" ok
else
    record "Node.js 22+" "missing or too old"
    if ! $CHECK_ONLY; then
        if have brew; then run brew install node; else
            err "Install Node.js 22+ from your runtime manager (nvm, fnm) and re-run"
        fi
    fi
fi

# ─── pnpm ────────────────────────────────────────────────────────────
if have pnpm && version_ge "$(pnpm -v)" 9; then
    record "pnpm $(pnpm -v)" ok
else
    record "pnpm 9+" "missing or too old"
    if ! $CHECK_ONLY; then
        if have corepack; then run corepack enable pnpm; else run npm install -g pnpm; fi
    fi
fi

# ─── Cline CLI and Kanban ────────────────────────────────────────────
for tool in cline kanban; do
    if have "$tool"; then
        record "${tool} $($tool --version 2>/dev/null | head -1)" ok
    else
        record "$tool" "not installed"
        if ! $CHECK_ONLY; then run npm install -g "$tool"; fi
    fi
done

# ─── fzf ─────────────────────────────────────────────────────────────
if have fzf; then
    record "fzf $(fzf --version | awk '{print $1}')" ok
else
    record "fzf" "not installed (required by the ucdev/ucusr selector)"
    if ! $CHECK_ONLY; then package_manager_install fzf fzf || true; fi
fi

# ─── Playwright browsers ─────────────────────────────────────────────
PW_CACHE="${PLAYWRIGHT_BROWSERS_PATH:-$HOME/Library/Caches/ms-playwright}"
if [[ -d "$FRONTEND_DIR/node_modules" ]]; then
    if ls "$PW_CACHE" 2>/dev/null | grep -q 'webkit' && ls "$PW_CACHE" 2>/dev/null | grep -q 'chromium'; then
        record "Playwright browsers (webkit + chromium)" ok
    else
        record "Playwright browsers" "webkit and/or chromium not downloaded"
        if ! $CHECK_ONLY; then
            run pnpm --dir "$FRONTEND_DIR" exec playwright install webkit chromium
        fi
    fi
else
    record "Playwright browsers" "frontend dependencies missing (run pnpm install first)"
fi

# ─── mkcert and the local CA ─────────────────────────────────────────
if $WITH_HTTPS; then
    if ! have mkcert; then
        record "mkcert" "not installed"
        if ! $CHECK_ONLY; then package_manager_install mkcert mkcert || true; fi
    else
        record "mkcert" ok
        if [[ "$OS_NAME" == "Darwin" ]] \
            && security find-certificate -c mkcert /Library/Keychains/System.keychain >/dev/null 2>&1; then
            record "mkcert local CA trusted" ok
        else
            record "mkcert local CA" "not trusted (needs administrator approval)"
            if ! $CHECK_ONLY; then
                warn "mkcert -install adds a local CA to the system trust store"
                run mkcert -install
            fi
        fi
    fi
else
    info "Skipping mkcert (--no-https)"
fi

# ─── Summary ─────────────────────────────────────────────────────────
echo
if ((${#MISSING[@]} == 0)); then
    ok "Toolchain complete: ${#INSTALLED[@]} component(s) verified"
    echo "Next: bash scripts/enable-engineering-https.sh status"
    exit 0
fi

warn "${#MISSING[@]} component(s) need attention:"
for item in "${MISSING[@]}"; do echo "  - $item"; done

if $CHECK_ONLY; then
    err "Run without --check to install the missing components"
    exit 1
fi

echo "Re-run with --check to confirm. See docs/ENGINEERING_TOOLCHAIN.md"
exit 0

#!/bin/bash
# enable-engineering-https.sh — Advanced Users / Engineering
#
# Serves the same Vite dev app over a trusted local HTTPS origin so Safari will
# install the standalone web app (File -> Add to Dock). Plain-HTTP localhost is
# refused by Safari's web-app installer.
#
# Usage: bash scripts/enable-engineering-https.sh start|stop|status [--help]
#
# Effects: writes certificates and a log under UDOS_HOME/runtime/engineering-https
# and runs one foreground-free Vite process on the chosen port. It does not edit
# a repository, install a launchd job, or change the documented :5175 runtime.

set -euo pipefail

ACTION="${1:-status}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="$REPO_ROOT/frontend-vue"
UDOS_HOME="${UDOS_HOME:-$HOME/Code/.udos}"
STATE_DIR="$UDOS_HOME/runtime/engineering-https"
PORT="${UCORE_HTTPS_PORT:-5176}"
CERT_FILE="$STATE_DIR/localhost.pem"
KEY_FILE="$STATE_DIR/localhost-key.pem"
LOG_FILE="$STATE_DIR/vite.log"
PID_FILE="$STATE_DIR/vite.pid"
PORT_FILE="$STATE_DIR/port"

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
Local HTTPS for the standalone uCore web app — Advanced Users / Engineering

Usage: bash scripts/enable-engineering-https.sh [start|stop|status]

  start    Ensure a trusted certificate, then serve the dev app on
           https://localhost:${UCORE_HTTPS_PORT:-5176}
  stop     Stop the instance started by this script
  status   Report certificate, trust, listener and PID state

Environment:
  UCORE_HTTPS_PORT   HTTPS port (default 5176)
  UDOS_HOME          Mutable state root (default ~/Code/.udos)

Prerequisite: mkcert installed and its CA trusted (see
docs/ENGINEERING_TOOLCHAIN.md). The documented http runtime on :5175 is not
touched.
EOF
}

port_pid() {
    lsof -nP -iTCP:"$PORT" -sTCP:LISTEN -t 2>/dev/null | head -1
}

ensure_certificate() {
    if [[ -s "$CERT_FILE" && -s "$KEY_FILE" ]]; then
        ok "Certificate present: $CERT_FILE"
        return 0
    fi
    if ! command -v mkcert >/dev/null 2>&1; then
        err "mkcert is not installed. Run: bash scripts/install-engineering-toolchain.sh"
        return 1
    fi
    mkdir -p "$STATE_DIR"
    info "Issuing a local certificate for localhost, 127.0.0.1 and ::1"
    mkcert -cert-file "$CERT_FILE" -key-file "$KEY_FILE" localhost 127.0.0.1 ::1
    ok "Certificate written to $STATE_DIR"
}

ca_trusted() {
    [[ "$(uname -s)" == "Darwin" ]] || return 0
    security find-certificate -c mkcert /Library/Keychains/System.keychain >/dev/null 2>&1
}

certificate_expiry() {
    [[ -s "$CERT_FILE" ]] || return 1
    openssl x509 -enddate -noout -in "$CERT_FILE" 2>/dev/null | cut -d= -f2
}


start_instance() {
    ensure_certificate || exit 1
    if ca_trusted; then
        ok "mkcert CA is trusted in the system keychain"
    else
        warn "mkcert CA is not trusted; Safari will refuse the certificate."
        warn "Run 'mkcert -install' (administrator approval) and retry."
    fi

    local existing
    existing="$(port_pid || true)"
    if [[ -n "$existing" ]]; then
        ok "Port $PORT is already serving (PID $existing)"
        echo "    https://localhost:$PORT/engineering"
        return 0
    fi

    if [[ ! -x "$FRONTEND_DIR/node_modules/.bin/vite" ]]; then
        err "Frontend dependencies are missing. Run: pnpm install"
        return 1
    fi

    info "Starting HTTPS instance on port $PORT"
    (
        cd "$FRONTEND_DIR"
        UCORE_HTTPS_CERT="$CERT_FILE" \
        UCORE_HTTPS_KEY="$KEY_FILE" \
        UCORE_HTTPS_PORT="$PORT" \
        UCORE_PWA_DEV=1 \
        nohup ./node_modules/.bin/vite --config vite.https.config.mjs \
            >"$LOG_FILE" 2>&1 &
        echo $! >"$PID_FILE"
        echo "$PORT" >"$PORT_FILE"
    )

    local attempt
    for attempt in $(seq 1 30); do
        if curl -sk -o /dev/null "https://localhost:$PORT/"; then break; fi
        sleep 1
    done

    if ! curl -sk -o /dev/null "https://localhost:$PORT/"; then
        err "The instance did not answer on port $PORT. Log: $LOG_FILE"
        tail -20 "$LOG_FILE" 2>/dev/null || true
        return 1
    fi

    ok "Serving https://localhost:$PORT/"
    cat <<EOF

Next:
  1. open -a Safari 'https://localhost:$PORT/engineering'
  2. Safari -> File -> Add to Dock, then verify the app window (390 px wide)
  3. bash scripts/enable-engineering-https.sh stop   when finished

The page is HTTPS while the backend stays http://localhost:8484, so API-backed
state will show "Local backend unavailable". Layout and navigation remain valid.
EOF
}

stop_instance() {
    local pid
    pid="$(cat "$PID_FILE" 2>/dev/null || true)"
    if [[ -z "$pid" ]] || ! kill -0 "$pid" 2>/dev/null; then
        rm -f "$PID_FILE"
        local other
        other="$(port_pid || true)"
        if [[ -n "$other" ]]; then
            warn "Port $PORT is held by PID $other, which this script did not start; leaving it alone"
        else
            ok "No HTTPS instance running"
        fi
        return 0
    fi

    info "Stopping PID $pid"
    kill "$pid" 2>/dev/null || true
    local attempt
    for attempt in $(seq 1 10); do
        kill -0 "$pid" 2>/dev/null || break
        sleep 1
    done
    if kill -0 "$pid" 2>/dev/null; then
        warn "PID $pid did not exit; inspect it before forcing"
        return 1
    fi
    rm -f "$PID_FILE" "$PORT_FILE"
    ok "Stopped"
}

show_status() {
    info "Engineering HTTPS — status"
    if [[ -s "$CERT_FILE" ]]; then
        ok "Certificate: $CERT_FILE"
        warn "Expires: $(certificate_expiry || echo unknown)"
    else
        warn "Certificate: not issued yet ($STATE_DIR)"
    fi
    if ca_trusted; then ok "Local CA: trusted"; else warn "Local CA: not trusted"; fi

    # Report the port the running instance actually uses, not just this shell's default.
    local live_port
    live_port="$(cat "$PORT_FILE" 2>/dev/null || true)"
    live_port="${live_port:-$PORT}"

    local pid
    pid="$(lsof -nP -iTCP:"$live_port" -sTCP:LISTEN -t 2>/dev/null | head -1)"
    if [[ -n "$pid" ]]; then
        ok "Listener: port $live_port (PID $pid)"
        echo "    https://localhost:$live_port/engineering"
    else
        warn "Listener: port $live_port is closed"
    fi
    [[ -f "$LOG_FILE" ]] && info "Log: $LOG_FILE"
    [[ -d "$HOME/Applications/uCore.app" ]] && info "Installed app: ~/Applications/uCore.app"
    return 0
}

case "$ACTION" in
    start) start_instance ;;
    stop) stop_instance ;;
    status) show_status ;;
    --help|-h|help) usage ;;
    *) err "Unknown action: $ACTION"; usage; exit 2 ;;
esac

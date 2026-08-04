#!/bin/bash
# uCore Watchdog — health/self-heal loop for backend + orchestration services.
# Intended to run via launchd StartInterval.

set -euo pipefail

UCORE_ROOT="${UCORE_ROOT:-$HOME/Code/uCore}"
BACKEND_DIR="$UCORE_ROOT/backend"
ROOT_VENV_DIR="$UCORE_ROOT/.venv"
LOG_DIR="$HOME/.ucore/logs"
LOG_FILE="$LOG_DIR/ucore-watchdog.log"

mkdir -p "$LOG_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

check_backend() {
    curl -s --max-time 3 "http://127.0.0.1:8484/api/health" > /dev/null 2>&1
}

check_hivemind() {
    curl -s --max-time 2 "http://127.0.0.1:8490/health" > /dev/null 2>&1
}

launchd_menu_pid() {
    launchctl print "gui/$(id -u)/com.udos.ucore-menu" 2>/dev/null \
        | awk '/pid = / {print $3; exit}'
}

enforce_single_menu_instance() {
    local keep_pid
    keep_pid="$(launchd_menu_pid || true)"
    local pids
    pids="$(pgrep -f "app.menu.unified_menu|app.menu.unified_menu_simple" 2>/dev/null || true)"
    local count
    count="$(echo "$pids" | awk 'NF>0 {c++} END {print c+0}')"

    if [[ "$count" -le 1 ]]; then
        return
    fi

    if [[ -z "$keep_pid" ]]; then
        keep_pid="$(echo "$pids" | head -n 1)"
    fi

    while IFS= read -r pid; do
        [[ -z "$pid" ]] && continue
        if [[ "$pid" != "$keep_pid" ]]; then
            kill "$pid" 2>/dev/null || true
            log "Killed duplicate menu process PID=$pid (keeping PID=$keep_pid)"
        fi
    done <<< "$pids"
}

run_autonomy_health_action() {
    curl -s --max-time 6 \
        "http://127.0.0.1:8484/api/skills/autostart_health_check/run" \
        > /dev/null 2>&1 || true
}

attempt_control_recover() {
    curl -s --max-time 8 -X POST \
        "http://127.0.0.1:8484/api/control/recover" \
        -H "Content-Type: application/json" \
        -d '{"lane":"ecosystem"}' \
        > /dev/null 2>&1
}

pick_python_bin() {
    if [[ -x "$ROOT_VENV_DIR/bin/python" ]]; then
        echo "$ROOT_VENV_DIR/bin/python"
    elif [[ -x "$BACKEND_DIR/.venv/bin/python" ]]; then
        echo "$BACKEND_DIR/.venv/bin/python"
    else
        echo "/usr/bin/python3"
    fi
}

hard_restart_backend() {
    local pids
    pids="$(lsof -tiTCP:8484 -sTCP:LISTEN 2>/dev/null || true)"
    if [[ -n "$pids" ]]; then
        log "Forcing backend listener restart (PIDs: $pids)"
        # shellcheck disable=SC2086
        kill -9 $pids 2>/dev/null || true
    fi

    local python_bin
    python_bin="$(pick_python_bin)"

    log "Starting backend with $python_bin"
    (
        cd "$BACKEND_DIR"
        PYTHONPATH=. "$python_bin" -m app --port 8484 \
            >> "$LOG_DIR/ucore-server.log" \
            2>> "$LOG_DIR/ucore-server.log" &
    )
}

main() {
    log "Watchdog tick"

    # Enforce single menu process so only one popcorn icon is shown.
    enforce_single_menu_instance

    if ! check_backend; then
        log "Backend health failed; attempting control recovery"
        if ! attempt_control_recover; then
            log "Control recovery unavailable; running hard backend restart"
            hard_restart_backend
        fi

        if check_backend; then
            log "Backend recovered"
        else
            log "Backend still unhealthy after recovery attempts"
        fi
    fi

    if check_backend && ! check_hivemind; then
        log "Hivemind health failed; attempting control recovery"
        attempt_control_recover || true
    fi

    if check_backend; then
        log "Triggering autonomy health action"
        run_autonomy_health_action
    fi
}

main

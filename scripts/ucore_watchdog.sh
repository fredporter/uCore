#!/bin/bash
# uCore Watchdog — health loop for the backend and frontend.
# Intended to run via launchd StartInterval.

set -euo pipefail

UCORE_ROOT="${UCORE_ROOT:-$HOME/Code/uCore}"
BACKEND_DIR="$UCORE_ROOT/backend"
ROOT_VENV_DIR="$UCORE_ROOT/.venv"
LOG_DIR="$HOME/.ucore/logs"
LOG_FILE="$LOG_DIR/ucore-watchdog.log"
CIRCUIT_BREAKER_FILE="/tmp/ucore-watchdog-restarts"
LAST_RESTART_FILE="/tmp/ucore-watchdog-last-restart"
CIRCUIT_BREAKER_MAX=5         # max restarts in window
CIRCUIT_BREAKER_WINDOW=600    # 10 minutes in seconds
GRACE_PERIOD=15               # seconds to wait after restart before checking

mkdir -p "$LOG_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

check_backend() {
    curl -s --max-time 3 "http://127.0.0.1:8484/api/health" > /dev/null 2>&1
}

check_vite() {
    curl -s --max-time 3 "http://127.0.0.1:5175" > /dev/null 2>&1
}

restart_vite() {
    log "Restarting Vite frontend..."
    lsof -tiTCP:5175 -sTCP:LISTEN | xargs kill -9 2>/dev/null || true
    sleep 1
    cd "$UCORE_ROOT/frontend-vue"
    nohup pnpm dev >> "$LOG_DIR/vite.log" 2>&1 &
    date +%s > /tmp/ucore-vite-last-restart
    log "Vite restarted"
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
        "http://127.0.0.1:8484/api/health" \
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

# ─── Circuit breaker ───────────────────────────────────────────

check_circuit_breaker() {
    local now
    now="$(date +%s)"

    if [[ ! -f "$CIRCUIT_BREAKER_FILE" ]]; then
        return 0  # no history, ok to restart
    fi

    # Count restarts within the window
    local count=0
    while IFS= read -r ts; do
        [[ -z "$ts" ]] && continue
        if (( now - ts < CIRCUIT_BREAKER_WINDOW )); then
            ((count++))
        fi
    done < "$CIRCUIT_BREAKER_FILE"

    if (( count >= CIRCUIT_BREAKER_MAX )); then
        log "CIRCUIT BREAKER TRIPPED: $count restarts in ${CIRCUIT_BREAKER_WINDOW}s — refusing to restart"
        return 1
    fi
    return 0
}

record_restart() {
    date +%s >> "$CIRCUIT_BREAKER_FILE"
    # Prune entries older than the window
    local now cutoff
    now="$(date +%s)"
    cutoff=$(( now - CIRCUIT_BREAKER_WINDOW ))
    local tmpfile="${CIRCUIT_BREAKER_FILE}.tmp"
    while IFS= read -r ts; do
        [[ -z "$ts" ]] && continue
        if (( ts >= cutoff )); then
            echo "$ts" >> "$tmpfile"
        fi
    done < "$CIRCUIT_BREAKER_FILE"
    mv "$tmpfile" "$CIRCUIT_BREAKER_FILE"
}

# ─── Startup grace period ──────────────────────────────────────

in_grace_period() {
    if [[ ! -f "$LAST_RESTART_FILE" ]]; then
        return 1  # no recent restart
    fi
    local last now elapsed
    last="$(cat "$LAST_RESTART_FILE")"
    now="$(date +%s)"
    elapsed=$(( now - last ))
    if (( elapsed < GRACE_PERIOD )); then
        log "Grace period: $elapsed/${GRACE_PERIOD}s since last restart — skipping health check"
        return 0
    fi
    return 1
}

# ─── Hard restart with graceful shutdown ───────────────────────

hard_restart_backend() {
    # Try graceful shutdown first
    log "Attempting graceful shutdown before hard restart..."
    curl -s --max-time 3 -X POST \
        "http://127.0.0.1:8484/api/shutdown" \
        -H "Content-Type: application/json" \
        -d '{"confirm":true}' \
        > /dev/null 2>&1 || true
    sleep 2

    # Force-kill any remaining listeners
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

    # Record restart timestamp for grace period
    date +%s > "$LAST_RESTART_FILE"
}

main() {
    log "Watchdog tick"

    # Enforce single menu process so only one popcorn icon is shown.
    enforce_single_menu_instance

    # Skip health checks if we're in the startup grace period.
    if in_grace_period; then
        return
    fi

    if ! check_backend; then
        log "Backend health failed; attempting control recovery"

        # Circuit breaker: don't restart if we've already restarted too many times.
        if ! check_circuit_breaker; then
            log "Circuit breaker active — skipping restart. Check logs at $LOG_DIR/ucore-server.log"
            return
        fi

        if ! attempt_control_recover; then
            log "Control recovery unavailable; running hard backend restart"
            record_restart
            hard_restart_backend
        fi

        if check_backend; then
            log "Backend recovered"
        else
            log "Backend still unhealthy after recovery attempts"
        fi
    fi

    if check_backend; then
        log "Triggering autonomy health action"
        run_autonomy_health_action
    fi

    # ── Vite frontend health ──────────────────────────────────
    if ! check_vite; then
        log "Vite frontend health failed; restarting..."
        restart_vite
        if check_vite; then
            log "Vite frontend recovered"
        else
            log "Vite frontend still unhealthy after restart"
        fi
    fi
}

main

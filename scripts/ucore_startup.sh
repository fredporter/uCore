#!/bin/bash
# uCore Startup Script — Self-healing auto-start for snackbar services
# This script ensures all uCore services are running at login

set -e

UCORE_ROOT="${UCORE_ROOT:-$HOME/Code/uCore}"
BACKEND_DIR="$UCORE_ROOT/backend"
ROOT_VENV_DIR="$UCORE_ROOT/.venv"
LOG_DIR="$HOME/.ucore/logs"
PID_DIR="$HOME/.ucore"

# Ensure directories exist
mkdir -p "$LOG_DIR"
mkdir -p "$PID_DIR"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_DIR/ucore-startup.log"
}

log "🚀 Starting uCore services..."

# Check if backend is running
check_backend() {
    curl -s --max-time 2 "http://localhost:8484/api/health" > /dev/null 2>&1
}

# Check if menu is running
check_menu() {
    pgrep -f "app.menu.unified_menu_simple|app.menu.unified_menu" > /dev/null 2>&1
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
            log "🧹 Killed duplicate menu process PID=$pid (keeping PID=$keep_pid)"
        fi
    done <<< "$pids"
}

# Start backend if not running
if ! check_backend; then
    log "🔧 Starting snackbar backend..."
    if [ -f "$ROOT_VENV_DIR/bin/python" ]; then
        PYTHON_BIN="$ROOT_VENV_DIR/bin/python"
    elif [ -f "$BACKEND_DIR/.venv/bin/python" ]; then
        PYTHON_BIN="$BACKEND_DIR/.venv/bin/python"
    else
        PYTHON_BIN="/usr/bin/python3"
    fi
    
    cd "$BACKEND_DIR" && PYTHONPATH=. $PYTHON_BIN -m app --port 8484 > "$LOG_DIR/ucore-server.log" 2>&1 &
    sleep 3
    
    if check_backend; then
        log "✅ Backend started successfully"
    else
        log "❌ Backend failed to start"
    fi
fi

# Start menu if not running
if ! check_menu; then
    log "🔧 Starting uCore menu..."
    if launchctl print "gui/$(id -u)/com.udos.ucore-menu" >/dev/null 2>&1; then
        launchctl kickstart "gui/$(id -u)/com.udos.ucore-menu" >/dev/null 2>&1 || true
    elif [ -f "$ROOT_VENV_DIR/bin/python" ]; then
        PYTHON_BIN="$ROOT_VENV_DIR/bin/python"
        cd "$BACKEND_DIR" && PYTHONPATH=. $PYTHON_BIN -m app.menu.unified_menu_simple > "$LOG_DIR/ucore-menu.log" 2>&1 &
    elif [ -f "$BACKEND_DIR/.venv/bin/python" ]; then
        PYTHON_BIN="$BACKEND_DIR/.venv/bin/python"
        cd "$BACKEND_DIR" && PYTHONPATH=. $PYTHON_BIN -m app.menu.unified_menu_simple > "$LOG_DIR/ucore-menu.log" 2>&1 &
    else
        PYTHON_BIN="/usr/bin/python3"
        cd "$BACKEND_DIR" && PYTHONPATH=. $PYTHON_BIN -m app.menu.unified_menu_simple > "$LOG_DIR/ucore-menu.log" 2>&1 &
    fi

    sleep 2
    
    if check_menu; then
        log "✅ Menu started successfully"
    else
        log "❌ Menu failed to start"
    fi
fi

# Ensure only one menu process remains (single popcorn icon)
enforce_single_menu_instance

# Probe the canonical backend health endpoint
log "🏥 Running health check..."
if check_backend; then
    curl -s --max-time 5 "http://localhost:8484/api/health" > /dev/null 2>&1 || true
fi

log "✅ uCore startup complete"

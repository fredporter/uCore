#!/usr/bin/env bash
set -euo pipefail

# Local smoke for SnackMachine + uCore wiring.
# Verifies:
# 1) SnackMachine capability handshake is available.
# 2) One snack can be queued through uCore API.
# 3) Popcorn/menu status is healthy.
# 4) Frontend launch targets for SnackMachine and Clipboard pages are reachable.

UCORE_URL="${UCORE_URL:-http://127.0.0.1:8484}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:5175}"
SNACKMACHINE_PATH="${UCORE_SNACKMACHINE_PATH:-$HOME/Code/SnackMachine}"

if [[ ! -d "$SNACKMACHINE_PATH" ]]; then
  echo "[FAIL] SnackMachine path not found: $SNACKMACHINE_PATH"
  exit 1
fi

echo "[1/4] Validate SnackMachine capability payload"
CAP_JSON="$(PYTHONPATH="$SNACKMACHINE_PATH/src" python3 -m snackmachine_ext.cli capabilities)"
python3 - "$CAP_JSON" <<'PY'
import json
import sys

payload = json.loads(sys.argv[1])
required = {
    "snacks.catalog",
    "snacks.packages.install",
    "snacks.packages.uninstall",
    "snacks.packages.list",
}
missing = sorted(required - set(payload.get("provides", [])))
if payload.get("id") != "snackmachine-extension":
    raise SystemExit("[FAIL] capability id mismatch")
if missing:
    raise SystemExit(f"[FAIL] missing required capabilities: {missing}")
print("[OK] Capability payload is compatible")
PY

echo "[2/4] Queue one smoke snack"
SMOKE_RESPONSE="$(curl -fsS -X POST "$UCORE_URL/api/snacks" \
  -H 'Content-Type: application/json' \
  -d '{"type":"message","priority":"normal","source":"snackmachine-smoke","content":{"title":"Smoke","text":"SnackMachine smoke queue"}}')"
python3 - "$SMOKE_RESPONSE" <<'PY'
import json
import sys

payload = json.loads(sys.argv[1])
if not payload.get("id"):
    raise SystemExit("[FAIL] snack queue response missing id")
if payload.get("source") != "snackmachine-smoke":
    raise SystemExit("[FAIL] snack queue source mismatch")
print(f"[OK] Queued snack id={payload['id']}")
PY

echo "[3/4] Verify popcorn menu status"
STATUS_JSON="$(curl -fsS "$UCORE_URL/api/surfaces/popcorn/status")"
python3 - "$STATUS_JSON" <<'PY'
import json
import sys

payload = json.loads(sys.argv[1])
menu_running = bool(payload.get("menu", {}).get("running"))
backend_running = bool(payload.get("backend", {}).get("running"))
if not menu_running or not backend_running:
    raise SystemExit(
        f"[FAIL] unhealthy status: menu.running={menu_running}, backend.running={backend_running}"
    )
print("[OK] Popcorn status healthy")
PY

echo "[4/4] Verify launch/open targets"
curl -fsS "$FRONTEND_URL/server?tab=snacks" >/dev/null
curl -fsS "$FRONTEND_URL/system/s310" >/dev/null

ROUTER_FILE="frontend-vue/src/router/index.ts"
MENU_FILE="backend/app/menu/unified_menu_simple.py"

if ! grep -q "path: '/snackmachine/:pathMatch(.*)*'" "$ROUTER_FILE"; then
  echo "[FAIL] Missing /snackmachine route in $ROUTER_FILE"
  exit 1
fi
if ! grep -q "return '/server?tab=snacks'" "$ROUTER_FILE"; then
  echo "[FAIL] /snackmachine redirect target mismatch in $ROUTER_FILE"
  exit 1
fi
if ! grep -q '"snackmachine-extension": "http://localhost:5175/server?tab=snacks"' "$MENU_FILE"; then
  echo "[FAIL] SnackMachine menu link mismatch in $MENU_FILE"
  exit 1
fi

echo "[OK] Launch/open targets verified"
echo "SnackMachine integration smoke passed"

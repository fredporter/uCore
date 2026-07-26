#!/bin/bash
# Setup overnight autonomy engine as a launchd job
# Runs every 6 hours to ensure 4x daily health checks
set -e

PLIST="$HOME/Library/LaunchAgents/com.udos.ucore-autonomy.plist"
REPO="$HOME/Code/uCore"

cat > "$PLIST" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.udos.ucore-autonomy</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>${REPO}/backend/health/autonomy_engine.py</string>
        <string>--once</string>
    </array>
    <key>WorkingDirectory</key>
    <string>${REPO}</string>
    <key>StartInterval</key>
    <integer>21600</integer>
    <key>StandardOutPath</key>
    <string>${HOME}/.ucore/logs/autonomy_launchd.log</string>
    <key>StandardErrorPath</key>
    <string>${HOME}/.ucore/logs/autonomy_launchd_err.log</string>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
PLIST

launchctl unload "$PLIST" 2>/dev/null || true
launchctl load "$PLIST"

echo "Autonomy engine installed — runs every 6 hours"
echo "State file: ~/.ucore/logs/autonomy_state.json"
echo "API endpoint: GET /api/autonomy/state"
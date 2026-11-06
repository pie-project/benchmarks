#!/usr/bin/env bash
# Runs the phone ingest on this Mac (a site laptop) as a launchd agent, listening on its Tailscale address only.
#
#   mobile/ingest/install-launchd.sh            # install or restart
#   mobile/ingest/install-launchd.sh --remove
#
# The token is made once in ~/.config/pie-evals/phone-ingest.token (mode 600; never committed). Phones send to
# http://<this Mac's Tailscale IP>:8787/v1/results with that token; rows wait in ~/.pie-evals/phone-inbox until the pages
# build (which holds PIE_EVALS_DB) stores them, so this service never holds the database URL.
set -euo pipefail
repo="$(cd "$(dirname "$0")/../.." && pwd)"
label=ai.liszt.pie-evals.phone-ingest
plist="$HOME/Library/LaunchAgents/$label.plist"
ts=/Applications/Tailscale.app/Contents/MacOS/Tailscale
command -v tailscale >/dev/null && ts=tailscale
launchctl bootout "gui/$(id -u)/$label" 2>/dev/null || true
if [ "${1:-}" = --remove ]; then rm -f "$plist"; echo "removed $label"; exit 0; fi
ip="$("$ts" ip -4 | head -1)"
[ -n "$ip" ] || { echo "no Tailscale IPv4 address: is Tailscale up?" >&2; exit 1; }
port="${PHONE_INGEST_PORT:-8787}"
token="$HOME/.config/pie-evals/phone-ingest.token"
"$repo/.venv/bin/pie-evals" --matrix "$repo/matrix" phone-ingest --help >/dev/null
mkdir -p "$HOME/.pie-evals/phone-inbox" "$HOME/Library/Logs"
cat > "$plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>$label</string>
  <key>WorkingDirectory</key><string>$repo</string>
  <key>ProgramArguments</key><array>
    <string>$repo/.venv/bin/pie-evals</string><string>--matrix</string><string>$repo/matrix</string>
    <string>phone-ingest</string><string>--listen</string><string>$ip:$port</string>
    <string>--token-file</string><string>$token</string><string>--init-token</string>
    <string>--spool</string><string>$HOME/.pie-evals/phone-inbox</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>ThrottleInterval</key><integer>30</integer>
  <key>StandardErrorPath</key><string>$HOME/Library/Logs/pie-evals-phone-ingest.log</string>
  <key>StandardOutPath</key><string>$HOME/Library/Logs/pie-evals-phone-ingest.log</string>
</dict></plist>
PLIST
launchctl bootstrap "gui/$(id -u)" "$plist"
for _ in $(seq 20); do curl -sf "http://$ip:$port/v1/health" >/dev/null && break; sleep 0.5; done
curl -sf "http://$ip:$port/v1/health" && echo
echo "phone ingest: http://$ip:$port  (token: $token)"

#!/bin/bash
# Stop this Mac's pie-evals runner and unregister it. Run it on the Mac:
#   bash uninstall.sh <remove-token>     (fleet.sh uninstall <id> does this over ssh)
# Keeps ~/workspace/pie-evals/pie and ~/workspace/pie-evals/cache; pass --all to delete ~/workspace/pie-evals entirely.
set -euo pipefail
TOKEN="${1:?usage: uninstall.sh <remove-token> [--all]}"
HOME_DIR="${PIE_EVALS_HOME:-$HOME/workspace/pie-evals}"
PLIST=/Library/LaunchDaemons/com.pie-project.pie-evals-runner.plist
ok() { printf '  \033[32m✓\033[0m %s\n' "$1"; }

if [ -f "$PLIST" ]; then sudo launchctl bootout system "$PLIST" 2>/dev/null || true; sudo rm -f "$PLIST"; fi
ok "service stopped"
if [ -f "$HOME_DIR/runner/.runner" ]; then (cd "$HOME_DIR/runner" && ./config.sh remove --token "$TOKEN" >/dev/null); fi
ok "runner unregistered"
rm -rf "$HOME_DIR/runner" "$HOME_DIR/logs"
[ "${2:-}" = --all ] && rm -rf "$HOME_DIR" && ok "removed $HOME_DIR" || ok "removed runner; kept $HOME_DIR/pie and $HOME_DIR/cache"

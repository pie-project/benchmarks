#!/bin/bash
# Turn this Mac into a pie-evals runner. Run it on the Mac (fleet.sh does this over ssh):
#   bash install.sh <registration-token>
# Everything lands in ~/workspace/pie-evals; the runner is a system service that starts at boot.
set -euo pipefail
TOKEN="${1:?usage: install.sh <registration-token>}"
REPO="${REPO:-pie-project/pie-evals}"
RUNNER_VERSION="${RUNNER_VERSION:-2.338.0}"
HOME_DIR="${PIE_EVALS_HOME:-$HOME/workspace/pie-evals}"
RUNNER="$HOME_DIR/runner" PIE="$HOME_DIR/pie" CACHE="$HOME_DIR/cache" LOGS="$HOME_DIR/logs"
SERVICE=com.pie-project.pie-evals-runner
PLIST=/Library/LaunchDaemons/$SERVICE.plist
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:/opt/homebrew/bin:$PATH"

step() { printf '\n\033[1m[%s/6] %s\033[0m\n' "$1" "$2"; }
ok() { printf '  \033[32m✓\033[0m %s\n' "$1"; }
warn() { printf '  \033[33m!\033[0m %s\n' "$1"; }
die() { printf '  \033[31m✗\033[0m %s\n' "$1"; exit 1; }

[ "$(uname -s)" = Darwin ] && [ "$(uname -m)" = arm64 ] || die "This script sets up Apple Silicon Macs only."

step 1 "Identifying this Mac"
CHIP=$(sysctl -n machdep.cpu.brand_string)
GIB=$(( $(sysctl -n hw.memsize) / 1073741824 ))
BASE=$(echo "$CHIP" | sed -E 's/^Apple //' | tr '[:upper:]' '[:lower:]' | tr ' ' '-')
if [ -n "${PLATFORM_ID:-}" ]; then :
elif [ "$BASE" = m2-max ]; then PLATFORM_ID=m2-max
else PLATFORM_ID="$BASE-${GIB}g"; fi
ok "$CHIP, ${GIB} GB, macOS $(sw_vers -productVersion) -> platform $PLATFORM_ID"
pmset -g batt | grep -q "AC Power" && ok "on AC power" || warn "on battery: runs on battery are recorded as noisy"

step 2 "Installing tools"
xcode-select -p >/dev/null 2>&1 || die "Command Line Tools missing: sudo softwareupdate -i \"Command Line Tools for Xcode <ver>\" (see infra/mac/README.md)"
ok "Command Line Tools"
command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh >/dev/null 2>&1
command -v uv >/dev/null && ok "uv" || die "uv failed to install"
command -v rustup >/dev/null || curl -sSf https://sh.rustup.rs | sh -s -- -y --no-modify-path >/dev/null 2>&1
rustup target add wasm32-wasip2 >/dev/null 2>&1 && ok "rust + wasm32-wasip2" || die "rust failed to install"

step 3 "Laying out $HOME_DIR"
[ -d "$HOME/pie-evals/runner" ] && [ ! -e "$HOME_DIR" ] && { mkdir -p "$(dirname "$HOME_DIR")"; mv "$HOME/pie-evals" "$HOME_DIR"; }
mkdir -p "$RUNNER" "$CACHE" "$LOGS"
# move an older install (~/actions-runner, ~/pie, ~/.cache/pie-evals) into the folder
for svc in "$HOME"/Library/LaunchAgents/actions.runner.pie-project-pie-evals.*.plist; do
  [ -f "$svc" ] && { launchctl bootout "gui/$(id -u)" "$svc" 2>/dev/null || true; rm -f "$svc"; ok "removed old login service $(basename "$svc")"; }
done
[ -f /Library/LaunchDaemons/pie-evals-runner.plist ] && { sudo launchctl bootout system /Library/LaunchDaemons/pie-evals-runner.plist 2>/dev/null || true; sudo rm -f /Library/LaunchDaemons/pie-evals-runner.plist; ok "removed old system service"; }
[ -d "$HOME/actions-runner" ] && grep -qs "$REPO" "$HOME/actions-runner/.runner" 2>/dev/null && { rm -rf "$HOME/actions-runner"; ok "removed old ~/actions-runner"; }
[ -d "$HOME/actions-runner" ] && [ ! -f "$HOME/actions-runner/.runner" ] && [ ! -f "$HOME/actions-runner/config.sh" ] && rm -rf "$HOME/actions-runner"
[ -d "$HOME/pie/.git" ] && [ ! -e "$PIE" ] && { mv "$HOME/pie" "$PIE"; ok "moved ~/pie -> $PIE"; }
[ -d "$HOME/.cache/pie-evals" ] && [ -z "$(ls -A "$CACHE")" ] && { rmdir "$CACHE"; mv "$HOME/.cache/pie-evals" "$CACHE"; ok "moved ~/.cache/pie-evals -> $CACHE"; }
rm -f "$HOME/setup-runner.sh" "$HOME/remote-setup.sh"
[ -d "$PIE/.git" ] || git clone -q https://github.com/pie-project/pie "$PIE"
ok "pie checkout at $PIE"

step 4 "Fetching runner $RUNNER_VERSION"
cd "$RUNNER"
have=$(./config.sh --version 2>/dev/null || true)
if [ "$have" != "$RUNNER_VERSION" ]; then
  find . -mindepth 1 -maxdepth 1 ! -name _work -exec rm -rf {} +
  curl -fsSL "https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-osx-arm64-${RUNNER_VERSION}.tar.gz" | tar xz
fi
ok "runner $RUNNER_VERSION in $RUNNER"

step 5 "Registering with github.com/$REPO"
NAME="$(scutil --get ComputerName | tr -cd '[:alnum:] -' | tr ' ' '-')-$PLATFORM_ID"
# re-running replaces the registration by name: drop the local one first
rm -f .runner .credentials .credentials_rsaparams
./config.sh --unattended --url "https://github.com/$REPO" --token "$TOKEN" --name "$NAME" \
  --labels "self-hosted,macos,$PLATFORM_ID" --work _work --replace >/dev/null
SDK=$(readlink -f /Library/Developer/CommandLineTools/SDKs/MacOSX.sdk 2>/dev/null || xcrun --show-sdk-path)
# jobs read these: the workflows default PIE_ROOT / PIE_EVALS_CACHE to these values when set
printf 'SDKROOT=%s\nPIE_ROOT=%s\nPIE_EVALS_CACHE=%s\nLANG=en_US.UTF-8\n' "$SDK" "$PIE" "$CACHE" > .env
echo "$PATH" > .path
ok "registered as $NAME (labels self-hosted,macos,$PLATFORM_ID)"

step 6 "Starting the system service (asks for your password)"
cat > "$LOGS/$SERVICE.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>$SERVICE</string>
  <key>UserName</key><string>$(id -un)</string>
  <key>WorkingDirectory</key><string>$RUNNER</string>
  <key>ProgramArguments</key><array><string>$RUNNER/run.sh</string></array>
  <key>EnvironmentVariables</key><dict><key>HOME</key><string>$HOME</string></dict>
  <key>RunAtLoad</key><true/><key>KeepAlive</key><true/>
  <key>ProcessType</key><string>Interactive</string>
  <key>StandardOutPath</key><string>$LOGS/runner.log</string>
  <key>StandardErrorPath</key><string>$LOGS/runner.log</string>
</dict></plist>
EOF
sudo launchctl bootout system "$PLIST" 2>/dev/null || true
sudo install -m 0644 -o root -g wheel "$LOGS/$SERVICE.plist" "$PLIST" && rm "$LOGS/$SERVICE.plist"
sudo launchctl bootstrap system "$PLIST"
# a runner Mac must never sleep; it restarts itself after a power cut
sudo pmset -a sleep 0 disksleep 0 womp 1 autorestart 1 >/dev/null
sleep 5
pgrep -qf "$RUNNER/bin/Runner.Listener" && ok "service running; starts at boot, no login needed" || warn "service not up yet: tail $LOGS/runner.log"
printf '\n\033[32mDone.\033[0m %s is a runner. Logs: %s/runner.log\n' "$PLATFORM_ID" "$LOGS"

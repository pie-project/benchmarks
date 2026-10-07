#!/bin/bash
# Manage the resident Macs from your laptop (needs gh with admin on the repo, and tailscale).
#   infra/mac/fleet.sh status               runner state on GitHub + ssh reachability
#   infra/mac/fleet.sh keys                 copy your ssh key to every Mac (one password each, once)
#   infra/mac/fleet.sh install <id..|all>   install or update the runner (asks for the Mac's password for sudo)
#   infra/mac/fleet.sh uninstall <id>       stop and unregister one Mac
#   infra/mac/fleet.sh ssh <id> | logs <id>
set -euo pipefail
cd "$(dirname "$0")"
REPO="${REPO:-pie-project/pie-evals}"

# "id host user" per Mac, and the reserved hosts, from fleet.yaml
macs() { awk '/^reserved:/{r=1} r{next} /- id:/{id=$3} /host:/{h=$2} /user:/{print id, h, $2}' fleet.yaml; }
reserved() { awk '/^reserved:/{r=1} r && /host:/{print $3}' fleet.yaml; }
lookup() { macs | awk -v id="$1" '$1==id' | grep . || { echo "unknown mac: $1 (see fleet.yaml)" >&2; exit 1; }; }
targets() { if [ "${1:-}" = all ]; then macs; else for id in "$@"; do lookup "$id"; done; fi; }
guard() { if reserved | grep -qx "$1"; then echo "$1 is reserved; refusing" >&2; exit 1; fi; }
runners() { gh api "repos/$REPO/actions/runners?per_page=100" --jq '.runners[] | [.id, .name, .status, (if .busy then "busy" else "idle" end), ([.labels[].name] | map(select(test("^m[0-9]"))) | join(","))] | @tsv'; }

case "${1:-status}" in
  status)
    gh_rows=$(runners)
    printf '%-13s %-30s %-5s %-8s %s\n' MAC HOST SSH RUNNER STATE
    macs | while read -r id host _; do
      nc -z -G 3 "$host" 22 2>/dev/null && s=up || s=down
      row=$(awk -F'\t' -v id="$id" '$5==id' <<<"$gh_rows" | head -1)
      printf '%-13s %-30s %-5s %-8s %s\n' "$id" "$host" "$s" "$(cut -f3 <<<"$row" | grep . || echo none)" "$(cut -f4 <<<"$row")"
    done ;;
  keys)
    [ -f ~/.ssh/id_ed25519.pub ] || ssh-keygen -t ed25519 -N "" -f ~/.ssh/id_ed25519
    macs | while read -r id host user; do guard "$host"; echo "== $id"; ssh-copy-id -o StrictHostKeyChecking=accept-new "$user@$host" </dev/tty; done ;;
  install)
    shift; [ $# -gt 0 ] || { echo "usage: fleet.sh install <id..|all>"; exit 1; }
    token=$(gh api -X POST "repos/$REPO/actions/runners/registration-token" --jq .token)
    targets "$@" | while read -r id host user; do
      guard "$host"; echo; echo "================ $id ($host)"
      ssh "$user@$host" 'mkdir -p ~/workspace/pie-evals' </dev/null
      scp -q install.sh "$user@$host:workspace/pie-evals/install.sh"
      ssh -t "$user@$host" "bash ~/workspace/pie-evals/install.sh $token" </dev/tty || { echo "!! $id failed"; continue; }
      # an earlier registration under another name stays behind offline: drop it
      runners | awk -F'\t' -v id="$id" '$5==id && $3=="offline" {print $1}' | while read -r rid; do gh api -X DELETE "repos/$REPO/actions/runners/$rid"; done
    done
    "$0" status ;;
  uninstall)
    read -r id host user < <(lookup "${2:?usage: fleet.sh uninstall <id>}"); guard "$host"
    token=$(gh api -X POST "repos/$REPO/actions/runners/remove-token" --jq .token)
    scp -q uninstall.sh "$user@$host:workspace/pie-evals/uninstall.sh"
    ssh -t "$user@$host" "bash ~/workspace/pie-evals/uninstall.sh $token" ;;
  ssh)  read -r id host user < <(lookup "${2:?id}"); guard "$host"; exec ssh "$user@$host" ;;
  logs) read -r id host user < <(lookup "${2:?id}"); guard "$host"; exec ssh "$user@$host" 'tail -f ~/workspace/pie-evals/logs/runner.log' ;;
  *) sed -n '2,8p' "$0"; exit 1 ;;
esac

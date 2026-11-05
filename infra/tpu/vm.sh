#!/usr/bin/env bash
# The TPU VM of one tpu.yml run, whichever API serves its generation: the Cloud TPU API (tpu-vm) for
# v4/v5e/v5p/v6e, Compute Engine (an instance with attached TPUs) for TPU7x, which the TPU API does not serve.
#
#   vm.sh resolve <platform>        print the platform's tpu settings as KEY=value lines (for $GITHUB_ENV)
#   vm.sh create                    try each zone of TPU_ZONES, on demand then spot; print zone=<zone>
#   vm.sh wait                      until the VM is up
#   vm.sh state                     the VM's state (READY/RUNNING when up)
#   vm.sh ssh <command>             run a command on the VM
#   vm.sh put <local>...            copy files to the VM's home
#   vm.sh get [--recurse] <remote> <local>
#   vm.sh delete                    delete the VM in every zone of TPU_ZONES it exists in
#
# Environment: GCP_PROJECT, TPU_NAME, TPU_KIND (tpu|compute), TPU_ZONES (space separated), TPU_ZONE (after create),
# TPU_TYPE + TPU_RUNTIME (tpu), TPU_MACHINE_TYPE + TPU_IMAGE (compute: a regex over the accelerator image families),
# TPU_DATA_DISK_GB (optional: a disk of that size, <name>-data, for ~/.cache where the checkpoints and imports land;
# a TPU VM's boot disk is 100 GB, too small for gpt-oss-120b's download beside its import).
set -euo pipefail
cmd=$1; shift
P=(--project "$GCP_PROJECT")
SSH=(--strict-host-key-checking=no --quiet)

case "$cmd" in
  resolve)
    python3 - "$1" <<'EOF'
import sys, yaml
p = {x["id"]: x for x in yaml.safe_load(open("matrix/platforms.yaml"))["platforms"]}[sys.argv[1]]
t = p.get("tpu") or sys.exit(f"{sys.argv[1]} has no tpu: settings")
print("TPU_KIND=" + ("compute" if t.get("machine_type") else "tpu"))
for k in ("type", "runtime", "machine_type", "image", "data_disk_gb", "all_chips"):
    print(f"TPU_{k.upper()}={t.get(k, '')}")
print("TPU_ZONES=" + " ".join(t["zones"]))
EOF
    ;;
  create)
    image=()
    if [ "$TPU_KIND" = compute ]; then
      fams=$(gcloud compute images list --project ubuntu-os-accelerator-images --format 'value(family)' | sort -u)
      fam=$(echo "$fams" | grep -E "$TPU_IMAGE" | sort | tail -n 1 || true)
      [ -n "$fam" ] || { echo "::error::no ubuntu-os-accelerator-images family matches $TPU_IMAGE:" >&2; echo "$fams" >&2; exit 1; }
      echo "image family $fam" >&2
      image=(--image-family "$fam" --image-project ubuntu-os-accelerator-images)
    fi
    errs=""
    # TPU_ON_DEMAND=1: never a spot VM (a v6e spot VM was taken back within 20 min in 6 of 8 runs, 2026-11-04); the zones
    # are tried again on demand until a VM comes or two hours pass; TPU_ON_DEMAND=retry: on demand then spot, retried alike
    # (v5p-8: no on-demand permission, its spot zones often full)
    modes=("" spot); [ "${TPU_ON_DEMAND:-}" = 1 ] && modes=("")
    wait_s=0; [ -n "${TPU_ON_DEMAND:-}" ] && wait_s=7200; until_t=$(( $(date +%s) + wait_s ))
    while :; do
    for zone in $TPU_ZONES; do
      for spot in "${modes[@]}"; do
        echo "trying $zone ${spot:-on-demand}" >&2
        if [ "$TPU_KIND" = tpu ]; then
          disk=()
          if [ -n "${TPU_DATA_DISK_GB:-}" ]; then
            # the project's SSD and hyperdisk quotas are 500 GB a region: a standard disk when those are spent
            for t in pd-balanced hyperdisk-balanced pd-standard; do
              gcloud compute disks describe "$TPU_NAME-data" "${P[@]}" --zone "$zone" >/dev/null 2>&1 && break
              gcloud compute disks create "$TPU_NAME-data" "${P[@]}" --zone "$zone" --size "${TPU_DATA_DISK_GB}GB" --type "$t" \
                --labels "owner=pie-evals" --quiet >&2 && break
            done
            if gcloud compute disks describe "$TPU_NAME-data" "${P[@]}" --zone "$zone" >/dev/null 2>&1; then
              disk=(--data-disk "source=projects/$GCP_PROJECT/zones/$zone/disks/$TPU_NAME-data,mode=read-write")
            else
              echo "::warning::no data disk in $zone: the boot disk only" >&2
            fi
          fi
          out=$(gcloud compute tpus tpu-vm create "$TPU_NAME" "${P[@]}" --zone "$zone" --accelerator-type "$TPU_TYPE" \
                  --version "$TPU_RUNTIME" ${disk[@]+"${disk[@]}"} ${spot:+--spot} --labels "owner=pie-evals" --quiet 2>&1) && { echo "zone=$zone"; exit 0; }
        else
          out=$(gcloud compute instances create "$TPU_NAME" "${P[@]}" --zone "$zone" --machine-type "$TPU_MACHINE_TYPE" \
                  ${image[@]+"${image[@]}"} --boot-disk-size "${TPU_DATA_DISK_GB:-200}GB" --maintenance-policy TERMINATE \
                  ${spot:+--provisioning-model SPOT --instance-termination-action DELETE} --labels "owner=pie-evals" --quiet 2>&1) \
            && { echo "zone=$zone"; exit 0; }
        fi
        echo "$out" >&2
        errs+="$zone ${spot:-on-demand}: $(echo "$out" | grep -m1 -iE 'quota|capacity|denied|LOCATION_POLICY|not (found|supported)|unavailable' || echo "$out" | grep -m1 ERROR || echo "$out" | tail -n 1)"$'\n'
        # a VM half-created by a failed call must not linger
        TPU_ZONES=$zone bash "$0" delete >/dev/null 2>&1 || true
      done
    done
    [ "$(date +%s)" -lt "$until_t" ] || break
    echo "no zone had an on-demand VM: trying again in 5 minutes" >&2; errs=""; sleep 300
    done
    echo "::error::no zone gave a $TPU_NAME VM:"$'\n'"$errs" >&2
    echo "$errs" >> "${GITHUB_STEP_SUMMARY:-/dev/null}"
    exit 1
    ;;
  wait)
    for _ in $(seq 1 60); do
      if [ "$TPU_KIND" = tpu ]; then
        s=$(gcloud compute tpus tpu-vm describe "$TPU_NAME" "${P[@]}" --zone "$TPU_ZONE" --format 'value(state)'); want=READY
      else
        s=$(gcloud compute instances describe "$TPU_NAME" "${P[@]}" --zone "$TPU_ZONE" --format 'value(status)'); want=RUNNING
      fi
      echo "state: $s"; [ "$s" = "$want" ] && exit 0; sleep 10
    done
    echo "::error::the VM is not up after 10 minutes"; exit 1
    ;;
  state)  # READY / RUNNING when up; PREEMPTED, TERMINATED, ... when a spot VM was taken back
    if [ "$TPU_KIND" = tpu ]; then
      gcloud compute tpus tpu-vm describe "$TPU_NAME" "${P[@]}" --zone "$TPU_ZONE" --format 'value(state)'
    else
      gcloud compute instances describe "$TPU_NAME" "${P[@]}" --zone "$TPU_ZONE" --format 'value(status)'
    fi
    ;;
  ssh)
    if [ "$TPU_KIND" = tpu ]; then
      gcloud compute tpus tpu-vm ssh "$TPU_NAME" "${P[@]}" --zone "$TPU_ZONE" "${SSH[@]}" --command "$1"
    else
      gcloud compute ssh "$TPU_NAME" "${P[@]}" --zone "$TPU_ZONE" "${SSH[@]}" --command "$1"
    fi
    ;;
  put|get)
    if [ "$cmd" = put ]; then args=("$@" "$TPU_NAME:"); else
      rec=(); [ "${1:-}" = --recurse ] && { rec=(--recurse); shift; }
      args=(${rec[@]+"${rec[@]}"} "$TPU_NAME:$1" "$2")
    fi
    if [ "$TPU_KIND" = tpu ]; then
      gcloud compute tpus tpu-vm scp "${args[@]}" "${P[@]}" --zone "$TPU_ZONE" "${SSH[@]}"
    else
      gcloud compute scp "${args[@]}" "${P[@]}" --zone "$TPU_ZONE" "${SSH[@]}"
    fi
    ;;
  delete)
    for zone in $TPU_ZONES; do
      if [ "$TPU_KIND" = tpu ]; then
        if gcloud compute tpus tpu-vm describe "$TPU_NAME" "${P[@]}" --zone "$zone" >/dev/null 2>&1; then
          gcloud compute tpus tpu-vm delete "$TPU_NAME" "${P[@]}" --zone "$zone" --quiet && echo "deleted $TPU_NAME in $zone"
        fi
      elif gcloud compute instances describe "$TPU_NAME" "${P[@]}" --zone "$zone" >/dev/null 2>&1; then
        gcloud compute instances delete "$TPU_NAME" "${P[@]}" --zone "$zone" --quiet && echo "deleted $TPU_NAME in $zone"
      fi
      # the data disk outlives its VM unless deleted after it
      if gcloud compute disks describe "$TPU_NAME-data" "${P[@]}" --zone "$zone" >/dev/null 2>&1; then
        gcloud compute disks delete "$TPU_NAME-data" "${P[@]}" --zone "$zone" --quiet && echo "deleted disk $TPU_NAME-data in $zone"
      fi
    done
    ;;
  *) echo "unknown command $cmd" >&2; exit 2 ;;
esac

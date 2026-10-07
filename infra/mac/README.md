# mac

The resident Macs that run the benchmarks as GitHub runners.

- `fleet.yaml` lists the Macs (tailnet host, login, platform id) and the ones that must never be touched.
- `fleet.sh` runs on your laptop and manages them over ssh.
- `install.sh` / `uninstall.sh` run on a Mac; `fleet.sh` copies them over.

## Everyday use

```sh
infra/mac/fleet.sh status              # is every Mac reachable and its runner online?
infra/mac/fleet.sh keys                # once: copy your ssh key to every Mac
infra/mac/fleet.sh install all         # install or update every runner (asks each Mac's password for sudo)
infra/mac/fleet.sh install m3-16g      # just one
infra/mac/fleet.sh logs m3-16g         # follow its runner log
infra/mac/fleet.sh uninstall m3-16g
```

A new Mac: add it to `fleet.yaml`, to `matrix/platforms.yaml` and to `machines` in `config.json`, then `fleet.sh install <id>`.

## On each Mac

```
~/workspace/pie-evals/
  runner/   GitHub runner (labels self-hosted,macos,<id>) and its job workspace
  pie/      pie checkout       (PIE_ROOT in runner/.env)
  cache/    builds, models, pinned baseline engines (PIE_EVALS_CACHE in runner/.env)
  logs/     runner.log
```

The runner is the system service `com.pie-project.pie-evals-runner` (`/Library/LaunchDaemons`), so it starts at boot without anyone logged in. The install also turns sleep off and restart-after-power-loss on. An older install (`~/actions-runner`, `~/pie`, `~/.cache/pie-evals`) is moved into this layout.

## Before the first install

- Command Line Tools: `sudo touch /tmp/.com.apple.dt.CommandLineTools.installondemand.in-progress; softwareupdate -l` lists them as
  `Command Line Tools for Xcode <ver>`; install with
  `sudo softwareupdate -i "Command Line Tools for Xcode <ver>" --agree-to-license`. If none is listed, update macOS first.
- AC power, Low Power Mode off. Splash needs macOS 26.4 or newer.

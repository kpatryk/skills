# macOS Diagnostic Playbook

Symptom → evidence mapping for Mac troubleshooting, plus a safety tier for each
class of command. Read the section that matches the reported symptom; scan the
safety tiers before running anything that changes state.

## Contents

- [Safety tiers](#safety-tiers)
- [Environment baseline](#environment-baseline)
- [Battery & power](#battery--power)
- [Thermals, fans & performance](#thermals-fans--performance)
- [Sleep, wake & shutdown](#sleep-wake--shutdown)
- [Kernel panics & unexpected restarts](#kernel-panics--unexpected-restarts)
- [Disk, APFS & free space](#disk-apfs--free-space)
- [Wi-Fi & networking](#wi-fi--networking)
- [Bluetooth](#bluetooth)
- [Startup, login items & launchd](#startup-login-items--launchd)
- [Software & toolchains (Homebrew, bun, mise, uv, npm, pip)](#software--toolchains-homebrew-bun-mise-uv-npm-pip)
- [General health sweep](#general-health-sweep)

## Safety tiers

**Tier 0 — passive / read-only.** Safe to run without asking. Start here.
`sw_vers`, `uname -m`, `system_profiler`, `sysctl -n`, `pmset -g` and
`pmset -g assertions`, `pmset -g log`, `log show`, `diskutil list`,
`diskutil info`, `diskutil apfs list`, `df`, `du`, `tmutil listlocalsnapshots`,
`launchctl list`, `launchctl print`, `ps`, `top`, `vm_stat`, `ifconfig`,
`networksetup -getinfo`, `scutil`, `ioreg`, `csrutil status`, `spctl --status`,
`softwareupdate --list`, `fdesetup status`, `tmutil destinationinfo`.

**Tier 1 — read-only but needs root.** Explain why and get a quick OK.
`sudo powermetrics`, `sudo dmesg` (kernel messages), `sudo smartctl` (if
installed), `sudo log collect`/`sudo log show` for some private streams,
`sudo diskutil verifyVolume` on some volumes.

**Tier 2 — state-changing, allowed once evidence justifies it.** These are the
remediations you run *after* passive diagnostics point to a cause. Announce what
you're changing and the expected effect, run it, then verify. They are
reversible-ish and normally safe: `brew update`/`install`/`upgrade`/`link`/
`cleanup`, `mise install/use`, `uv tool install`/`uv cache clean`,
`bun install`/`bun upgrade`, `npm install -g`, `launchctl kickstart` of a
user agent, editing your own shell `PATH`, killing your own stray process,
`pmset` *writes*, `defaults write`, toggling network interfaces, deleting
caches or your own temporary files, `diskutil verifyVolume` on a mounted volume.

**Tier 3 — destructive / hard to undo.** Do not run without explicit,
specific, per-command consent and, where relevant, a backup. `diskutil
erase*`, `diskutil repairVolume` on a damaged volume, `rm -rf` on paths you did
not create, deleting user data, `sudo chown -R` across system paths, Secure
Erase, DFU restore, formatting a volume.

> Rule of thumb: if passive diagnostics justify a Tier 2 change, make it. If you
> cannot state precisely what the command changes and how the user would undo
> it, it's Tier 3 — ask first.

## Environment baseline

```bash
sw_vers                                    # macOS product/version/build
uname -m                                   # arm64 on Apple Silicon
system_profiler SPHardwareDataType         # model, chip, memory, serial
```

## Battery & power

Symptoms: drains fast, drains while asleep, shuts down early, won't charge,
"service battery" warning, fan/heat while charging.

```bash
pmset -g                                   # current power settings
pmset -g ps                                # live battery/AC state
pmset -g assertions                        # who is PREVENTING sleep
pmset -g log                               # sleep/wake + charging history
pmset -g therm                             # thermal pressure affecting performance
system_profiler SPPowerDataType            # cycle count, condition, capacity
ioreg -rn AppleSmartBattery                # raw battery registers
pmset -g custom                            # per-power-source settings
```

Look for:
- Assertions held by a runaway process (`pmset -g assertions` names the PID).
- `Sleep` prevented by `PreventUserIdleSystemSleep` / `PreventSystemSleep`.
- `pmset -g log` showing repeated wakes with a short duration (dark wake storms).
- High `CycleCount` with `Condition: Replace Soon/Service Battery`.
- `lowpowermode` disabled while the drain is thermal.

## Thermals, fans & performance

Symptoms: hot to the touch, fans never stop, sluggish, kernel_task pegging CPU,
performance drops under load.

```bash
ps -Ao pid,pcpu,pmem,comm -r | head -20   # top CPU consumers (snapshot)
top -l 1 -o cpu -n 10                      # one-shot, no interactive UI
pmset -g therm                             # thermal pressure / CPU speed limit
sudo powermetrics --samplers cpu_power -n 1 -i 1000   # needs root
sysctl -n machdep.xcpm.vectors_loaded_count 2>/dev/null || true
log show --predicate 'subsystem == "com.apple.thermalmonitord"' --last 1h --style compact
log show --predicate 'process == "kernel_task"' --last 30m --style compact
```

Look for:
- A runaway process (browser helper, backup, indexing like `mdworker`/`mds`).
- `kernel_task` at high CPU — macOS clamping performance to manage heat, not the cause.
- Sustained `pmset -g therm` `CPU_Speed_Limit` below 100.
- Spotlight indexing (`mds_stores`) after large file changes — usually transient.

## Sleep, wake & shutdown

Symptoms: won't sleep, wakes constantly, drains while closed, won't wake,
spontaneous restarts on sleep.

```bash
pmset -g assertions
pmset -g log | grep -Ei 'wake|sleep|darkwake' | tail -50
log show --predicate 'subsystem == "com.apple.iokit.IOPM"' --last 2h --style compact 2>/dev/null || true
log show --predicate 'eventMessage CONTAINS[c] "wake"' --last 2h --style compact
system_profiler SPUSBDataType SPThunderboltDataType   # devices can block sleep
```

Look for:
- Out-of-band devices (USB hubs, docks, peripherals) waking the Mac.
- `Power Nap`/`Wake on LAN` (`womp`) left enabled.
- Repeated `DarkWake` short cycles — often a peripheral or a scheduled task.
- Bluetooth devices or Find My causing wakes.

## Kernel panics & unexpected restarts

Symptoms: random restart, "your computer restarted because of a problem", black
screen, panic log.

```bash
ls -la /Library/Logs/DiagnosticReports/            # panic, .ips reports
ls -la ~/Library/Logs/DiagnosticReports/
log show --predicate 'process == "kernel"' --last 1d --style compact | tail -100
sysctl -n kern.boottime
sysctl -n vm.panic_on_therm_trip 2>/dev/null || true
nvram -p 2>/dev/null | grep -i panic || true
```

Look for:
- A consistent panic signature (same kext/driver across reports) → likely a
  driver, third-party kernel extension, or a failing device.
- Thermal-trip panics (`panic_on_therm_trip`) → cooling/hardware.
- Watchdog panics under load → hardware or firmware; escalate.

## Disk, APFS & free space

Symptoms: "disk almost full", slow boot, permission errors, I/O errors, volume
disappears, Time Machine snapshot bloat.

```bash
df -h                                      # free space per volume
diskutil list                              # physical/logical layout
diskutil info /                            # volume + SMART summary
diskutil apfs list                         # containers, roles, snapshots
diskutil verifyVolume /                    # Tier 1/2 — verify, not repair
tmutil listlocalsnapshots /                # APFS local snapshots
du -sh ~/* 2>/dev/null | sort -h | tail -20
sudo du -xh /System/Volumes/Data 2>/dev/null | sort -h | tail -20   # Tier 1, slow
log show --predicate 'process == "kernel"' --last 1h --style compact | grep -i -E 'apfs|i/o error'
```

Look for:
- Local APFS snapshots pinning space: `sudo tmutil deletelocalsnapshots` is a
  Tier 2 command — confirm with the user.
- Large caches (`~/Library/Caches`), old Xcode/iOS device support, Docker images.
- `diskutil info` showing `SMART Status: Failing` → back up immediately, escalate.
- I/O errors in the log → failing storage; do not attempt repair first.

## Wi-Fi & networking

Symptoms: drops, slow, won't connect, captive-portal issues, VPN weirdness.

```bash
system_profiler SPAirPortDataType          # current network, channel, RSSI/noise
ifconfig                                   # interface addresses and errors
networksetup -getinfo Wi-Fi
networksetup -listallhardwareports
route -n get default
scutil --dns | head -40
ping -c 5 1.1.1.1
dns-sd -G v4 www.apple.com 2>/dev/null & sleep 3; kill %1 2>/dev/null
log show --predicate 'subsystem == "com.apple.wifi"' --last 1h --style compact | tail -80
```

Look for:
- Weak RSSI (< -70 dBm) or high noise; channel congestion.
- EAPOL/association/auth failures in the log.
- DNS not responding while ping works → resolver issue.
- A stale VPN or proxy config (`networksetup -getwebproxy Wi-Fi`).

## Bluetooth

Symptoms: devices disconnect, won't pair, audio cutouts, mouse lag.

```bash
system_profiler SPBluetoothDataType
system_profiler SPBluetoothDataType 2>/dev/null | grep -Ei 'address|firmware|connected'
log show --predicate 'subsystem == "com.apple.bluetooth"' --last 1h --style compact | tail -80
defaults read /Library/Preferences/com.apple.Bluetooth 2>/dev/null | head -40
```

Look for:
- 2.4 GHz Wi-Fi + Bluetooth coexistence interference.
- Repeated `disconnect`/`connection` events for one device.
- Stale paired-device entries (clearing them is a Tier 2 UI action).

## Startup, login items & launchd

Symptoms: slow login, mystery background CPU/network, app won't launch, "app
wants to control" prompts, third-party daemons after uninstall.

```bash
launchctl list | grep -v -E '^\s*-?\s*[0-9]+\s+0\s+com\.apple\.'   # non-Apple jobs
launchctl print gui/$(id -u) | head -80
ls -la ~/Library/LaunchAgents /Library/LaunchAgents /Library/LaunchDaemons
log show --predicate 'process == "launchd"' --last 30m --style compact | tail -60
system_profiler SPStartupItemDataType
```

Look for:
- A job with a non-zero exit status (`launchctl list` second column).
- Orphaned agents/daemons for uninstalled apps.
- Login items launched via `System Settings > General > Login Items`.

## Software & toolchains (Homebrew, bun, mise, uv, npm, pip)

Symptoms: a tool won't install, upgrade, or run; `brew doctor` warnings; "command
not found" for something you installed; the wrong version runs; a tool breaks
after a macOS update; two version managers fight over the same binary.

First, locate the truth about what is on `PATH` and where it comes from — most
"toolchain" bugs are really ordering or shadowing bugs:

```bash
echo "$SHELL"; echo "$PATH" | tr ':' '\n'
type -a <command>; which -a <command>        # every match, in resolution order
command -v brew; brew --prefix; brew --version
```

If `type -a` shows multiple copies, the first one wins; a stale copy earlier in
`PATH` is the usual culprit.

### Homebrew

```bash
brew doctor                     # actionable warnings
brew config                     # prefix, arch, HOMEBREW_* vars, Xcode CLT
brew update                     # Tier 2: refresh formulae/taps
brew outdated                   # outdated formulae/casks
brew list --versions            # installed versions
brew missing                    # formulae with missing deps
brew tap                        # third-party taps
brew info <formula>             # provenance and caveats
```

Look for: unlinked kegs (`brew link <formula>`), orphaned kegs from removed
taps, untrusted taps, formulae built against the wrong prefix, `/usr/local` vs
`/opt/homebrew` mixups on Apple Silicon, Homebrew temp/caskroom leftovers eating
disk (`/opt/homebrew/var/homebrew/tmp`). `brew doctor` then `brew link` then
`brew cleanup` is a common justified sequence.

### Version managers and package tools

```bash
mise --version; mise doctor; mise ls; mise current; mise where <tool>
bun --version; bun pm ls; bun install; bun upgrade
uv --version; uv python list; uv tool list; uv cache dir; uv pip list
node --version; npm ls -g --depth=0; corepack --version
python3 --version; python3 -m pip --version; pipx list
```

Look for: the manager's shim/activation block missing from `~/.zshrc` (e.g.
`eval "$(mise activate zsh)"`, `eval "$(brew shellenv)"`, `bun` added to
`PATH`); a tool installed under the manager but not exposed; a global
`npm -g` tool shadowed by a Homebrew one (or vice versa); `uv` venv not
activated; architecture mismatch (`arch` shows `arm64` but the binary is x86_64,
or Rosetta shell); and macOS quarantine on a downloaded binary
(`xattr -d com.apple.quarantine <path>` — Tier 2).

### Working the loop on software issues

Read the failing command's own output first — installers almost always name the
cause. Then reproduce with `--verbose`/`--debug`, inspect `PATH`/`type -a`, check
the manager's own doctor/diagnostic command, and only then mutate: re-link,
reinstall, `mise use`, `uv tool install`, fix `PATH`, or clear a corrupt cache.
After a fix, prove it by re-running the original failing command, not just the
installer.

## General health sweep

For "check my Mac's overall health" requests, this ordered pass gives a broad,
evidence-backed picture:

```bash
sw_vers && uname -m
system_profiler SPHardwareDataType SPSoftwareDataType     # model, OS, uptime
df -h
system_profiler SPPowerDataType | grep -Ei 'cycle|condition|maximum capacity'
diskutil info / | grep -Ei 'smart|file system|read-only'
csrutil status && spctl --status && fdesetup status       # security posture
pmset -g assertions                                       # sleep blockers
softwareupdate --list 2>&1 | tail -30                     # pending updates
command -v brew >/dev/null && brew doctor 2>&1 | tail -20 # if Homebrew present
```

Report what is healthy as well as what is not — a clean bill of health is a
legitimate, useful outcome.

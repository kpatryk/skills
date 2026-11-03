---
name: macos-diagnostics
description: >-
  Diagnose and fix problems on a Mac running macOS, including dev-tool
  problems. Use whenever the user reports a Mac issue (battery drain,
  heat/fans, panics, restarts, Wi-Fi/Bluetooth drops, sleep/wake, slowness,
  low disk, rogue processes) OR a tool problem (mise, bun, npm, pnpm, yarn,
  uv, pip, pipx, poetry, brew / brew doctor / brew upgrade failing, tool
  won't install/upgrade/run, wrong version, command not found). Trigger on
  "my Mac is acting up", "brew is broken", "mise won't install X", "this
  tool won't run", even without the word diagnostic. Passive checks first,
  state changes only with evidence, raw traces, structured report filed
  under diagnostics/ as resolved or unresolved.
---

# macOS Diagnostics

Evidence-first troubleshooting for Mac system issues and for dev tools installed on it. Don't guess — probe, verify, log, file a report.

## Use when

- **Mac system:** battery, heat/fans, panics/restarts, Wi-Fi/Bluetooth, sleep/wake, slowness, disk full, SMART, rogue launchd.
- **Tools:** any report that `mise`, `bun`, `npm`/`pnpm`/`yarn`, `uv`, `pip`/`pipx`/`poetry`, `brew` won't install, upgrade, link, or run; `brew doctor` warnings; wrong version runs; `command not found`; PATH/shadowing; arm64 vs Rosetta; Gatekeeper quarantine; broken symlinks.
- Also on "check my Mac's health" with no symptom.

Quick one-liner questions can skip the full report — say so.

## Clarify first

If unclear, ask before spending budget. Don't guess the tool, version, or scope. Ask 1–3 targeted questions covering what's missing:

- What symptom + when/repro? What does "fixed" look like?
- Which tool, version, exact failing command + output?
- System or tool-only? Which Mac/macOS if relevant?

## Rules

1. **Passive first.** Read-only probes (`system_profiler`, `pmset -g`, `log show`, `diskutil`, `df`, `launchctl`, `type -a`, `brew doctor`) before any state change.
2. **10-attempt budget.** One attempt = hypothesis + probe/action + verification. After 10, stop and file as unresolved.
3. **Mutate only with evidence — then do it.** Once passive evidence supports a cause, run the Tier 2 fix (reinstall, re-link, `mise use`, PATH fix, cache clear), announce it, verify. Tier 3 (erase/repair, delete user data, `rm -rf`, system `sudo`, SIP/firmware) needs explicit per-command consent.
4. **Verify symptom, not exit code.** Re-run the failing command / check the symptom is gone.
5. **Log before you act.** Create `diagnostics/working/<slug>/` before first state change; append every command + output; update `report.md` attempt table immediately.
6. **Stop when resolved.** File and quit.

## Workspace

Default root: `./diagnostics/` (or `$MACOS_DIAGNOSTICS_ROOT` / user-specified).

```text
diagnostics/{working,resolved,unresolved}/<issue-slug>/report.md + traces/{command_outputs.log,system_logs.log}
```

`<slug>`: kebab-case (`m2-sleep-drain`, `bun-install-fails`). `working/` is scratch — finalize moves it, never copies.

## Workflow

1. **Capture + init:** 1–2 sentence symptom, slug, then:
   ```bash
   python3 scripts/diag.py init --root diagnostics --slug <slug> --title "…"
   ```
   Log baseline: `sw_vers`, `uname -m`, `system_profiler SPHardwareDataType`.
2. **Loop (≤10):** hypothesis → probe → fix if justified → verify → log. Note unrelated-but-important finds under Incidental Findings without derailing.
3. **Finalize:**
   ```bash
   python3 scripts/diag.py finalize --root diagnostics --slug <slug> --status resolved|unresolved \
     --machine "MacBook Pro (Apple Silicon)" --os "macOS 15.x" --description "One-line index description"
   ```
   Unresolved: executive summary of hypotheses eliminated, machine state, next steps (Safe Mode, Apple Diagnostics via power-on holding `D`, SMC/NVRAM, reinstall/DFU, Apple service).

## Report

Use `references/templates.md` exactly — Summary, RCA, Attempts table (hypothesis/command/result), Traces, Incidental, Lessons. Mark RESOLVED vs UNRESOLVED honestly; folder and status must match.

## References

- `references/templates.md` — exact `report.md` / `index.md` format.
- `scripts/diag.py` — `init` / `log` / `finalize` / `status`. See `--help`.

## Escalate, don't flail

Failing SMART / I/O errors, repeated panics same signature, data loss, T2/enclave/firmware errors, liquid damage, survives Safe Mode → stop, point to Apple Diagnostics, Safe Mode isolation, hardware service.

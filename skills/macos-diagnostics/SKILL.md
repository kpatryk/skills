---
name: macos-diagnostics
description: >-
  Diagnose, troubleshoot, and document problems on a Mac or MacBook running
  macOS — hardware/system issues and the software toolchains installed on it.
  Use this skill whenever the user reports a Mac or toolchain problem: battery
  draining overnight, overheating or loud fans, kernel panics, random restarts,
  Wi-Fi/Bluetooth drops, sleep/wake failures, slowness, low disk space,
  SSD/SMART concerns, misbehaving launchd processes; or broken Homebrew
  packages, brew doctor warnings, failing brew upgrade, or tools managed by
  bun, mise, uv, npm, pipx, or pip that will not install, upgrade, or run.
  Trigger on phrasing like "my Mac is acting up", "brew is broken", or "this
  tool won't install", even without the word "diagnostic". It runs a safe,
  auditable investigation: passive checks first, state changes only when
  evidence justifies them, raw command and log traces, and a structured report
  filed under diagnostics/ as resolved or unresolved with an updated index.
---

# macOS Diagnostics

A disciplined workflow for investigating Mac problems without guessing, without
trashing the machine, and without losing the evidence. The value here is not
just running the right command — it's running the *right command in the right
order*, proving whether it helped, and leaving behind a report a human (or a
future agent) can trust.

## When to use this

Trigger on any "something is wrong with my Mac" request, and on requests to
produce a Mac health report even when nothing is obviously broken.

- **System / hardware symptoms**: battery drain, heat/fans, panics and restarts,
  Wi-Fi/Bluetooth drops, sleep/wake failure, slowness, low disk space, corrupt
  disk warnings, background processes gone rogue.
- **Software / toolchain symptoms**: a dev tool that will not install, upgrade,
  or run — Homebrew (`brew doctor`, `brew upgrade`, taps, links, orphaned or
  unlinked kegs), and anything managed by bun, mise, uv, npm, pnpm, pip, pipx,
  poetry, or similar. This includes PATH/shadowing problems, version-manager
  conflicts, architecture (arm64 vs Rosetta) mismatches, Gatekeeper quarantine,
  and broken symlinks. See the software section of the playbook.

If the user only wants a quick one-line answer, you can still use the diagnostic
mindset but skip the full report — say so in your reply.

## Core operating rules

These exist because a Mac has one user, no easy rollback, and often the
information needed to fix it. Breaking them can cost data.

1. **Passive first.** Gather evidence with read-only commands before changing
   any state. Most "mystery" issues are explained by `system_profiler`,
   `pmset -g`, `log show`, `diskutil`, `df`, and `launchctl` alone. A fix applied
   before the cause is understood usually hides the evidence and can make
   things worse.
2. **Budget of 10 attempts.** An *attempt* is one hypothesis plus the
   command(s) that test it plus the verification that follows. Group related
   read-only probes from a single hypothesis into one attempt; don't burn the
   budget on trivial standalone inspections. After 10 unresolved attempts, stop
   and escalate (see below) rather than flailing.
3. **Mutate state only when evidence justifies it — then go ahead.** Passive
   diagnostics come first, but they are a means, not the goal: once they support
   a specific hypothesis, you *may* run the state-changing command(s) that test
   or fix it (reinstalling a package, re-linking a keg, updating PATH, restarting
   a service). Announce what you are about to change and the expected effect,
   run it, then verify. Reserve explicit consent for **destructive or
   hard-to-undo** actions — disk erase/repair, deleting user data, SIP/firmware
   changes, `rm -rf`, or `sudo` that alters system state. See
   `references/diagnostic-playbook.md` for the safety tiering.
4. **Verify after every attempt.** Run the check that would prove the symptom
   is gone. "Command exited 0" is not verification; the symptom disappearing is.
5. **Log before you act.** Create the issue log *before* the first change of
   state, then update it after every attempt. The log is how you avoid
   re-testing the same hypothesis twice.
6. **Stop the moment it's resolved.** Don't keep poking. File the report.

## Workspace layout

Create and maintain this structure (the script in `scripts/diag.py` can scaffold
it for you):

```text
diagnostics/
├── working/
│   └── <issue-slug>/
│       └── traces/
│           ├── command_outputs.log   # stdout/stderr of diagnostic commands
│           └── system_logs.log       # excerpts from macOS unified log
├── resolved/
│   ├── index.md
│   └── <issue-slug>/
│       ├── traces/{command_outputs.log,system_logs.log}
│       └── report.md
└── unresolved/
    ├── index.md
    └── <issue-slug>/
        ├── traces/{command_outputs.log,system_logs.log}
        └── report.md
```

- **Root location**: the `diagnostics/` directory lives in the current working
  directory by default. If `$MACOS_DIAGNOSTICS_ROOT` is set, or the user names a
  location, use that instead.
- **`<issue-slug>`**: a short kebab-case description, e.g.
  `m2-sleep-battery-drain`, `thermal-fans-idle`, `apfs-disk-space-low`. The same
  slug is used for the folder, the traces, and the index link.
- **`working/`** is the scratch area during the investigation. It only ever
  moves — never gets copied into both `resolved/` and `unresolved/`.

## Workflow

### Step 1 — Capture the symptom and pick a slug

Write the user's complaint in one or two sentences: what they observe, when it
happens, and how they'd know it's fixed. If any of that is missing and matters
(e.g. "slow" — when? doing what?), ask before spending the budget. Choose the
slug now.

### Step 2 — Initialize the log

Create `diagnostics/working/<issue-slug>/traces/` and both trace files. Record
the environment baseline in `command_outputs.log`: `sw_vers`, `uname -m`,
`sysctl -n machdep.cpu.brand_string` (or `system_profiler SPHardwareDataType`).
This is context, not an attempt. From here on, append every command and its
relevant output.

A convenient way to do all of this:

```bash
python3 scripts/diag.py init --root diagnostics --slug <issue-slug> --title "…"
```

### Step 3 — Diagnostic & remediation loop (max 10 attempts)

For each attempt:

1. **Hypothesis** — a specific, testable cause (not "the Mac is broken").
2. **Probe / action** — start with the read-only commands that test the
   hypothesis (see the playbook for symptom → command mapping). Once the
   evidence supports a cause, take the mutating step that fixes it — announce
   it, then run it. Don't stop at a diagnosis you could have acted on.
3. **Verify** — run the check that proves the symptom changed.
4. **Log** — append to `command_outputs.log` and, for each attempt, add an entry
   to `report.md`'s attempt table *immediately*, before the next attempt. Note
   the result even if the attempt failed; a failed attempt is a finding.

If a probe reveals something unrelated but important (failing SMART status, an
almost-full disk, a broken third-party launch daemon), note it under
**Incidental Findings** — don't let it derail the current investigation.

### Step 4 — Finalize

Branch on the outcome:

- **Resolved (attempt ≤ 10):** move `working/<issue-slug>/` to
  `diagnostics/resolved/<issue-slug>/`, write the final `report.md` from the
  template, and add a row to `diagnostics/resolved/index.md`.
- **Unresolved (10 attempts reached):** stop all interventions so you don't
  degrade the machine further. Move the folder to
  `diagnostics/unresolved/<issue-slug>/`, write `report.md` with the best
  root-cause hypothesis and a clear "next steps for a human", and add a row to
  `diagnostics/unresolved/index.md`.

To move the folder and update the index in one step:

```bash
python3 scripts/diag.py finalize --root diagnostics --slug <issue-slug> \
  --status resolved --machine "MacBook Pro (Apple Silicon)" --os "macOS 15.x" \
  --description "Short description for the index row"
```

On the unresolved path, end with a concise executive summary to the user:
hypotheses eliminated, current machine state, and recommended next steps
(Safe Mode, Apple Diagnostics/hardware test, SMC/NVRAM reset, reinstall or DFU
restore, or Apple service). Point them at the report file.

## Writing the report

Use the exact structure in `references/templates.md`. Keep it honest: if the
root cause is a strong hypothesis rather than proven, say so. The attempt table
should read like a lab notebook — hypothesis, command, result — so a reader can
reproduce or falsify your work. Fill **Incidental Findings** and **Lessons
Learned** even though they're optional-feeling; they're often the most useful
part to the user.

## Reference files

- `references/diagnostic-playbook.md` — symptom → passive commands, likely
  causes, and the safety tier of each command. Read the relevant section when
  you start an investigation.
- `references/templates.md` — the exact `report.md` and `index.md` formats to
  copy.
- `scripts/diag.py` — scaffold the workspace, append timestamped trace blocks,
  and finalize/relocate an issue. Run `python3 scripts/diag.py --help`.

## Escalate instead of guessing

Some problems are not agent-fixable and trying harder only risks data. Escalate
to the human when you see: a failing SMART status or I/O errors, repeated kernel
panics with matching signatures, actual data loss, T2/secure-enclave or
firmware errors, liquid-damage sensors, or a symptom that survives Safe Mode.
Give them Apple Diagnostics (`power on holding D`), Safe Mode isolation, and
hardware service as the next steps.

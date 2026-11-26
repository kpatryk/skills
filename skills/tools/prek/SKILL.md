---
name: prek
description: >
  Manage prek git hooks (the fast Rust hook manager): migrate a repo from
  pre-commit (YAML to prek.toml conversion, Rust builtin hooks), audit and
  maintain an existing prek.toml (update hardening backfill, builtin drift,
  minimum_prek_version bumps), harden hook updates with cooldown-days
  supply-chain protection, or clean up legacy pre-commit artifacts (mise tasks,
  CI workflows, AGENTS.md docs, old shims, badges). Use whenever the user
  mentions prek, prek.toml, pre-commit to prek migration, repo: builtin, prek
  util yaml-to-toml, prek update, cooldown-days hardening, or auditing prek
  config — even if they only say "speed up hooks" or "replace pre-commit"
  without naming prek explicitly.
license: MIT
---

# prek — migrate, audit, harden

prek (https://github.com/j178/prek, docs https://prek.j178.dev/) is a Rust drop-in replacement for pre-commit: one binary, no Python runtime for prek itself, parallel setup, Rust-native builtin hooks. `repo: builtin` is prek-only — if the repo must keep running under stock pre-commit (users or CI still install it), stop and keep the YAML.

## 0. Inventory first — read-only, always

A bare invocation (no scope given) means: run the inventory below, classify the repo, report findings, and propose a scoped plan. **Do not edit files, install shims, or commit until the user confirms scope.** Never infer scope from a vague prompt — "migrate to prek" alone gets a proposal, not edits.

```bash
ls .pre-commit-config.yaml .pre-commit-config.yml prek.toml mise.toml .mise.toml 2>/dev/null
grep -rn "pre-commit" mise.toml .mise.toml pyproject.toml package.json tox.ini AGENTS.md README.md CONTRIBUTING.md docs/ .github/ 2>/dev/null \
  | grep -v -E "pre-commit-hooks|CHANGELOG|changelog"
ls .github/workflows/ 2>/dev/null
prek --version && prek util list-builtins
test -f prek.toml && prek validate-config prek.toml
```

Record: which config exists (YAML / `prek.toml` / both / neither); every `repo` + `rev` + hook `id` + `args` / `files` / `exclude` / `types` / `stages`, every `default_*`, and every caller (mise tasks, CI, docs, package.json). Also record what already exists so nothing is duplicated: a `prek` tool entry in mise config, tasks invoking `prek install` / `prek run` / `prek update` (under any name), an `[update]` block, `minimum_prek_version`, a prek badge, a pinned `prek-action` step. Set `CONFIG` to whichever YAML exists: `.pre-commit-config.yaml` or `.pre-commit-config.yml`.

Classify and propose:

| Repo state | Propose |
|---|---|
| **A: YAML only** | **Migrate** (§1, 3 commits) |
| **B: `prek.toml` only** | **Audit / maintain** (§2, usually 1 commit) |
| **C: both files** | finish migration (builtin switch green → delete YAML) + audit |
| **D: neither** | scaffold a fresh `prek.toml` from builtins, then audit rules apply |

Always offer **Full sweep** (`references/cleanup.md`: mise pin, CI pin, docs, badge, shims) as an opt-in add-on, never assumed. List findings as `already OK` vs `missing/stale (will change if approved)` — a re-run on a managed repo should converge to an empty plan.

## Rules

- **Hardening is mandatory, not opt-in** — every migration (commit 3) and every audit lands `[update] cooldown_days = 7`. `freeze` / `include_tags` / `exclude_tags` stay opt-in (offer them in the proposal; never silently apply).
- **Merge, never duplicate** — if a `prek` tool entry, `prek` tasks, `[update]` keys, `minimum_prek_version`, badge, or CI pin already exist, keep them; bump only when stale/loose AND the user approved. Never add a second entry under a different name — adopt whichever task names the repo already uses.
- **Convert, don't translate** — `prek util yaml-to-toml` writes the config; hand-edit only comments and preflight fixes.
- **Installed prek is truth** — builtins and flags come from `prek util list-builtins`, never a static list.
- **Three commits for migrate, one for audit, never squash** — `chore(prek)` in order; commit only when validate + run are green.
- **Commit 1 is a no-op** — keep YAML unchanged; stage only `prek.toml` (YAML preflight edits stay unstaged).
- **One config after commit 2** — YAML dies in commit 2; no long-lived dual config.

## 1. Migrate (YAML → `prek.toml`)

### 1a. Convert

Two kinds of preflight fixes — different files, different commits:

| Fix | Where | Why |
|---|---|---|
| Local YAML parse errors (invalid YAML, duplicate key in the local file) | YAML, before conversion | the converter can't read it; leave this edit unstaged |
| Deprecated stage aliases (`commit`→`pre-commit`, `push`→`pre-push`) and remote rev bumps (duplicate key in a remote hook manifest) | `prek.toml`, after conversion | keeps commit 1 a no-op for stock pre-commit users |

```bash
prek validate-config "$CONFIG"          # parse errors → fix YAML first
prek util yaml-to-toml "$CONFIG" -o prek.toml
# edit prek.toml: stage aliases, rev bumps, comments
prek validate-config prek.toml
prek run --all-files
```

`CONFIG` may be omitted from `yaml-to-toml`; it auto-discovers `.yaml`/`.yml`. Re-add comments the converter dropped. `prek.toml` now wins; on older prek pass `-c prek.toml` explicitly. Run `prek install -f` — the `-f` overwrites stale shims (plain `prek install` preserves a legacy hook, e.g. one still pointing at stock pre-commit or an older prek binary); shims are not committed. Then commit 1 — see §3; stage only `prek.toml`. Details: `references/toml.md`.

### 1b. Builtins

Baseline first, before touching `prek.toml`, so the remote pinned implementation runs:

```bash
PREK_NO_FAST_PATH=1 prek run <hook-id> --all-files   # before: remote impl
```

Run `prek util list-builtins` — ids + flags are ground truth. Move every hook whose id is listed and whose repo is `https://github.com/pre-commit/pre-commit-hooks` into one `[[repos]] repo = "builtin"` block, preserving `args`, `files`, `exclude`, `types`, `stages`. Drop `entry` (forbidden); `language` may stay only as `system`. Everything else stays as-is — remote (ruff, `mirrors-*`, shellcheck, conventional hooks) or local — except local `pygrep` one-liners, which map to `deny-pattern`/`require-pattern` (mapping 4).

```bash
prek run <hook-id> --all-files                       # after: builtin
prek validate-config prek.toml && prek run --all-files
git rm -f --ignore-unmatch .pre-commit-config.yaml .pre-commit-config.yml
prek cache gc
```

Mappings and edge cases: `references/builtins.md`. Then commit 2 — see §3.

## 2. Audit / maintain an existing `prek.toml`

For repo state B (and as a follow-up pass for A/C, and whenever the skill is re-invoked after its own patterns changed). Full checklist: `references/maintain.md`. In short, backfill/verify in order and stage only files that changed:

1. `#:schema https://www.schemastore.org/prek.json` header present.
2. `minimum_prek_version = "<installed prek>"` — bump when stale; replace legacy `minimum_pre_commit_version`, never keep both.
3. `[update] cooldown_days = 7` (or higher) — add when missing; this is how repos migrated before hardening became mandatory get hardened now.
4. Builtin drift — re-run `prek util list-builtins`; move newly-eligible `pre-commit-hooks` ids into the single `repo = "builtin"` block; re-check `check-yaml --disallow-unknown-tags`, `file-contents-sorter` `files:`, `pygrep` → `deny`/`require-pattern`.
5. Ordering + comments — builtins first (guards → fixers → validators), other pre-commit-stage remotes next, `commit-msg` hooks last; don't reorder for aesthetics beyond that (order is execution order unless `priority` is used).
6. `prek update --dry-run` preview only (respects cooldown); apply with `prek update`, review EVERY `rev` change in `git diff`, then validate + green run.
7. `prek install -f` only when shims are stale or hook types changed.

Land as one `chore(prek): audit config to current patterns` commit (split off `rev` bumps into their own commit when both change). When nothing is missing or stale, change nothing and say so.

## 3. Validate and commit

Verify `prek validate-config prek.toml`, `prek run --all-files`, and `prek list` before staging.

| # | `chore(prek)` commit | Contains | Gate |
|---|---|---|---|
| 1 (migrate) | `convert pre-commit config to prek.toml` | `prek.toml` only (converter output + comments); YAML kept and unchanged | validate + green run |
| 2 (migrate) | `switch eligible hooks to builtin and drop pre-commit config` | builtin block; YAML removed with `git rm -f --ignore-unmatch`; `prek cache gc` | validate + green run |
| 3 (migrate) | `migrate settings to native format and add update hardening` | `minimum_prek_version = "<installed prek>"` replacing legacy `minimum_pre_commit_version` when present; `[update] cooldown_days = 7` always; mise/docs/CI/badge deltas only in full sweep | validate + green run |
| audit | `audit config to current patterns` | backfills/bumps from §2; `rev` bumps split into their own commit | validate + green run |

Stage only files that changed: commit 1 stages `prek.toml` only and leaves YAML preflight edits unstaged. Commit 3 always lands the native `minimum_prek_version` **and** the `[update]` cooldown block. Never fold commit 3 work into 1–2, never commit red, never squash.

## References

- `references/maintain.md` (audit checklist: schema, version bump, hardening backfill, builtin drift, ordering, update workflow) · `references/builtins.md` (ground truth, mappings, caveats) · `references/toml.md` (converter, shape, gotchas) · `references/hardening.md` (mandatory cooldown + opt-in freeze/tag filters) · `references/cleanup.md` (opt-in full sweep: mise, docs, badge, CI, shims)
- Upstream: https://prek.j178.dev/ · https://github.com/j178/prek · https://github.com/j178/prek-action

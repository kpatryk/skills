---
name: prek-migrate
description: >
  Migrate a repo from pre-commit to prek (the fast Rust Git hook manager).
  Use this skill whenever the user mentions prek, pre-commit to prek migration,
  prek.toml, converting .pre-commit-config.yaml to TOML, Rust builtin hooks,
  repo: builtin, prek util yaml-to-toml, prek update cooldown-days supply-chain
  hardening, or cleaning up legacy pre-commit artifacts (mise tasks, CI workflows,
  AGENTS.md docs, old shims) — even if they only say "speed up hooks" or "replace
  pre-commit" without naming prek explicitly.
license: MIT
---

# prek-migrate — pre-commit to prek migration

prek (https://github.com/j178/prek, docs https://prek.j178.dev/) is a Rust
drop-in replacement for pre-commit: single binary, no Python runtime needed,
`uv`-backed Python envs, parallel setup, and Rust-native builtin hooks.
This skill performs a **full team migration**: YAML goes away, `prek.toml`
is the single source of truth, eligible hooks become `repo: builtin`, updates
get supply-chain hardening, and legacy pre-commit artifacts are removed.

Why migrate this way instead of staying dual-compatible: `repo: builtin`
skips cloning and Python env setup entirely (offline, zero-setup), while
keeping `.pre-commit-config.yaml` with `repo: https://github.com/pre-commit/pre-commit-hooks`
only gets the automatic fast path, which still clones and builds the env.
The price is that `repo: builtin` runs **only under prek** — which is the
assumption of this skill. If the repo must keep running under stock
pre-commit, stop and keep YAML (see §4 — `repo: builtin` is prek-only).

## 1. Inventory — read before touching anything

Read all of these before planning:

```bash
cat .pre-commit-config.yaml 2>/dev/null
cat prek.toml 2>/dev/null
cat mise.toml 2>/dev/null; cat .mise.toml 2>/dev/null
cat AGENTS.md 2>/dev/null; cat README.md 2>/dev/null | head -n 80
ls .github/workflows/ 2>/dev/null && grep -rl "pre-commit" .github/ docs/ 2>/dev/null
grep -rn "pre-commit" mise.toml AGENTS.md README.md package.json pyproject.toml 2>/dev/null
prek --version; prek util list-builtins
```

Record: every `repo` + `rev` + hook `id` + custom `args`, every
`default_install_hook_types` / `default_stages`, and every place that invokes
`pre-commit` (mise tasks, docs, CI workflows, shell scripts).

## 2. Preflight — fix what prek's strict parser rejects

prek's YAML/TOML parser is stricter than pre-commit's (PyYAML silently kept
the last duplicate key; prek errors). Known real-world rejections
(see https://www.paulsprogrammingnotes.com/2026/06/switching-from-pre-commit-to-prek.html):

- **Duplicate keys in hook manifests** (e.g. old `gruntwork-io/pre-commit`
  `golangci-lint` declared `language:` twice). Fix: bump the hook `rev` to a
  version where upstream fixed it (e.g. `v0.1.30+`).
- **Deprecated stage names** `commit` / `push` in `stages:`. Fix: rename to
  `pre-commit` / `pre-push`, or bump `pre-commit-hooks` to `v6.0.0+` which
  uses modern names.

Check the local config for these, then validate early:

```bash
prek validate-config .pre-commit-config.yaml
PREK_NO_FAST_PATH=1 prek run --all-files  # baseline: pinned impls still pass?
```

## 3. Convert YAML to TOML

Use the deterministic converter, never hand-translate:

```bash
prek util yaml-to-toml .pre-commit-config.yaml -o prek.toml
prek validate-config prek.toml
```

The converter drops YAML comments and anchors — re-add the important ones
by hand (why a hook exists, non-obvious `args`). If both files exist, prek
(0.5.9+) prefers `prek.toml` and prints a warning naming the active config —
confirm with `prek list` right after converting. On older prek the YAML can
win instead; then pass `-c prek.toml` explicitly to every command until the
YAML is deleted in commit 2. Delete the YAML only after `prek.toml`
validates and `prek run --all-files` passes (see §6).

Two converter gotchas: it keeps `minimum_pre_commit_version` (harmless —
prek ignores it; optionally replace it with
`minimum_prek_version = "<your prek version>"`), and it emits TOML 1.1
multiline inline tables, which prek accepts but TOML-1.0 tooling (e.g.
Python's `tomllib`) cannot parse — validate with `prek validate-config`,
not a generic TOML parser.

TOML hook shape (inline or array-of-tables, equivalent):

```toml
[[repos]]
repo = "https://github.com/astral-sh/ruff-pre-commit"
rev = "v0.16.0"
hooks = [
  { id = "ruff-check", args = ["--fix"] },
  { id = "ruff-format" },
]
```

## 4. Convert eligible hooks to `repo: builtin`

Run `prek util list-builtins` (or `prek util list-builtins -v` for args) —
the installed version is ground truth. As of prek 0.5.x the builtins are:

`trailing-whitespace`, `end-of-file-fixer`, `check-added-large-files`,
`check-merge-conflict`, `detect-private-key`, `check-yaml`, `check-toml`,
`check-json`, `check-json5`, `check-jsonc`, `pretty-format-json`,
`check-xml`, `check-vcs-permalinks`, `fix-byte-order-marker`,
`mixed-line-ending`, `check-case-conflict`, `check-illegal-windows-names`,
`forbid-new-submodules`, `file-contents-sorter`, `requirements-txt-fixer`,
`check-symlinks`, `destroyed-symlinks`, `no-commit-to-branch`,
`check-signed-commit`, `check-commit-trailers`,
`check-executables-have-shebangs`, `check-shebang-scripts-are-executable`,
`deny-pattern`, `require-pattern`, `deny-filename-pattern`,
`require-filename-pattern`, `normalize-indentation`.

Rules:

- Any hook `id` in that list whose current `repo` is
  `https://github.com/pre-commit/pre-commit-hooks` moves to one
  `[[repos]] repo = "builtin"` block. Preserve its `args`, `files`,
  `exclude`, `types`, `stages`.
- For `repo: builtin`, `entry` is forbidden and `language` must be omitted
  (or `system`). Configure via `args` exactly like pre-commit.
- Hooks **not** in the list stay as remote repos (pin `rev`, keep working):
  language-specific linters (`ruff-pre-commit`, `mirrors-*`), `shellcheck`
  via jumanjihouse, `conventional-pre-commit` (commit-msg), local `system`/`script`
  hooks. Bump obviously stale pins while migrating.
- `file-contents-sorter` defaults to `files: '^$'` (matches nothing) — it
  needs an explicit `files:` or it silently does nothing. Copy the `files:`
  from the old entry; if the old entry has none, the hook was already a
  silent no-op upstream — flag it to the user and either add `files:`, drop
  the hook, or keep it with a comment saying it is intentionally a no-op.
- `check-yaml` builtin allows unknown YAML tags by default (upstream Python
  rejects them); add `--disallow-unknown-tags` for parity.
- `pretty-format-json` exists **only** via `repo: builtin` (no fast path).
- Non-builtin hooks from `pre-commit-hooks` (e.g. `forbid-binary`,
  `script-must-have-extension`, `shellcheck` from other repos) keep working
  as remote hooks — do not force them into builtin.
- `pygrep`-style custom greps map to `deny-pattern` / `require-pattern`
  builtins instead of cloning a repo for a one-liner.

Example — before (YAML):

```yaml
- repo: https://github.com/pre-commit/pre-commit-hooks
  rev: v6.0.0
  hooks:
  - id: trailing-whitespace
    args: [--markdown-linebreak-ext=md]
  - id: check-yaml
    args: [--allow-multiple-documents]
  - id: end-of-file-fixer
```

After (prek.toml):

```toml
[[repos]]
repo = "builtin"
hooks = [
  { id = "trailing-whitespace", args = ["--markdown-linebreak-ext=md"] },
  { id = "check-yaml", args = ["--allow-multiple-documents"] },
  { id = "end-of-file-fixer" },
]
```

If a builtin behaves differently than the pinned Python original, compare
with `PREK_NO_FAST_PATH=1 prek run` (forces repo impl) and pin the
difference in a comment.

## 5. Supply-chain hardening — `cooldown-days` and pins

`prek update` resolves the newest tag; without a guard a freshly-published
(maybe compromised) release is adopted immediately. Harden it.
After the builtin switch (commit 2), auto-update the remaining remote hooks
so the migration lands on current releases rather than the stale pins copied
from the YAML:

```bash
prek update --cooldown-days 7
git diff prek.toml   # review every rev bump — a hook config is executable code
prek validate-config prek.toml && prek run --all-files
```

This lands in commit 3. If a bumped hook breaks the run, revert just that
hook's `rev` (or pin the incompatibility in a comment) instead of skipping
the update entirely.

```bash
# One-off: only accept releases at least 7 days old
prek update --cooldown-days 7

# Persist in prek.toml so every future update honors it
```

```toml
[update]
cooldown_days = 7          # 0 disables; max 255; skips tags younger than N days
                           # (annotated-tag timestamp, else commit timestamp).
                           # If current rev is newer than the newest eligible
                           # tag, prek keeps rev (no downgrade).
```

Add alongside as needed:

```toml
[update]
cooldown_days = 7
freeze = false             # true pins revs to immutable commit SHAs (strongest pin)
exclude_tags = ["nightly", "*-{alpha,beta,rc}*"]  # glob: skip moving/prerelease tags
include_tags = ["v*"]      # glob: only consider version tags
```

```bash
prek update --freeze              # write SHAs (+ `# frozen:` comments) when immutability required
prek update --check               # CI: fail without rewriting when updates/frozen mismatches exist
prek update --dry-run --exit-code # preview variant of --check
```

Operational notes: review the `prek update` diff before committing (a hook
config is executable code with user permissions); prefer full SHAs for
security-critical repos; never embed credentials in repo URLs — use a
credential helper or short-lived CI token.

## 6. Clear legacy artifacts

The migration is not done until `pre-commit` is unfindable:

1. `git rm .pre-commit-config.yaml .pre-commit-config.yml` — do this in
   commit 2 (§7) together with the builtin switch: once any hook is
   `repo: builtin` the config is prek-only anyway. While both files exist
   prek prefers `prek.toml`, so keeping the YAML through commit 1 is safe
   and keeps stock pre-commit users working.
2. **mise tasks** — if `mise.toml` (or `.mise.toml`) exists, ensure it has
   dedicated prek tasks plus a pinned prek. Never pin `latest` (unreproducible):
   resolve the latest stable release at migration time
   (`mise outdated prek`, or `gh release view --repo j178/prek --json tagName`)
   and pin that exact version:
   ```toml
   [tools]
   prek = "0.5.9"   # fixed stable version, no "latest"

   [tasks.install]
   description = "Install prek git shims"
   run = ["prek install -f"]
   [tasks.hooks]
   description = "Run prek hooks on all files"
   run = "prek run --all-files"
   [tasks."hooks:update"]
   description = "Update prek hook versions (respects cooldown_days)"
   run = "prek update"
   ```
   Delete any `pipx:pre-commit` / `pre-commit` tool entries and pre-commit
   task bodies. If no mise config exists, create `mise.toml` with the above.
   **Config sweep** — `mise.toml` is the single home for hook task wiring.
   Search every config file for pre-commit references (`mise.toml`,
   `.mise.toml`, `pyproject.toml`, `package.json`, `tox.ini`, `.flake8`,
   `lefthook.yml`, `.husky/`, CI workflows). If hook install/run wiring
   lives in `pyproject.toml` or any other non-mise config, move it into
   `mise.toml` tasks and delete it from the other file — prefer mise over
   every other config type. Keep only tool-native settings where they belong
   (e.g. `[tool.ruff]` stays in `pyproject.toml`); hook orchestration itself
   always lives in mise.
3. **Git shims**: `prek install -f` (replaces shims installed by
   `pre-commit install`; plain `prek install` preserves a legacy hook in
   migration mode — use `--force`/`-f` once the old checks are ported).
   Honor `default_install_hook_types` (e.g. `pre-commit`, `commit-msg`).
4. **Docs**: update `AGENTS.md`, `README.md`, `CONTRIBUTING.md`, and everything
   under `docs/` (`pre-commit run --all-files` → `prek run --all-files`,
   `mise run install` semantics). **Badge**: replace any pre-commit badge with
   the prek badge; if no hook-manager badge exists, add it right after the
   title at the top of `README.md`:
   ```markdown
   [![prek](https://raw.githubusercontent.com/j178/prek/main/docs/assets/badge.svg)](https://github.com/j178/prek)
   ```
5. **CI**: run the same hooks as local via
   [j178/prek-action](https://github.com/j178/prek-action) with
   `prek run --all-files`; keep hooks fast (formatters, linters, syntax
   checks) and leave full test suites / browser tests in CI jobs, not hooks.
6. Verify no stragglers: `grep -rn "pre-commit" --include="*.toml" --include="*.md" --include="*.yml" --include="*.yaml" .` should show only historical/changelog mentions and URLs of hook repos (which are fine — they are hook sources, not the tool).

## 7. Commit in three staged commits

Auto-commit progress as you go — three small conventional commits
(`chore(prek): …`), each committed only when `prek validate-config` and
`prek run --all-files` are green. Small commits keep every step bisectable
and reviewable: the no-op conversion stays separate from behavior changes.
Never squash them into one, and never commit a red step — fix forward in
the working tree instead.

Commit 1 — converted config:

```bash
git add prek.toml
git commit -m "chore(prek): convert pre-commit config to prek.toml"
```

Covers §3 only (converter output + re-added comments). Keep
`.pre-commit-config.yaml` in place — prek prefers `prek.toml` when both
exist, so this is a no-op for stock pre-commit users. Run `prek install -f`
locally so new commits already exercise prek (shims live in `.git/hooks`
and are not committed).

Commit 2 — builtin hooks, drop the legacy config:

```bash
git rm .pre-commit-config.yaml .pre-commit-config.yml 2>/dev/null
prek cache gc
git add prek.toml
git commit -m "chore(prek): switch eligible hooks to builtin and drop pre-commit config"
```

Covers §4 plus §6 step 1: eligible hooks moved to `repo: builtin`, YAML
deleted in the same commit (builtin is prek-only, so the old config is dead
weight once the switch is green).

Commit 3 — native settings, hardening, legacy cleanup:

```bash
prek update --cooldown-days 7   # auto-update remaining remote hooks post-conversion
git diff prek.toml              # review every rev bump before staging
prek validate-config prek.toml && prek run --all-files
git add prek.toml mise.toml pyproject.toml package.json AGENTS.md README.md CONTRIBUTING.md docs/ .github/
git commit -m "chore(prek): migrate settings to native format and add hardening"
```

Covers §5 plus the rest of §6: auto-updated remote revs, `[update]` `cooldown_days` /
freeze / tag filters, mise consolidation (hook wiring moved out of
`pyproject.toml`/other configs), rewritten mise tasks, updated docs, badge,
and CI. Add only the files that actually changed. Finish with the §6
straggler grep — only hook-repo URLs and historical mentions may remain.

## 8. Validate and finish

```bash
prek validate-config prek.toml
prek run --all-files
prek list
prek cache gc   # drop caches for repos no longer referenced
```

Expected: `prek run --all-files` green and `git log --oneline -3` shows the
three `chore(prek)` commits from §7. If `prek run` fails on a converted hook, check §4 caveats first,
then `PREK_NO_FAST_PATH=1 prek run <hook-id>` to isolate builtin-vs-upstream
divergence before reverting that hook to its remote form.

Do NOT keep both configs to "be safe" — dual configs drift. One config
(`prek.toml`), one installer (`prek install`), one runner (`prek run`).

## References

- prek docs: https://prek.j178.dev/ (configuration, built-in-hooks,
  migration, security, CLI reference for `prek update --cooldown-days`)
- prek repo: https://github.com/j178/prek
- Migration field notes: https://www.paulsprogrammingnotes.com/2026/06/switching-from-pre-commit-to-prek.html

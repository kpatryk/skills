# Audit / maintain an existing `prek.toml`

For repos that already run prek (no YAML): bring the config up to the current
skill patterns. Work through the list in order; stop at the first item that
does not apply and report "already OK" for the rest. Stage only files that
actually changed.

## Checklist

1. **Schema header** — first lines must be the prek header plus
   `#:schema https://www.schemastore.org/prek.json` (editors get
   completion/validation; the converter emits it, hand-written files often
   lack it).
2. **`minimum_prek_version`** — must equal the installed `prek --version`.
   Bump when stale. If the legacy `minimum_pre_commit_version` is still
   present, replace it — never keep both (prek ignores the legacy key;
   see `references/toml.md`).
3. **`[update]` hardening backfill** — `[update] cooldown_days = 7` (or higher)
   must exist. Repos migrated before hardening became mandatory get hardened
   here. `freeze` / `include_tags` / `exclude_tags` only when the user asked
   for them (`references/hardening.md`).
4. **Builtin drift** — re-run `prek util list-builtins` (installed prek is
   ground truth; new releases add builtins). Move every newly-eligible
   `https://github.com/pre-commit/pre-commit-hooks` id into the single
   `[[repos]] repo = "builtin"` block, preserving `args`, `files`,
   `exclude`, `types`, `stages`. Re-check the three classic gotchas:
   `check-yaml` parity (`--disallow-unknown-tags` unless the repo relies on
   custom tags), `file-contents-sorter` needs an explicit `files:` (without it
   the builtin is a silent no-op — add `files:`, drop the hook, or comment
   that the no-op is intentional), local `pygrep` one-liners map to
   `deny-pattern` / `require-pattern` (mapping 4 in `references/builtins.md`).
5. **Ordering + comments** — builtins first (guards that fail fast, then
   fixers that rewrite files, then validators that check final content),
   other pre-commit-stage remotes next, `commit-msg` hooks last. Do not
   reorder repos/hooks for aesthetics beyond that: hook order is execution
   order unless `priority` is used. Keep the why-comments (non-obvious `args`,
   intentional no-ops, `exclude` reasons).
6. **Remote `rev` freshness (preview, then apply)** —
   ```bash
   prek update --cooldown-days 7 --dry-run   # preview eligible rev bumps
   prek update --cooldown-days 7             # apply only after approval
   git diff prek.toml                        # review EVERY rev change
   prek validate-config prek.toml && prek run --all-files
   ```
   Revert a single hook's `rev` if the new release breaks instead of dropping
   the whole update. A hook config is executable code — read the diff.
7. **Shims** — run `prek install -f` when shims are stale or
   `default_install_hook_types` changed. The `-f` matters: git shims embed
   the absolute path of the prek binary that installed them, so after a
   prek upgrade they keep invoking the old binary — `-f` overwrites them.
   Shims are not committed.

## Commit

One `chore(prek): audit config to current patterns` commit when only §1–5
(plus shims) changed. Split remote `rev` bumps (§6) into their own
`chore(prek): update hook revs` commit when both kinds of changes exist —
config modernization and upstream releases review separately. Gate every
commit on `prek validate-config prek.toml` + green `prek run --all-files`.
When nothing is missing or stale, change nothing and say so: a re-run on a
managed repo converges to zero changes.

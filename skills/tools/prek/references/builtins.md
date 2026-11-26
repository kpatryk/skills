# Builtin hooks — ground truth and mappings

`repo: builtin` runs prek's Rust-native implementations: no clone, no env
setup, works offline. They run **only** under prek, so never move a hook here
while the repo must also work with stock pre-commit.

## Ground truth

```bash
prek --version
prek util list-builtins        # ids, descriptions, supported flags
```

`-v` is the global verbosity flag and does not change this listing; flags are
already shown for every builtin that accepts any.

The installed version is the only authoritative list — builtin ids and flags
change between releases. Never copy a list from docs, memory, or another repo.

A hook is eligible when all of these hold:

- its `repo` is `https://github.com/pre-commit/pre-commit-hooks`
- its `id` appears in `prek util list-builtins`
- its pinned behavior matches the builtin at the current prek version

Any `pre-commit-hooks` id not listed stays remote as-is — never force it into
builtin. Hooks from other repos and local hooks are out of scope here, except
for the local `pygrep` mapping below.

Put every eligible hook into one block:

```toml
[[repos]]
repo = "builtin"
hooks = [
  { id = "trailing-whitespace", args = ["--markdown-linebreak-ext=md"] },
  { id = "check-added-large-files", args = ["--maxkb=1024"] },
]
```

Preserve `args`, `files`, `exclude`, `types`, `types_or`, `exclude_types`,
`stages`, `always_run`, `pass_filenames`. `entry` is rejected for builtin
hooks; `language` may be omitted, and if set must be `system`.

## Example mappings

Mappings 1–3 move eligible `pre-commit-hooks` hooks; mapping 4 replaces a local
`pygrep` hook.

1. Plain id with args (above). Keep every `args` entry verbatim; builtin flags
   mirror the upstream hook, not the old `entry`.

2. `check-yaml` — parity for unknown tags:

   ```yaml
   - id: check-yaml
     args: [--allow-multiple-documents]
   ```

   ```toml
   { id = "check-yaml", args = ["--allow-multiple-documents", "--disallow-unknown-tags"] }
   ```

   The builtin accepts unknown YAML tags by default; upstream Python rejects
   them. Add `--disallow-unknown-tags` unless the repo relies on custom tags.

3. `file-contents-sorter` — needs an explicit `files`:

   ```yaml
   - id: file-contents-sorter
     files: ^requirements/.*\.txt$
   ```

   ```toml
   { id = "file-contents-sorter", files = '^requirements/.*\.txt$' }
   ```

   Use a TOML literal string (`'…'`) so backslashes survive untouched.

4. `pygrep` one-liner to builtin:

   ```yaml
   - repo: local
     hooks:
       - id: no-todo
         name: no TODO markers
         language: pygrep
         entry: TODO
         types: [text]
   ```

   ```toml
   { id = "deny-pattern", name = "no TODO markers", args = ["TODO"], types = ["text"] }
   ```

   The regex goes in `args`; `require-pattern` is the "must contain" variant,
   and `deny-filename-pattern` / `require-filename-pattern` cover filenames.
   Drop the now-empty `repo: local` entry.

## Caveats

- On re-runs (audit mode) the installed prek may know builtins the config
  predates — drift newly-eligible ids into the builtin block then, too
  (`references/maintain.md`).
- Within the builtin block, keep guards first (fail fast, no file
  modifications), then fixers that rewrite files, then validators that check
  the final content — but do not reorder repos/hooks for aesthetics beyond
  that: hook order is execution order unless `priority` is used.

- `file-contents-sorter` defaults to `files: '^$'`, which matches nothing — it
  is a silent no-op without `files:`. Copy the old `files:`; if the old hook
  had none, it was already a no-op. Flag it and either add `files:`, drop the
  hook, or keep it with a comment saying the no-op is intentional.
- `check-yaml` builtin is more permissive than upstream: add
  `--disallow-unknown-tags` for parity (see mapping 2).
- `pretty-format-json` has no automatic fast path — use the builtin (or keep
  the hook remote).
- `pygrep`/shell-grep custom hooks map to `deny-pattern` / `require-pattern`
  (or filename variants) instead of cloning a repo for a regex.
- `entry` is forbidden on builtin hooks; `language`, if set, must be `system`
  (omitting it is fine). Any other language fails validation in prek.

## Verify

```bash
# Before switching: pinned upstream implementation
PREK_NO_FAST_PATH=1 prek run <hook-id> --all-files
# After switching: builtin implementation
prek run <hook-id> --all-files
```

`PREK_NO_FAST_PATH` only disables prek's automatic fast path for remote
`pre-commit-hooks`; it does not recreate a remote implementation for a hook
already configured as `repo: builtin`. Compare against the YAML config (or a
temporary copy pointing at `pre-commit/pre-commit-hooks`) when behavior
diverges, then pin the difference in a comment or revert that hook to remote.

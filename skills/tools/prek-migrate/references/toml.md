# YAML → `prek.toml` — converter, shape, gotchas

## Convert

Use the deterministic converter; never hand-translate hook by hook.

```bash
CONFIG=.pre-commit-config.yaml   # or .yml; auto-discovered when omitted
prek util yaml-to-toml "$CONFIG" -o prek.toml
prek validate-config prek.toml
prek run --all-files
```

- `CONFIG` is optional: without it the converter discovers
  `.pre-commit-config.yaml` / `.pre-commit-config.yml`.
- `-o/--output` defaults to `prek.toml` next to the input.
- It refuses to overwrite an existing output unless you pass `--force`.
- It prepends a header and `#:schema https://www.schemastore.org/prek.json`,
  which gives editors completion/validation.

## Shape

One minimal, valid file:

```toml
default_stages = ["pre-commit"]
default_install_hook_types = ["pre-commit", "commit-msg"]

[[repos]]
repo = "builtin"
hooks = [
  { id = "trailing-whitespace" },
  { id = "check-yaml", args = ["--disallow-unknown-tags"] },
]

[[repos]]
repo = "https://github.com/astral-sh/ruff-pre-commit"
rev = "<pinned tag>"
hooks = [
  { id = "ruff-check", args = ["--fix"] },
  { id = "ruff-format" },
]
```

Add an `[update]` block only when hardening is requested
(`references/hardening.md`); a plain migration leaves update behavior at its
defaults. `minimum_prek_version` is also optional here: commit 3 sets it to
the installed `prek --version`.

Inline hook tables and `[[repos.hooks]]` arrays of tables are equivalent; use
whichever the converter emits and keep edits local.

## Converter gotchas

- **Comments and anchors are dropped.** Anchors/aliases/merge keys are
  expanded into concrete entries; YAML comments disappear except the generated
  header. Re-add the important ones by hand — why a hook exists, non-obvious
  `args`, intentional no-ops.
- **`minimum_pre_commit_version` is carried over but ignored** by prek
  (upstream key). Replace it with `minimum_prek_version = "<installed prek>"`
  in commit 3. Do not leave both.
- **TOML 1.1 multiline inline tables.** The converter emits multiline inline
  tables, which prek accepts. Older TOML parsers do not (Python 3.13
  `tomllib` rejects them; newer Python accepts TOML 1.1). Validate with
  `prek validate-config`, not a generic TOML parser. If other tooling must
  read the file, rewrite hooks as `[[repos.hooks]]` arrays of tables.
- **`[update]` typos pass validation.** `prek validate-config` does not reject
  unknown `[update]` keys. Copy field names from
  https://prek.j178.dev/reference/configuration/#update.
- **Deprecated stage names** (`commit`, `push`) are preserved by the
  converter. Normalize them in `prek.toml` after conversion (not in the YAML,
  so commit 1 stays a no-op) so the config matches modern pre-commit-hooks
  manifests.
- **Ordering is preserved.** Do not reorder repos/hooks for aesthetics; hook
  order is execution order unless `priority` is used.

## Which file wins

If both files exist, prek uses `prek.toml` first and warns naming the active
config. Confirm with `prek list` (it lists hooks from the active config);
`prek run --dry-run` also shows what would run. On older prek versions the
YAML can win — pass `-c prek.toml` explicitly to every command (`run`,
`validate-config`, `install`, `update`) until the YAML is deleted in commit 2.

Do not keep both configs long-term to "be safe": they drift. One config
(`prek.toml`), one installer (`prek install`), one runner (`prek run`).

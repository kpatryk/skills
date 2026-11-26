# Full legacy cleanup — OPT-IN

Use only when the user asks to "remove all traces", "consolidate into mise",
or update "mise/docs/CI/badge". A plain migration changes only the config and
leaves these artifacts alone.

## Sweep checklist

| Artifact | Action | Verify |
| --- | --- | --- |
| `.pre-commit-config.yaml` / `.yml` | `git rm -f --ignore-unmatch .pre-commit-config.yaml .pre-commit-config.yml` in commit 2, after the builtin switch is green. | `ls` reports nothing |
| mise `prek` tool | Pin an exact stable version (resolve at migration time). Never `latest`. Remove `pre-commit` / `pipx:pre-commit` entries. | `grep -n prek mise.toml` |
| mise hook tasks | Move install/run/update wiring here: `prek install -f`, `prek run --all-files`, `prek update`. | `mise tasks` |
| Other config wiring | Rewrite surviving invocations to `prek` and move hook orchestration into mise tasks; delete pre-commit-specific blocks from `package.json` (e.g. `prepare`/`lint-staged`), `tox.ini`, `.husky/`, `lefthook.yml`, and similar wrappers. Keep tool-native settings (e.g. `[tool.ruff]`) where they belong. | `grep -rn "pre-commit"` |
| Git shims | `prek install -f` (the `-f` overwrites stale shims, which embed the installing binary's absolute path); honors `default_install_hook_types` (`pre-commit`, `commit-msg`, …). Plain `prek install` preserves a legacy hook in migration mode. | `ls .git/hooks` |
| Docs | Replace `pre-commit run/install` in `AGENTS.md`, `README.md`, `CONTRIBUTING.md`, `docs/`, scripts. | `grep -rn "pre-commit"` |
| Badge | Replace a pre-commit badge with the prek badge, or add the prek badge right after the README title when none exists. | README diff |
| CI | Run hooks via `j178/prek-action` pinned to an exact tag or full SHA, and pin `prek-version`. | workflow diff |
| Stragglers | Final grep: only hook-repo URLs and historical/changelog mentions may remain. | see below |

Resolve the pin, then write the mise block (create `mise.toml` if the repo has
no mise config). Merge, never duplicate: if a `prek` tool entry or tasks
invoking `prek install` / `prek run` / `prek update` already exist under any
names, keep them and fill in only what is missing — never add a second set of
tasks under a different naming scheme.

```bash
gh release view --repo j178/prek --json tagName -q .tagName
# or: mise outdated prek
```

```toml
[tools]
prek = "<installed prek>"   # exact version from `prek --version`, never "latest"

[tasks."prek:install"]
description = "Install prek git shims"
run = ["prek install -f"]

[tasks."prek:run"]
description = "Run prek hooks on all files"
run = "prek run --all-files"

[tasks."prek:update"]
description = "Update prek hook versions (honors [update] when configured)"
run = "prek update"
```

Ensure badge was added to the README or relevant documentation at the root of the repository:

```markdown
[![prek](https://raw.githubusercontent.com/j178/prek/main/docs/assets/badge.svg)](https://github.com/j178/prek)
```

CI (same hooks as local; keep tests/browser suites in dedicated jobs):

```yaml
- uses: j178/prek-action@<exact_sha>   # no floating v3 or similar tag exists
  with:
    prek-version: "<installed prek>"   # pin exactly; default is latest
```

Pin the action to an exact release tag (or a full commit SHA) — never a floating
major. Check the current tag with
`gh release view --repo j178/prek-action --json tagName -q .tagName` and keep
`prek-version` on the same prek release you run locally.

Final check:

```bash
grep -rn "pre-commit" --include="*.toml" --include="*.md" \
  --include="*.yml" --include="*.yaml" --include="*.json" \
  --include="*.py" --include="*.sh" --include="*.ini" --include="*.cfg" . \
  | grep -v -E "pre-commit-hooks|CHANGELOG|changelog"
```

Expected: no tool references (`pre-commit run`, `pre-commit install`,
`pipx:pre-commit`, task names). Hook source URLs and history are fine.

Land cleanup deltas in commit 3 (YAML removal stays in commit 2), staging only
files that actually changed.

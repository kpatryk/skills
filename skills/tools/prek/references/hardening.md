# Supply-chain hardening — mandatory cooldown, opt-in pins

Every migration and every audit lands `[update] cooldown_days = 7`. It changes
update behavior, which is exactly the point: without it, `prek update` adopts
the newest eligible tag, so a freshly published (possibly compromised) release
is adopted on the next update. `freeze` and tag filters stay opt-in — offer
them in the plan proposal, never apply them silently.

## Why

`prek update` resolves the newest eligible tag. Without a guard, a freshly
published (possibly compromised) release is adopted on the next update. A
cooldown and tag filters make fresh tags ineligible until they have aged.

## Persist settings

```toml
[update]
cooldown_days = 7          # 0 disables; 0–255 days
freeze = false             # true writes immutable commit SHAs as rev
include_tags = ["v*"]      # glob string or list; only consider these
exclude_tags = ["nightly", "*-{alpha,beta,rc}*"]  # glob string or list
```

| Key | Type | Default | Effective behavior |
| --- | --- | --- | --- |
| `cooldown_days` | integer 0–255 | `0` (disabled) | Skips tags younger than N days; age = annotated-tag timestamp, else tagged-commit timestamp. Keeps the current `rev` when it is newer than the newest eligible tag (no downgrade). |
| `freeze` | boolean | `false` | Writes frozen commit SHAs into `rev` (strongest pin). `--freeze` forces it on. |
| `include_tags` | glob string / list | empty | Only tags matching a glob are update candidates. |
| `exclude_tags` | glob string / list | empty | Matching tags (nightlies, prereleases) are skipped. |

Per-repo overrides are possible in `[update.repos."<repo-url>"]` with
`include_tags` / `exclude_tags`. CLI flags override project settings, which
override the user-level global config.

## Update workflow

```bash
prek update --cooldown-days 7 --dry-run   # preview eligible rev bumps
prek update --cooldown-days 7             # apply
git diff prek.toml                        # review EVERY rev change
prek validate-config prek.toml && prek run --all-files
```

A hook config is executable code with the user's permissions. Read the diff;
revert a single hook's `rev` if the new release breaks, instead of dropping the
whole update.

Variants:

```bash
prek update --freeze              # rewrite revs as immutable SHAs
prek update --check               # alias: --dry-run --exit-code (CI gate)
prek update --dry-run --exit-code # explicit preview gate
prek update --include-tag 'v*' --exclude-tag '*-rc*'
```

Operational notes: prefer full SHAs for security-critical repos; never embed
credentials in repo URLs (use a credential helper or a short-lived CI token);
keep `[update]` in the project config so every future update honors it.

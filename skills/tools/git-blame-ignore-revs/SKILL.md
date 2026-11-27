---
name: git-blame-ignore-revs
description: >
  Scan the full history of the current branch for formatting-only commits and
  maintain the git-blame ignore-revs file. Use when the user mentions
  blame.ignoreRevsFile, .git-blame-ignore-revs, git blame ignore, blame
  records, ignore revs, or asks to hide formatting commits from git blame.
license: MIT
---

# git-blame-ignore-revs

Scan the full history reachable from `HEAD` (root commit to tip) for
formatting-only commits and record them in the ignore-revs file that
`blame.ignoreRevsFile` points to, so `git blame` skips bulk reformatting noise.

**Never assume the filename** — always resolve it from
`git config --show-origin --get blame.ignoreRevsFile`. Only fall back to
`.git-blame-ignore-revs` at the repo root when the key is unset.

**Requires:** git (≥2.37 for `--ignore-revs-file`), python3 (≥3.11), POSIX sh.

Run scripts by their absolute path under this skill's directory (the `scripts/`
folder next to this `SKILL.md`), e.g.
`python3 <skill-dir>/scripts/inventory.py --json`, with CWD set to the target
repository. Do not use a relative `scripts/...` path from the repo root — the
skill may be installed globally while it operates on the local repo.

## Rules

- **Filename comes from git config** — resolve via `git config --show-origin
  --get blame.ignoreRevsFile` (report local/global/system scope on mismatch).
  Never hardcode `.git-blame-ignore-revs` except as the default when unset.
- **Git work tree only** — abort if outside a git work tree.
- **Missing file needs approval** — if the configured file does not exist,
  stop and ask the user to approve creating it. Pass `--create` to
  `patch.py` only after explicit approval. The new file is committed together
  with the scan results at the end, never as a separate commit.
- **Full branch history** — scan `git log --no-merges HEAD` from the root commit to
  the tip (skip merges, skip SHAs already listed). This is slow on large repos
  by design; do not silently cap it.
- **Confidence levels** — `--auto-high` commits only whitespace-proof commits
  (`git diff-tree --numstat` non-empty but `git diff-tree -w --numstat`
  empty). Medium-confidence (formatting keywords in the message) is proposed
  with evidence and added only via explicit `--add <sha>` approval. Low
  (plain code changes) is reported as a count, never added.
- **Merge, never overwrite** — preserve comments, keep first occurrence on
  duplicates, annotate each added SHA with `# <short> <date> <subject>`,
  ensure trailing newline. Quarantine nothing; invalid pre-existing lines are
  reported by Verify, not silently deleted.
- **Local scope only** — set `blame.ignoreRevsFile` with `--local` only.
- **Commit only if changed and green** — a single commit with message
  `chore(blame): ignore <n> formatting commit(s) in git blame` only when
  Patch reported a change and Verify passes. Otherwise commit nothing and
  print a concise summary (`scanned N, M already ignored, K new`).

## Workflow

### 1. Inventory (read-only)

Run `<skill-dir>/scripts/inventory.py --json` (pass `--file` to override the
configured filename). Record branch, total commit count, effective config +
origin, whether the file exists / is tracked / is gitignored, active SHA
count, malformed lines, and formatter signals (prettier, black, rustfmt,
editorconfig, prek configs).

### 2. Missing-file gate

If the file does not exist, stop and ask: `Create <filename> and set
git config --local blame.ignoreRevsFile <filename>? (yes/no)`. Proceed only
on explicit `yes` (then `patch.py --create`). On `no`, stop with no changes.

### 3. Scan (read-only)

Run `<skill-dir>/scripts/scan.py --json`. Report high-confidence candidates
(`to_add`, auto-eligible) with SHA + subject + evidence, medium-confidence
(`propose`) for approval, and the low count. If `to_add` is empty and no
approved `--add` SHAs exist, stop with a concise summary and change nothing.

### 4. Patch

Run `<skill-dir>/scripts/patch.py --json --auto-high [--add <sha>...]
[--create] [--dry-run]` (add `--file` to override, `--no-config` to skip
config writes). The script resolves explicit SHAs via `git rev-parse`,
dedupes against existing entries, appends `# <short> <date> <subject>` +
full-SHA lines, and sets local `blame.ignoreRevsFile` when missing or
mismatched. Use `--dry-run` to preview.

### 5. Verify

Run `<skill-dir>/scripts/verify.py --json`. It checks the file exists, every
active SHA resolves via `git cat-file -e`, no malformed lines, effective
config matches the file, and a `git blame --ignore-revs-file` smoke test on
a tracked file succeeds. Exit code 0 means green.

### 6. Commit and report

If Patch reported no change or Verify failed, commit nothing. Otherwise
stage only the revs file (`git add -f` since it may be gitignored) and
create a single `chore(blame): ignore <n> formatting commit(s) in git blame`
commit. Then summarize: file path, config status, SHAs added with subjects,
proposed-but-skipped mediums, and any warnings (dangling SHAs after a
rebase, gitignored file).

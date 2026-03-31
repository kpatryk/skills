---
name: cosmic-ray
license: MIT
description: >
  Comprehensive guide for Cosmic Ray, the Python mutation testing framework with
  session-based execution, distributors, and reporting tools. Use this skill whenever
  a user asks about mutation testing with Cosmic Ray, configuring `config.toml`,
  running `cosmic-ray init/baseline/exec`, interpreting `cr-report` output, filtering
  mutation jobs, running distributed HTTP workers, generating HTML/XML/badge reports,
  or integrating mutation thresholds into CI. Trigger this skill whenever users mention
  surviving mutants, session sqlite files, `cr-rate`, `cr-html`, or distributed mutation runs.
---

# cosmic-ray

`cosmic-ray` is a Python mutation testing tool built around **sessions** (`.sqlite` work manifests), configurable mutation scopes, and pluggable execution distributors (`local`, `http`).

## Documentation URLs used to create this skill

- https://cosmic-ray.readthedocs.io/en/latest/index.html
- https://cosmic-ray.readthedocs.io/en/latest/theory.html
- https://cosmic-ray.readthedocs.io/en/latest/tutorials/intro/index.html
- https://cosmic-ray.readthedocs.io/en/latest/tutorials/distributed/index.html
- https://cosmic-ray.readthedocs.io/en/latest/concepts.html
- https://cosmic-ray.readthedocs.io/en/latest/reference/cli.html
- https://cosmic-ray.readthedocs.io/en/latest/reference/continuous_integration.html
- https://cosmic-ray.readthedocs.io/en/latest/reference/badge.html
- https://cosmic-ray.readthedocs.io/en/latest/_sources/how-tos/filters.rst.txt

## Core model

Mutation testing cycle in Cosmic Ray:

1. Configure target modules + test command.
2. Initialize a session DB with all pending mutation jobs.
3. Baseline unmutated tests.
4. Execute pending mutation jobs.
5. Report survivors/kills/incompetents and iterate on tests.

## Install

```bash
pip install cosmic-ray
```

## Essential CLI workflow

```bash
# 1) Create config interactively
cosmic-ray new-config config.toml

# 2) Initialize session database
cosmic-ray init config.toml session.sqlite

# 3) Verify baseline on unmutated code
cosmic-ray --verbosity INFO baseline config.toml

# 4) Execute pending mutation jobs
cosmic-ray exec config.toml session.sqlite

# 5) Review results
cr-report session.sqlite --show-pending
cr-html session.sqlite > report.html
```

## Minimal `config.toml`

```toml
[cosmic-ray]
module-path = "src/my_pkg"
timeout = 20.0
excluded-modules = ["**/*_test.py"]
test-command = "pytest -x"

[cosmic-ray.distributor]
name = "local"
```

### Key configuration fields

- `module-path`: file, directory, or list of paths to mutate.
- `timeout`: max runtime per mutant test execution.
- `excluded-modules`: glob exclusions from mutation.
- `test-command`: how to run tests (run from current working dir / worker dir).
- distributor section: execution strategy (`local` or `http`).

## Session semantics and re-init rules

- `init` creates/rewrites session work manifest.
- Re-run `init` when code-under-test, tests, or mutation-affecting config changes.
- Do **not** re-init a session if you need to keep existing results.
- You can inspect progress while execution is running (`cr-report` supports this).

## Interpreting outcomes

- **killed**: tests failed on mutant (good).
- **survived**: tests passed despite mutation (action needed).
- **incompetent**: mutant caused runtime pathologies (for example timeout/infinite loop).

Use survivors to drive targeted test improvements.

## Report and gating utilities

```bash
# Text report
cr-report session.sqlite --show-diff --surviving-only

# HTML report
cr-html session.sqlite > mutation-report.html

# XML for CI systems
cr-xml session.sqlite > mutation-report.xml

# Survival rate
cr-rate session.sqlite

# Fail CI if survival exceeds threshold (%)
cr-rate session.sqlite --fail-over 20

# Confidence-interval estimate
cr-rate session.sqlite --estimate --confidence 95.0
```

## Distributed execution (HTTP distributor)

Use when mutation volume is large and local serial execution is too slow.

### Config

```toml
[cosmic-ray]
module-path = "mod.py"
timeout = 10.0
excluded-modules = []
test-command = "python -m unittest test_mod.py"

[cosmic-ray.distributor]
name = "http"

[cosmic-ray.distributor.http]
worker-urls = ["http://localhost:9876", "http://localhost:9877"]
```

### Start workers

```bash
cosmic-ray --verbosity INFO http-worker --port 9876
cosmic-ray --verbosity INFO http-worker --port 9877
```

Each worker needs its own independent code copy to avoid mutation collisions.

### Scale helper

```bash
cr-http-workers config.toml .
```

`cr-http-workers` can clone a git repo per worker URL and manage worker lifecycle (local machine scope).

## Filters (post-init mutation pruning)

Run filters after `init` to skip non-actionable mutations:

```bash
cosmic-ray init config.toml session.sqlite
cr-filter-pragma session.sqlite
cr-filter-git session.sqlite
cr-filter-operators config.toml session.sqlite
```

### Available built-in filters

- `cr-filter-pragma`: skip lines containing `# pragma: no mutate`.
- `cr-filter-git`: keep only mutations on changed/new lines against a branch.
- `cr-filter-operators`: skip operator classes via regex patterns in config.

## Advanced debugging commands

```bash
# List plugins
cosmic-ray operators
cosmic-ray distributors

# Inspect raw session data
cosmic-ray dump session.sqlite | head

# Apply a specific mutation to disk (debug tool)
cosmic-ray apply path/to/module.py core/NumberReplacer 0

# Single mutate+test worker cycle
cosmic-ray mutate-and-test path/to/module.py core/NumberReplacer 0 "pytest -x"
```

## Best practices from docs and operation model

- Keep tests separate from production modules to avoid mutating tests themselves.
- Use fail-fast test commands (`pytest -x`) for faster kill detection.
- Commit changes before `exec` (mutations happen on disk; protects against unexpected crash states).
- Tune `timeout` realistically to avoid excessive incompetent mutants.
- For large projects: use HTTP workers and/or filter passes to reduce wall time.

## pre-commit integration

No official Cosmic Ray pre-commit hook is documented.

If needed, use a local hook for targeted checks (full mutation runs are expensive for every commit):

```yaml
repos:
  - repo: local
    hooks:
      - id: cosmic-ray-rate-gate
        name: cosmic-ray mutation gate
        entry: bash -c 'cosmic-ray init config.toml session.sqlite && cosmic-ray exec config.toml session.sqlite && cr-rate session.sqlite --fail-over 20'
        language: system
        pass_filenames: false
```

## Usage examples (input -> expected output)

### Example 1: End-to-end local run

- Input: "Run mutation testing against `src/my_pkg` locally."
- Commands:
  ```bash
  cosmic-ray new-config config.toml
  cosmic-ray init config.toml session.sqlite
  cosmic-ray baseline config.toml
  cosmic-ray exec config.toml session.sqlite
  cr-report session.sqlite
  ```
- Expected output:
  - Session completes with kill/survival summary and mutation percentage.

### Example 2: Focus on surviving mutants only

- Input: "Show only survivors with diffs so I can write new tests."
- Command:
  ```bash
  cr-report session.sqlite --show-diff --surviving-only
  ```
- Expected output:
  - Concise list of surviving mutants with mutation diff context.

### Example 3: Parallel run using HTTP workers

- Input: "Speed this up across multiple workers."
- Commands:
  ```bash
  cosmic-ray --verbosity INFO http-worker --port 9876
  cosmic-ray --verbosity INFO http-worker --port 9877
  cosmic-ray init config.toml session.sqlite
  cosmic-ray exec config.toml session.sqlite
  ```
- Expected output:
  - Mutations distributed to workers; lower wall-clock execution time.

## Troubleshooting

- Baseline fails: fix tests first; mutation results are not meaningful otherwise.
- `exec` appears hung: inspect active workers, timeout settings, and run `cr-report` for progress.
- Unexpectedly high survivors: verify test command scope and whether tests actually assert behavior.
- Worker errors in distributed mode: ensure worker URLs match config and each worker runs in correct code directory.

## Agent execution checklist

When helping users with Cosmic Ray:

1. Ensure baseline passes.
2. Confirm config targets only production code.
3. Initialize fresh session after relevant code/config changes.
4. Execute mutations and report survivors with diffs.
5. Recommend specific test improvements tied to surviving mutants.
6. Add CI gate with `cr-rate --fail-over <threshold>` when desired.

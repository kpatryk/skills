---
name: mutmut
description: >
  Comprehensive guide for mutmut, a Python mutation testing tool focused on fast,
  incremental workflows. Use this skill whenever a user asks about mutation testing,
  surviving mutants, improving test quality beyond coverage, mutmut configuration in
  `setup.cfg` or `pyproject.toml`, mutmut TUI usage (`mutmut browse`), applying mutants
  to disk, or performance tuning (stack depth, pytest args, coverage line filtering).
  Trigger this skill even when users only mention "mutation score", "killed vs survived
  mutants", "tests pass but bug slips through", or "how do I make pytest tests stronger".
---

# mutmut

`mutmut` is a Python mutation testing tool with an incremental workflow: mutate code, run relevant tests, inspect survivors, improve tests, and rerun.

## Documentation URLs used to create this skill

- https://mutmut.readthedocs.io/en/latest/
- https://mutmut.readthedocs.io/en/latest/#mutmut---python-mutation-tester
- https://raw.githubusercontent.com/boxed/mutmut/master/README.rst

## What mutmut is best for

- Finding weak assertions that code coverage misses.
- Improving unit-test precision by targeting survivors.
- Incremental mutation testing during normal development.

## Requirements and platform caveats

- `mutmut` requires OS-level `fork` support.
- On Windows, run via WSL.
- On some architectures (documented for `x86_64-darwin`), `libcst` may require Rust tooling (`rustc`, `cargo`) during install.

## Install and first run

```bash
pip install mutmut
mutmut run
```

By default mutmut uses `pytest` and auto-discovers typical test/code locations.

## Core workflow

1. Run mutations:
   ```bash
   mutmut run
   ```
2. Inspect/retest in TUI:
   ```bash
   mutmut browse
   ```
3. Improve tests for surviving mutants.
4. Retest from TUI (`r`, `f`, `m`) or rerun from CLI.
5. Repeat until survivors are intentional or eliminated.

### TUI shortcuts (documented)

- `r`: rerun selected mutant
- `f`: retest function
- `m`: retest module

## Incremental behavior and state

`mutmut` stores progress in `mutants/` and resumes work between runs. If you need a full restart, remove `mutants/`.

```bash
rm -rf mutants/
mutmut run
```

## Running only specific targets (wildcards)

```bash
mutmut run "my_module*"
mutmut run "my_module.my_function*"
```

Use this for fast, focused loops while fixing a specific surviving mutant cluster.

## Configuration

Configure in either:

- `setup.cfg` under `[mutmut]`
- `pyproject.toml` under `[tool.mutmut]` (list-style values for path-like options)

### `setup.cfg` example

```ini
[mutmut]
paths_to_mutate=src/
pytest_add_cli_args_test_selection=tests/
do_not_mutate=
    *__tests.py
max_stack_depth=8
mutate_only_covered_lines=true
debug=false
also_copy=
    conftest.py
```

### `pyproject.toml` example

```toml
[tool.mutmut]
paths_to_mutate = ["src/"]
pytest_add_cli_args_test_selection = ["tests/"]
pytest_add_cli_args = ["-x"]
max_stack_depth = 8
mutate_only_covered_lines = true
```

## High-value tuning knobs

### 1) Speed and relevance: `max_stack_depth`

Lower values:
- speed up runs
- reduce incidental-test coupling
- may increase survivors that broader integration paths would kill

### 2) File-level exclusion: `do_not_mutate`

Exclude fixtures/generated files/tests you intentionally do not mutate.

### 3) Coverage-gated mutation: `mutate_only_covered_lines=true`

Uses coverage signal to mutate only executed lines for finer-grained filtering.

### 4) pytest argument control

- `pytest_add_cli_args_test_selection`: selection/deselection flags
- `pytest_add_cli_args`: other pytest flags/config overrides

## Type-checker filtering (advanced)

`mutmut` can filter invalid mutants using mypy or pyrefly JSON output:

```ini
# pyrefly
type_check_command = ['pyrefly', 'check', '--output-format=json']

# mypy
type_check_command = ['mypy', 'your_package', '--output', 'json']
```

Important caveats from docs:

- This can reduce noise/perf cost, but may hide relevant test weaknesses.
- Supported type checkers: **mypy** and **pyrefly**.
- `pyright`/`ty` are not supported for this mapping due to class-wide type-break effects.

## Suppressing known non-actionable mutations

Use inline pragma:

```python
VERSION = "1.2.3"  # pragma: no mutate
```

Use this sparingly for truly low-value lines (for example, version constants).

## Applying mutants to disk

From TUI or CLI:

```bash
mutmut apply <mutant>
```

Always commit your working tree first. Applying mutants modifies source on disk.

## pre-commit integration

No official `mutmut` pre-commit hook repository is documented in upstream docs.

If a team still wants mutation checks in pre-commit, use a **local** hook (usually scoped/manual because full mutation runs are expensive):

```yaml
repos:
  - repo: local
    hooks:
      - id: mutmut-targeted
        name: mutmut targeted run
        entry: mutmut run "my_module*"
        language: system
        pass_filenames: false
```

## Usage examples (input -> expected output)

### Example 1: Basic quality pass

- Input: "Check whether my tests really verify behavior in `src/`."
- Command:
  ```bash
  mutmut run
  ```
- Expected output:
  - Mutants generated/tested.
  - Survivors available for triage in `mutmut browse`.

### Example 2: Focused fix loop

- Input: "Only mutate my parser function while I improve tests."
- Command:
  ```bash
  mutmut run "mypkg.parser.parse_*"
  ```
- Expected output:
  - Only matching target region is exercised, giving faster feedback.

### Example 3: Use coverage + stack depth tuning

- Input: "Mutation runs are too noisy and slow in this monorepo."
- Config:
  ```ini
  mutate_only_covered_lines=true
  max_stack_depth=8
  ```
- Expected output:
  - Fewer incidental test executions and more actionable survivors.

## Troubleshooting

- If installs fail with `libcst`/Rust errors, install Rust toolchain and retry.
- If mutation scope is wrong, explicitly set `paths_to_mutate`.
- If runs are too slow, narrow target with wildcard and tune `max_stack_depth`.
- If too many irrelevant survivors, evaluate `do_not_mutate`, line coverage filtering, and test selection args.

## Practical guidance for an AI agent

When using this skill for a user request:

1. Start with `mutmut run` on a narrow scope if repo is large.
2. Inspect survivors in `mutmut browse`.
3. Propose targeted test improvements for each survivor class.
4. Rerun only relevant module/function wildcards for fast iteration.
5. Escalate to full run once focused areas are green.

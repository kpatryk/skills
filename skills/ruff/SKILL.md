---
name: ruff
description: |
  Expert guidance for ruff — the extremely fast Python linter and formatter written in Rust. Use this skill whenever the user mentions ruff, wants to lint or format Python code, asks about pyproject.toml linting config, wants to migrate from flake8/black/isort/pylint to a single tool, wants to set up pre-commit hooks for Python quality, asks about fixing unused imports or style violations, or needs to configure or debug ruff rules. Also trigger when the user asks about Python code quality tooling in general, since ruff is almost always the right recommendation.
---

# ruff

Ruff is an extremely fast Python linter and code formatter written in Rust. It replaces Flake8 (+ dozens of plugins), Black, isort, pydocstyle, pyupgrade, autoflake, and more — 10–100× faster than any individual tool, with a single configuration file.

Key facts:
- `ruff format` produces **>99.9% identical output** to Black on Black-formatted code — it's a true drop-in replacement
- Supports **800+ lint rules** including re-implementations of flake8-bugbear, isort, pydocstyle, pyupgrade, and more
- Built-in caching, watch mode, and editor LSP support

**Docs:** https://docs.astral.sh/ruff/

---

## Core Commands

```bash
ruff check .                    # Lint all Python files in current directory
ruff check --fix .              # Lint and auto-fix all safe fixable violations
ruff check --fix --unsafe-fixes # Also apply unsafe fixes (may change runtime behavior)
ruff check --watch .            # Lint in watch mode (re-runs on file change)
ruff format .                   # Format all Python files (Black-compatible)
ruff format --check .           # Check formatting without writing changes (CI-friendly)
ruff check --select E,F,I .     # Only run specific rule categories
ruff check --ignore E501 .      # Ignore specific rules
ruff check path/to/file.py      # Lint a single file
ruff check --show-fixes .       # Preview what --fix would change
ruff rule F401                  # Show docs for a specific rule
ruff linter                     # List all available linters/prefixes
```

---

## Installation

```bash
# Recommended (fastest, globally available)
uv tool install ruff@latest

# Add to a project as dev dependency
uv add --dev ruff

# pip / pipx
pip install ruff
pipx install ruff

# macOS
brew install ruff

# Zero-install (run directly via uvx)
uvx ruff check .
uvx ruff format .
```

---

## Configuration

Ruff reads config from `pyproject.toml`, `ruff.toml`, or `.ruff.toml`. The `[tool.ruff]` table in pyproject.toml is the standard location for projects that already use that file.

### Recommended starter config (pyproject.toml)

```toml
[tool.ruff]
line-length = 88          # Match Black's default
target-version = "py311"  # Minimum Python version to target

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "F",    # Pyflakes (undefined names, unused imports, etc.)
    "UP",   # pyupgrade (modernize syntax)
    "B",    # flake8-bugbear (likely bugs and design issues)
    "SIM",  # flake8-simplify
    "I",    # isort (import sorting)
]
ignore = [
    "E501",  # line too long — let the formatter handle this
]
fixable = ["ALL"]
unfixable = []

[tool.ruff.lint.per-file-ignores]
"__init__.py" = ["F401"]          # Allow re-exports in __init__.py
"tests/**/*.py" = ["S101", "ANN"] # Allow assert, skip type annotations in tests

[tool.ruff.format]
quote-style = "double"     # Like Black
indent-style = "space"     # Like Black
skip-magic-trailing-comma = false  # Respect trailing commas
docstring-code-format = true       # Format code blocks in docstrings
```

### ruff.toml (standalone)

```toml
line-length = 88
target-version = "py311"

[lint]
select = ["E", "F", "UP", "B", "SIM", "I"]
ignore = ["E501"]
fixable = ["ALL"]

[lint.per-file-ignores]
"__init__.py" = ["F401"]
"tests/**/*.py" = ["S101"]

[format]
quote-style = "double"
docstring-code-format = true
```

---

## Rule Categories (the most important ones)

| Prefix | Source | What it catches |
|--------|--------|-----------------|
| `E` | pycodestyle | Style errors (indentation, whitespace, etc.) |
| `W` | pycodestyle | Style warnings |
| `F` | Pyflakes | Undefined names, unused imports, unused variables |
| `I` | isort | Import sort order |
| `N` | pep8-naming | Naming conventions (classes, functions, vars) |
| `D` | pydocstyle | Docstring conventions |
| `UP` | pyupgrade | Use modern Python syntax (f-strings, `X \| Y` types) |
| `B` | flake8-bugbear | Likely bugs and bad design |
| `SIM` | flake8-simplify | Simplify complex expressions |
| `ANN` | flake8-annotations | Missing type annotations |
| `S` | flake8-bandit | Security issues |
| `C90` | mccabe | Cyclomatic complexity |
| `RUF` | Ruff-native | Ruff's own rules |
| `PT` | flake8-pytest-style | pytest best practices |
| `TCH` | flake8-type-checking | TYPE_CHECKING guard improvements |
| `ERA` | eradicate | Commented-out code |
| `FAST` | FastAPI | FastAPI-specific issues |

Use `ruff rule <CODE>` to get documentation for any individual rule.

---

## Fix Safety

Ruff distinguishes **safe** fixes (preserve behavior) from **unsafe** fixes (may alter behavior):

```bash
ruff check --fix .              # Only safe fixes (default)
ruff check --fix --unsafe-fixes # Safe + unsafe fixes
ruff check --unsafe-fixes .     # Show unsafe fixes without applying
```

Per-rule fix safety can be adjusted in config:
```toml
[tool.ruff.lint]
extend-safe-fixes = ["UP034"]   # Promote to safe
extend-unsafe-fixes = ["F601"]  # Demote to unsafe
```

---

## Suppressing Violations

```python
# Suppress a specific rule on one line
x = 1  # noqa: F841

# Suppress multiple rules on one line
i = 1  # noqa: E741, F841

# Suppress all rules on one line (avoid overusing this)
x = 1  # noqa

# Suppress across a range (file-level at top)
# ruff: noqa: E501
```

---

## Pre-commit Integration

Ruff has official pre-commit hooks. The linter hook must come **before** the formatter hook, and before any other formatters (Black, isort).

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.11.0   # Pin to a specific version
    hooks:
      - id: ruff-check          # Linter
        args: [--fix]           # Auto-fix safe violations on commit
      - id: ruff-format         # Formatter
```

To exclude Jupyter notebooks:
```yaml
      - id: ruff-check
        types_or: [python, pyi]
        args: [--fix]
      - id: ruff-format
        types_or: [python, pyi]
```

Find the latest version at: https://github.com/astral-sh/ruff-pre-commit/releases

---

## GitHub Actions Integration

```yaml
# .github/workflows/lint.yml
name: Lint
on: [push, pull_request]
jobs:
  ruff:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/ruff-action@v3   # Official GitHub Action
        with:
          args: "check --output-format=github"
```

Or with pip:
```yaml
      - name: Install ruff
        run: pip install ruff
      - name: Lint
        run: ruff check --output-format=github .
      - name: Format check
        run: ruff format --check .
```

---

## Migrating from Other Tools

### From Flake8 + isort + Black

Ruff replaces all three. Just add `I` to select for import sorting, and ruff format replaces Black.

```bash
# Remove old tools
pip uninstall flake8 black isort

# Add ruff
pip install ruff

# Run ruff to check parity
ruff check .
ruff format .
```

Key differences from Flake8:
- Ruff does NOT enable `W` (warnings) or `C901` (complexity) by default
- The `noqa` syntax is compatible — existing comments work

Key differences from Black:
- `ruff format` is > 99.9% identical output on Black-formatted code
- Ruff supports configuring quote style, indent style, and line endings (Black doesn't)
- Both respect magic trailing commas by default

### From pylint

```toml
[tool.ruff.lint]
select = ["E", "F", "W", "C90", "N", "B", "SIM"]
```

---

## Common Pitfalls

**E501 (line too long) conflicts with formatter:** The formatter won't always guarantee lines under the limit (e.g., long strings). Either ignore E501 or set a generous limit:
```toml
ignore = ["E501"]
```

**D203 vs D211 conflict:** These docstring rules are mutually exclusive. Ruff auto-resolves when you use `ALL`, but if you select `D` manually, pick one:
```toml
# One-blank-line before class docstring (D211) vs. one-blank-line required (D203)
select = ["D"]
ignore = ["D203"]  # Keep D211
```

**D212 vs D213 conflict:** Similarly, multi-line summary first/second line:
```toml
ignore = ["D213"]  # Keep D212
```

**`ALL` adds rules on ruff upgrades:** Using `select = ["ALL"]` means upgrading ruff can add new checks. Pin the version in CI or use explicit selects.

**isort config:** If you have existing `[tool.isort]` config, migrate those settings to `[tool.ruff.lint.isort]`. They don't auto-read each other.

**Type-checking imports:** For `TYPE_CHECKING` guard patterns, use the `TCH` rules:
```toml
select = ["TCH"]  # Moves type-only imports under TYPE_CHECKING
```

---

## Tips and Best Practices

1. **Start minimal, expand gradually:** Begin with `select = ["E4", "E7", "E9", "F"]` (the default), then add categories one at a time.

2. **Run formatter + linter together:** Always run both. The linter can create code that needs reformatting after `--fix`:
   ```bash
   ruff check --fix . && ruff format .
   ```

3. **Use `ruff check --diff`** to preview lint changes without applying them.

4. **Use `ruff format --diff`** to preview formatting changes.

5. **Caching:** Ruff has built-in caching (`.ruff_cache/`). Add it to `.gitignore`.

6. **Monorepos:** Ruff supports hierarchical config — parent directory configs cascade into subdirectories. You can override per-subdirectory with a local `ruff.toml`.

7. **Jupyter Notebooks:** Ruff supports `.ipynb` files natively. If you don't want it, use `exclude` in config or `types_or` in pre-commit hooks.

8. **Editor integrations:** Official VS Code extension (`charliermarsh.ruff`), and support in Neovim (via LSP/null-ls), PyCharm, Zed, Helix, and others.

9. **`ruff check --statistics`:** Shows which rules are firing most often — useful for prioritizing fixes.

10. **`ruff check --output-format=json`:** Machine-readable output for CI pipelines and custom tooling.

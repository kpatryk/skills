---
name: pyrefly
description: |
  Expert guidance for Pyrefly — the fast Python type checker and language server by Meta, written in Rust. Use this skill whenever the user mentions pyrefly, wants to type-check Python code, asks about setting up a type checker, wants to configure type checking in pyproject.toml or pyrefly.toml, needs to suppress type errors, wants to migrate from mypy or pyright to a modern alternative, wants to integrate type checking into CI/GitHub Actions, or needs editor/IDE type-checking setup. Also trigger when users ask about Python type annotations, flow types, gradual typing adoption, type inference, or Python LSP setup — pyrefly is the fast modern recommendation worth knowing about.
---

# pyrefly

Pyrefly is a fast Python type checker and language server built by Meta, written in Rust. It provides lightning-fast type checking with full IDE features: code completion, go-to definition, hover types, inlay hints, semantic highlighting, and more. Available on PyPI and as extensions for VSCode, Neovim, JetBrains, Emacs, Helix, and others.

Key facts:
- **Faster** than mypy and pyright — module-level incrementality + parallel checking leverages Rust performance
- **Type inference** for variables and return types (not just explicit annotations)
- **Flow types** — refines static types based on control flow (e.g., after `if x is None` check, `x` is narrowed to non-None)
- **LSP** built in via `pyrefly lsp` — works with any LSP-capable editor
- Weekly releases (Mondays) on PyPI; actively developed by Meta

**Docs:** https://pyrefly.org/en/docs/

---

## Installation

```bash
pip install pyrefly                    # pip
uv add --dev pyrefly                   # uv (recommended, adds as dev dependency)
poetry add --group dev pyrefly         # poetry
conda install pyrefly                  # conda
uvx pyrefly check .                    # zero-install via uvx
```

---

## Core Commands

```bash
pyrefly init                           # Initialize config; migrates from mypy/pyright automatically
pyrefly check                          # Type-check the whole project (uses config file)
pyrefly check --summarize-errors       # Check with a summary of error categories
pyrefly check src/ tests/             # Check specific files or directories
pyrefly suppress                       # Add # pyrefly: ignore to all erroring lines
pyrefly suppress --remove-unused       # Remove ignore comments that are no longer needed
pyrefly lsp                            # Start language server (for editor integration)
pyrefly dump-config [file.py]          # Debug config discovery and effective settings
```

### Key flags

```bash
--config / -c <path>              # Explicitly specify config file
--python-version 3.12             # Override Python version for sys.version checks
--python-platform linux           # Override sys.platform assumption
--output-format github            # Emit GitHub Actions workflow commands for inline PR annotations
--output-format json              # JSON output for programmatic consumption
--summarize-errors                # Show summary of error categories at the end
--suppress-errors                 # Add # pyrefly: ignore to all erroring lines (same as pyrefly suppress)
--remove-unused-ignores           # Remove stale # pyrefly: ignore comments
--baseline <path>                 # Use baseline JSON to suppress pre-existing errors
--update-baseline                 # Regenerate the baseline file
--min-severity warn               # Also show warn/info diagnostics (default: error only)
--search-path <dir>               # Add import resolution root (like mypy_path / extraPaths)
--project-excludes <glob>         # Exclude file patterns
--ignore-missing-imports <module> # Treat specific missing module as Any
--ignore-errors-in-generated-code # Skip files containing '@generated'
--permissive-ignores              # Also respect # pyre-ignore, # mypy: ignore, etc.
--check-unannotated-defs          # Type-check unannotated function bodies (default: true)
```

---

## Configuration

Pyrefly reads config from `pyrefly.toml` (top-level keys) or `pyproject.toml` (`[tool.pyrefly]` section). It's found automatically by walking up the directory tree — also detects `setup.py`, `mypy.ini`, and `pyrightconfig.json` as project root markers.

**Precedence:** CLI flags > config file > Pyrefly defaults

### Starter config (pyproject.toml)

```toml
[tool.pyrefly]
# Directories/globs to type-check
project-includes = ["src", "tests"]

# Python version for sys.version checks
python-version = "3.12"

# Silence errors in @generated files
ignore-errors-in-generated-code = true

# Per-error-code severity: "error" | "warn" | "ignore" | false (same as ignore)
[tool.pyrefly.errors]
# implicit-any = "warn"    # enable to enforce fully-annotated codebase
# deprecated = "warn"      # already "warn" by default
```

### Full pyrefly.toml reference

```toml
project-includes = ["src/**/*.py", "tests/**/*.py"]
project-excludes = ["src/generated/**"]      # Added on top of defaults (node_modules, venv, etc.)

python-version = "3.12"
python-platform = "linux"

# Import resolution roots (like mypy_path / Pyright's extraPaths)
search-path = ["src"]

# Treat these missing modules as Any (only when not found)
ignore-missing-imports = ["boto3", "mypy_boto3_*"]

# Always treat these as Any (even when found)
# replace-imports-with-any = ["legacy_module"]

ignore-errors-in-generated-code = true

# Also respect # pyre-ignore and # mypy: ignore comments
permissive-ignores = false

# Show warn/info diagnostics too (default: "error")
min-severity = "error"

# Output format for pyrefly check
output-format = "full-text"   # full-text | min-text | json | github | omit-errors

# Baseline file for suppressing pre-existing errors (experimental)
# baseline = "pyrefly-baseline.json"

# Type-check bodies of unannotated functions (false = mypy's old default)
check-unannotated-defs = true

# Return type inference: "checked" | "annotated" | "never"
infer-return-types = "checked"

# Infer container types from first use (true = mypy-like, false = Pyright-like)
infer-with-first-use = true

[errors]
bad-param-name-override = "warn"   # Downgrade from error to warning
implicit-any = "warn"              # Off by default; enable for strict codebases

# Per-directory overrides (sub-config)
[[sub-config]]
matches = ["tests/**"]
check-unannotated-defs = false     # More lenient in tests

[[sub-config]]
matches = ["src/legacy/**"]
check-unannotated-defs = false
ignore-missing-imports = ["*"]
```

### Config discovery

Pyrefly walks up from the current directory looking for:
1. `pyrefly.toml` (parsed for config)
2. `pyproject.toml` with `[tool.pyrefly]` (parsed for config)
3. `setup.py`, `mypy.ini`, `pyrightconfig.json` (used as project root markers only)

Use `-c path/to/pyrefly.toml` to bypass auto-discovery.

---

## Error Suppression

```python
# Suppress all errors on this line
x: str = 1  # pyrefly: ignore

# Suppress specific error code
x: str = 1  # pyrefly: ignore[bad-assignment]

# Standard type: ignore (also respected)
x: str = 1  # type: ignore

# Suppress ALL errors in an entire file (put near top of file)
# pyrefly: ignore-errors
```

### Bulk suppression workflow (onboarding existing codebases)

```bash
# Step 1: Mark all existing errors as ignored
pyrefly suppress

# Step 2: Run your formatter to normalize comment placement
black . && isort .

# Step 3: Remove stale ignores that are no longer needed
pyrefly suppress --remove-unused

# Repeat until clean, then add to CI
```

### Baseline files (experimental)

Baseline files suppress pre-existing errors without adding inline comments — useful for large migrations or version upgrades where you want clean diffs:

```bash
# Generate baseline from all current errors
pyrefly check --baseline="pyrefly-baseline.json" --update-baseline

# Subsequent checks only report newly-introduced errors
pyrefly check --baseline="pyrefly-baseline.json"
```

```toml
# pyproject.toml — persist baseline in config
[tool.pyrefly]
baseline = "pyrefly-baseline.json"
```

---

## Common Error Codes

| Code | Meaning |
|------|---------|
| `bad-assignment` | Value incompatible with variable's type annotation |
| `bad-argument-type` | Wrong type passed to a function argument |
| `bad-argument-count` | Too many or too few positional arguments |
| `missing-argument` | Required argument not provided |
| `bad-return` | Return value incompatible with declared return type |
| `bad-override` | Subclass method violates Liskov Substitution Principle |
| `missing-import` | Module cannot be found |
| `invalid-annotation` | Incorrect usage of `Final`, `ClassVar`, `TypeVar`, etc. |
| `annotation-mismatch` | Same variable annotated with different types in different branches |
| `bad-unpacking` | Unpacking into wrong number of variables |
| `bad-specialization` | Generic type specialized with wrong number/type arguments |
| `deprecated` | Usage of a `@deprecated` class or function (severity: warn) |
| `implicit-any` | Implicit `Any` inferred (off by default; enable for strict codebases) |
| `implicit-import` | Submodule accessed without explicit import (severity: warn) |
| `reveal-type` | Informational — shows inferred type of an expression |

Full list: https://pyrefly.org/en/docs/error-kinds/

---

## Gradual Typing Adoption

For adding Pyrefly to an existing untyped codebase, start permissive and tighten over time:

1. **`pyrefly init`** — initializes config and auto-migrates from mypy/pyright if present
2. **`pyrefly suppress`** — silences all existing errors with `# pyrefly: ignore`
3. **Add to CI** — any new code must pass type checks (see CI section below)
4. **Fix suppressed errors** gradually, module by module
5. **Use `sub-config`** to enforce different strictness in different parts of the codebase

```toml
# pyproject.toml — allow lenient checking in legacy dirs
[[tool.pyrefly.sub-config]]
matches = ["src/legacy/**"]
check-unannotated-defs = false

[[tool.pyrefly.sub-config]]
matches = ["src/new_module/**"]
# strict defaults apply here — no overrides needed
```

---

## CI Integration (GitHub Actions)

```yaml
# .github/workflows/typecheck.yml
name: Pyrefly Type Check
on:
  pull_request:
    branches: [main]
  workflow_dispatch:

jobs:
  typecheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - name: Install dependencies
        run: |
          python -m venv .venv
          source .venv/bin/activate
          pip install -r requirements-dev.txt
      - name: Install Pyrefly
        run: pip install pyrefly
      - name: Run Pyrefly
        # --output-format=github emits inline PR annotations
        run: pyrefly check --output-format=github
```

You can also drop `pyrefly check` into an existing workflow that already sets up your Python environment — the `pyproject.toml` / `pyrefly.toml` config is detected automatically.

---

## Pre-commit Integration

Using the official [facebook/pyrefly-pre-commit](https://github.com/facebook/pyrefly-pre-commit) hook:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/facebook/pyrefly-pre-commit
    rev: v0.x.x    # pin to latest release
    hooks:
      - id: pyrefly
```

---

## IDE / Editor Integration

### VSCode, Cursor, Windsurf, Kiro
Install the [Pyrefly extension](https://marketplace.visualstudio.com/items?itemName=meta.pyrefly) from the marketplace.

Useful settings:
```json
{
  "python.pyrefly.displayTypeErrors": "force-on",
  "python.pyrefly.diagnosticMode": "workspace"
}
```

### Neovim (0.11+)
```lua
-- Via Mason (recommended)
require("mason-lspconfig").setup({ ensure_installed = { "pyrefly" } })
vim.lsp.enable({"pyrefly"})

-- Or with custom command (e.g., for uv-installed pyrefly)
vim.lsp.config('pyrefly', { cmd = { 'uvx', 'pyrefly', 'lsp' } })
```

### JetBrains / PyCharm
Settings → Python → Tools → Pyrefly → Enable checkbox

### Emacs (eglot, built-in since Emacs 29)
```elisp
(add-to-list 'eglot-server-programs
  '((python-ts-mode python-mode) . ("pyrefly" "lsp")))
```

### Helix
```toml
# languages.toml
[language-server.pyrefly]
command = "pyrefly"
args = ["lsp"]

[[language]]
name = "python"
language-servers = ["pyrefly"]
```

### Vim + coc.nvim
```json
"languageserver": {
  "pyrefly": {
    "command": "pyrefly",
    "args": ["lsp"],
    "filetypes": ["python"],
    "rootPatterns": ["pyrefly.toml", "pyproject.toml", ".git"]
  }
}
```

---

## Comparison with mypy / pyright

**vs mypy:**
- Pyrefly is significantly faster (Rust + module-level incrementality)
- Pyrefly infers return types by default; mypy traditionally requires explicit annotations
- `check-unannotated-defs = false` mimics mypy's old default behavior
- `permissive-ignores = true` makes Pyrefly respect existing `# type: ignore` comments
- `pyrefly init` auto-migrates `mypy.ini` / `[tool.mypy]` configuration

**vs pyright:**
- Both are fast; Pyrefly uses Rust, Pyright uses TypeScript
- `infer-with-first-use = false` makes container type inference behave like Pyright (`list[Any]` vs inferring from first use)
- `pyrefly init` auto-migrates `pyrightconfig.json`
- Both support the LSP; Pyright's LSP is Pylance in VSCode

**Type system support:** PEP 484, 526, 544 (Protocols), 589 (TypedDict), 604 (X | Y union syntax), 612 (ParamSpec), 673 (Self), 675 (LiteralString), 695 (type aliases), and more.

---

## Type Checking Concepts

### Flow types (type narrowing)
```python
x: int | None = get_value()
if x is not None:
    print(x + 1)   # x is narrowed to int — no error

def f(s: str | None) -> str:
    if s is None:
        return ""
    return s.upper()  # s: str here, not str | None
```

### Type inference
```python
def process(items):       # items: Any (no annotation = Any)
    return len(items)     # return type inferred as int

xs = []                   # inferred as list[int] from first use
xs.append(1)              # ok
xs.append("two")          # error: str not assignable to int
```

### Using `reveal_type` for debugging
```python
from typing import reveal_type
x = [1, 2, 3]
reveal_type(x)   # Revealed type: list[int]
```

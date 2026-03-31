---
name: ty
description: |
  Expert guidance for ty — the extremely fast Python type checker written in Rust by Astral (makers of ruff and uv). Currently in beta. Use this skill whenever the user mentions ty, wants to type-check Python code, asks about Python type checking, wants to migrate from mypy or Pyright, needs to configure type checking rules, wants to integrate a type checker into their project, asks about type checking performance, or needs help with type checking errors and diagnostics. Also trigger when the user asks about fast Python tooling or Astral's tools in general.
---

# ty

ty is an extremely fast Python type checker and language server written in Rust. It's backed by Astral, the creators of uv and Ruff. ty is currently in **beta** with 0.0.x versioning — breaking changes may occur between versions.

**Key highlights:**
- 10x–100x faster than mypy and Pyright
- Comprehensive diagnostics with rich contextual information
- Language server (LSP) with code navigation, completions, auto-import, inlay hints
- Fine-grained incremental analysis for fast IDE updates
- Designed for adoption: supports redeclarations, partially typed code, and gradual typing
- Editor integrations: VS Code, PyCharm, Neovim, and more

**Docs:** https://docs.astral.sh/ty/

---

## Quick Start

Run type checking without installation:
```bash
uvx ty check                 # Check all Python files in current directory
uvx ty check path/to/file.py # Check a specific file
uvx ty check --watch .       # Watch mode — re-runs on file changes
```

Or start a language server for editor integration:
```bash
uvx ty server                # Start LSP server on stdin/stdout
```

**Online playground:** Try ty in your browser at https://play.ty.dev

---

## Installation

### Add to project (recommended)
```bash
# Using uv (recommended)
uv add --dev ty

# Then use it
uv run ty check

# Or upgrade
uv lock --upgrade-package ty
```

### Global installation
```bash
# Install globally with uv
uv tool install ty@latest

# Or with pip / pipx
pip install ty
pipx install ty

# Or via mise
mise install ty
```

### Standalone installer
```bash
# macOS / Linux
curl -LsSf https://astral.sh/ty/install.sh | sh

# Specify version
curl -LsSf https://astral.sh/ty/0.0.26/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/ty/install.ps1 | iex"
```

### Docker
```dockerfile
COPY --from=ghcr.io/astral-sh/ty:latest /ty /bin/
```

Available tags: `ghcr.io/astral-sh/ty:latest`, `ghcr.io/astral-sh/ty:0.0.26`, `ghcr.io/astral-sh/ty:0.0`

---

## Core Commands

```bash
ty check [FILES/DIRS]         # Type-check Python files (default: all in cwd)
ty check --watch .            # Watch mode — re-runs on file changes
ty check --python /path/to/python  # Specify Python interpreter
ty check --python-version 3.12 # Target specific Python version
ty check --config-file ty.toml # Use specific config file
ty check --output-format json  # Machine-readable JSON output
ty check --output-format text  # Human-readable output (default)
ty check --exclude '*.pyi' .   # Exclude files by pattern
ty check --select rule1,rule2 . # Only check specific rules
ty check --ignore rule1,rule2 . # Ignore specific rules
ty server                      # Start LSP server for editor integration
ty generate-shell-completion bash # Generate shell completions
```

---

## Configuration

ty reads from `pyproject.toml` (under `[tool.ty]`) or `ty.toml`. Configuration is optional — ty works out-of-the-box on most projects.

### Minimal config (pyproject.toml)

```toml
[tool.ty]
# Configuration goes here
```

Or create a dedicated `ty.toml`:

```toml
# Root directories for first-party module resolution
[environment]
root = ["./src", "."]

# Python version and environment
[environment]
python-version = "3.12"
python = ".venv/bin/python3"  # Path to interpreter or venv

# Rule severity configuration
[rules]
possibly-unbound = "warn"       # Warn on possibly-unbound variables
division-by-zero = "error"      # Error on division by zero
invalid-argument-type = "warn"  # Warn on type mismatches
unresolved-import = "error"     # Error on missing imports
```

### Comprehensive config example

```toml
# Environment configuration
[environment]
# Root directories for resolving first-party imports (priority order)
root = ["./src", "./lib", "."]

# Python interpreter or venv path
python = ".venv"

# Target Python version (affects standard library stubs and syntax features)
python-version = "3.12"

# Target platform (win32, darwin, linux, ios, android, all)
python-platform = "darwin"

# Extra module search paths (like mypy's MYPYPATH)
extra-paths = ["./vendor"]

# Path to typeshed for standard library types
typeshed = "/path/to/typeshed"

# Module import handling
[analysis]
# Suppress unresolved-import errors for modules matching these patterns
allowed-unresolved-imports = ["pandas.**", "numpy.**", "!pandas.core"]

# Replace module types with Any (even if found)
replace-imports-with-any = ["sklearn.**"]

# Support type: ignore comments (default: true)
respect-type-ignore-comments = true

# Rule severity (values: ignore, warn, error)
[rules]
all = "warn"                           # Default: all rules as warnings
possibly-unbound = "error"             # Override: specific rules as errors
invalid-argument-type = "warn"
unresolved-import = "error"
division-by-zero = "ignore"

# Per-file rule overrides
[rules.overrides]
"tests/**/*.py" = { all = "warn" }
"*_test.py" = { invalid-argument-type = "ignore" }
```

---

## Rule Categories (Common Types)

| Rule | What it catches |
|------|-----------------|
| `possibly-unbound` | Variables that may be used without assignment |
| `invalid-argument-type` | Passing wrong types to function arguments |
| `possibly-unresolved-reference` | Names that may not be defined |
| `unresolved-import` | Imports that can't be found |
| `division-by-zero` | Obvious division-by-zero errors |
| `unreachable-code` | Code after unconditional returns/raises |
| `unused-variable` | Unused local variables |
| `type-mismatch` | Return type doesn't match annotated type |
| `incompatible-default` | Default argument value type mismatch |

Use the [rules documentation](https://docs.astral.sh/ty/rules/) for the complete list and details on each rule.

---

## Suppressing Errors

### Inline suppression
```python
# Suppress on a single line
x = bad_function()  # ty: ignore[invalid-argument-type]

# Suppress multiple rules
y = other()  # ty: ignore[unresolved-import, possibly-unbound]

# Suppress all rules on line (avoid overusing)
z = something()  # ty: ignore
```

### type: ignore support
By default, ty respects `type: ignore` comments (compatible with mypy/Pyright):
```python
x = bad_call()  # type: ignore
```

Disable this in config if you prefer only `ty: ignore`:
```toml
[analysis]
respect-type-ignore-comments = false
```

### Module-level suppression
At the top of a file:
```python
# ty: ignore-errors
```

This suppresses all errors in the file.

---

## Watch Mode & Development

### Incremental type checking with watch mode
ty uses fine-grained incrementality — it only re-analyzes affected files when you edit:

```bash
ty check --watch .
```

This is excellent for IDE integration. The language server (`ty server`) uses the same incremental engine.

---

## Editor Integration

### VS Code
Install the official extension: **Astral ty** (`astral-sh.astral-python-types`)

The extension automatically runs the `ty` language server and provides:
- Real-time diagnostics
- Code navigation (Go to Definition)
- Completions and auto-imports
- Hover information
- Inlay hints

### PyCharm
1. Go to Settings → Languages & Frameworks → Python → Type Checker
2. Select "ty" from the dropdown
3. Configure the path to the ty binary

### Neovim
Use a plugin like `nvim-lspconfig` to connect to the `ty` language server:
```lua
local lspconfig = require('lspconfig')
lspconfig.ty.setup {}  -- Requires LSP binary
```

Or use `cmp-ty` for completion support.

### Other editors
ty provides an LSP server. Configure your editor to run:
```bash
ty server
```

And point to the language server capabilities. See the [editor integration docs](https://docs.astral.sh/ty/editors/).

---

## Integration with uv

ty integrates seamlessly with **uv**, Astral's fast Python package manager:

```bash
# Install ty in your project
uv add --dev ty

# Type-check using the project environment
uv run ty check

# Type-check in watch mode
uv run ty check --watch .

# Start the language server
uv run ty server
```

When run via `uv run`, ty automatically uses the project's virtual environment for resolving dependencies.

---

## Language Server Protocol (LSP)

The `ty server` command starts an LSP server for editor integration. It provides:

- **Real-time diagnostics** — errors/warnings as you type
- **Code navigation** — Go to Definition, Find References
- **Completions** — Context-aware suggestions with auto-import
- **Hover information** — Type signatures and documentation
- **Inlay hints** — Type annotations inline
- **Code actions** — Quick fixes and refactoring suggestions
- **Auto-import** — Automatically add imports for undefined names
- **Fine-grained incrementality** — Fast updates after edits

Example editor configuration (for generic LSP setup):
```bash
ty server  # Runs on stdin/stdout
```

---

## Type Checking in CI/CD

### GitHub Actions
```yaml
name: Type Check
on: [push, pull_request]
jobs:
  ty:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-astral@v0
        with:
          tool: ty
      - run: ty check --output-format github
```

Or with uv:
```yaml
      - uses: astral-sh/setup-astral@v0
      - run: uv run ty check --output-format github
```

### JSON output for CI pipelines
```bash
ty check --output-format json > results.json
```

This produces machine-readable diagnostics that CI systems can parse.

---

## Configuration File Formats

### pyproject.toml style
```toml
[tool.ty]
# ... configuration
```

### ty.toml style (standalone)
```toml
[environment]
python-version = "3.12"

[rules]
all = "warn"
```

Both are equivalent — use whichever your project prefers. The ty.toml is loaded if present, otherwise ty looks for `[tool.ty]` in pyproject.toml.

---

## Comparison with mypy and Pyright

| Feature | ty | mypy | Pyright |
|---------|-----|------|---------|
| **Speed** | ⚡ 10–100x faster | Baseline | ~2–3x faster than mypy |
| **Incremental** | Yes, fine-grained | Yes, basic | Yes |
| **Rust-based** | ✅ Yes | ❌ Python | ❌ TypeScript |
| **Language Server** | ✅ Yes | ⚠️ Partial | ✅ Yes |
| **Rule configuration** | ✅ Granular | ⚠️ Limited | ✅ Full |
| **Status** | Beta (0.0.x) | Stable | Stable |
| **Feature completeness** | ~70% | ~95% | ~95% |

**Migration notes:**
- `type: ignore` comments work the same way (or disable them in config)
- Error codes are different (ty uses its own system, not mypy's)
- Configuration is simpler than mypy's config file
- Gradual typing and partially-typed code are first-class features

---

## Common Workflows

### Check all Python files
```bash
ty check
```
ty walks the project and checks all `.py` files.

### Check specific file or directory
```bash
ty check src/mymodule.py
ty check tests/
```

### Fix issues (limited support in beta)
Some rules support auto-fixes; check the documentation for which ones. Use `--no-fix` to preview changes without applying:
```bash
# Note: auto-fix support is still developing in ty beta
# For now, rely on manual fixes or other tools
```

### Exclude files or directories
```bash
# Command line
ty check --exclude '*.pyi' --exclude 'build/*' .

# Or in config
# (ty.toml or pyproject.toml)
[tool.ty]
# Configure exclusions (see docs for exact syntax)
```

### Run with specific Python version
```bash
ty check --python-version 3.10 .
```

### JSON output for parsing
```bash
ty check --output-format json
```

---

## Limitations in Beta

- **0.0.x versioning** — Breaking changes may occur between versions
- **Fewer rules than mypy/Pyright** — ty covers ~70% of common cases; if you need every edge case, consider hybrid approaches
- **Limited auto-fix support** — Most fixes require manual changes; ty is primarily a checker, not a formatter
- **Type system features** — Advanced generics, TypeVar constraints, and protocol edge cases may not be fully supported yet
- **Third-party stubs** — py.typed packages are supported, but some legacy packages may need `allowed-unresolved-imports` workarounds

See the [type system support tracking issue](https://github.com/astral-sh/ty/issues/1889) for detailed feature status.

---

## Best Practices for Adoption

1. **Start with the defaults** — ty's default rules are well-balanced. No need to configure much upfront.

2. **Use in watch mode during development** — Combine `ty check --watch` with your editor for real-time feedback:
   ```bash
   ty check --watch .
   ```

3. **Gradual adoption** — You can suppress errors selectively and fix them incrementally:
   ```python
   result = untyped_function()  # ty: ignore[invalid-argument-type]
   ```

4. **Allow unresolved imports temporarily** — When migrating, temporarily suppress errors for untyped dependencies:
   ```toml
   [analysis]
   allowed-unresolved-imports = ["django.**", "requests.**"]
   ```

5. **Combine with uv** — Use `uv add --dev ty` and `uv run ty check` to keep ty in sync with your project environment.

6. **Integrate into CI** — Add `ty check --output-format github` to your CI pipeline so issues are surfaced on PRs.

7. **Don't aim for 100% coverage immediately** — ty is designed for adoption. Start with core files, then expand. Use rule severity to prioritize errors as `warn` before promoting to `error`.

8. **Pin the version** — Since ty is in beta with 0.0.x versioning, pin it in your project:
   ```bash
   uv add --dev ty==0.0.26  # or latest
   ```

9. **Use the language server** — Combine `ty check` in CI with `ty server` for IDE integration. The server's fine-grained incrementality makes development fast.

10. **Reference the rules** — Use `https://docs.astral.sh/ty/rules/` to understand each error. ty's error messages are detailed and actionable.

---

## Troubleshooting

### "Unresolved import" errors for installed packages
**Cause:** ty can't find your Python environment.

**Solution:**
```bash
# Explicitly point to your interpreter
ty check --python /path/to/python .

# Or use uv run to set the environment
uv run ty check .

# Or set VIRTUAL_ENV
export VIRTUAL_ENV=/path/to/venv
ty check
```

### Type checking is slow
**Cause:** Likely the first run before caching, or incremental analysis hasn't kicked in.

**Solution:**
- Use watch mode for development (enables incremental analysis):
  ```bash
  ty check --watch .
  ```
- Subsequent runs are much faster due to ty's fine-grained incrementality

### False positives or odd errors
**Cause:** ty is in beta; some edge cases may not be fully supported.

**Solution:**
- Suppress with `# ty: ignore` temporarily
- Check the [tracking issue](https://github.com/astral-sh/ty/issues/1889) for known limitations
- Report bugs on [GitHub](https://github.com/astral-sh/ty/issues)

### Can't find ty command
**Cause:** Not installed or not in PATH.

**Solution:**
```bash
# Try uvx
uvx ty check .

# Or install globally
uv tool install ty
ty check .

# Or add to project
uv add --dev ty
uv run ty check .
```

---

## Resources

- **Official Docs:** https://docs.astral.sh/ty/
- **GitHub Repository:** https://github.com/astral-sh/ty
- **Online Playground:** https://play.ty.dev
- **Rules Documentation:** https://docs.astral.sh/ty/rules/
- **Type System Features:** https://docs.astral.sh/ty/features/type-system/
- **Language Server Info:** https://docs.astral.sh/ty/features/language-server/
- **Issue Tracker:** https://github.com/astral-sh/ty/issues
- **Discord Community:** https://discord.com/invite/astral-sh

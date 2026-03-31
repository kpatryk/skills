---
name: uv
description: >
  Comprehensive guide for uv — the extremely fast Python package and project manager written in Rust
  by Astral. uv replaces pip, pip-tools, pipx, poetry, pyenv, twine, and virtualenv in a single tool.
  Use this skill whenever the user asks about: managing Python projects or dependencies, installing
  Python packages, creating virtual environments, running Python scripts with dependencies, managing
  Python versions, publishing packages to PyPI, converting from pip/poetry/pipenv to uv, writing
  inline script metadata (PEP 723), using uvx to run tools without installing them, or any question
  involving pyproject.toml, uv.lock, uv.toml, or the `uv` CLI command. Also trigger for questions
  like "how do I set up a Python project", "replace pip with something faster", "manage multiple
  Python versions", or "run a one-off Python script with dependencies".
---

# uv — Fast Python Package & Project Manager

uv is a single Rust-powered binary that replaces: `pip`, `pip-tools`, `pipx`, `poetry`, `pyenv`, `twine`, `virtualenv`. It is 10–100× faster than pip thanks to parallel downloads and a global content-addressable cache.

## Core mental model

| Old tool | uv equivalent |
|---|---|
| `python -m venv` / `virtualenv` | `uv venv` |
| `pip install` | `uv pip install` or `uv add` |
| `pip-compile` | `uv pip compile` |
| `poetry add` / `poetry run` | `uv add` / `uv run` |
| `pyenv install 3.12` | `uv python install 3.12` |
| `pipx run black` | `uvx black` |
| `pipx install black` | `uv tool install black` |

---

## Project management (recommended workflow)

### Create a new project

```bash
uv init my-project              # application (default) — creates main.py
uv init my-lib --lib            # library — creates src/my_lib/__init__.py
uv init my-app --app            # explicit app with __main__.py entry point
uv init my-pkg --package        # packaged app (buildable)
uv init --python 3.12           # pin Python version at init
```

Generated structure:
```
my-project/
├── .gitignore
├── .python-version       ← pins Python for this project
├── README.md
├── pyproject.toml
└── main.py               (or src/my_lib/__init__.py for --lib)
```

### Manage dependencies

```bash
uv add requests                          # add runtime dependency
uv add 'httpx>=0.27'                     # with version constraint
uv add --dev pytest ruff                 # add dev dependencies
uv add --optional docs sphinx            # optional dependency group
uv add --editable ./my-local-package     # editable (local) dependency
uv add git+https://github.com/psf/black # from git
uv add -r requirements.txt              # import from requirements.txt

uv remove requests                       # remove dependency
uv lock --upgrade-package requests       # upgrade one package
uv lock --upgrade                        # upgrade all packages
```

### Sync and run

```bash
uv sync                    # install/update venv to match uv.lock
uv sync --frozen           # sync without updating uv.lock (CI-safe)
uv sync --no-dev           # exclude dev dependencies (production)
uv sync --extra docs       # include optional group

uv run python              # run in project venv (auto-syncs first)
uv run main.py             # run a script in project venv
uv run pytest              # run dev tool inside the venv
uv run --no-project script.py  # skip project install for standalone scripts
uv run --env-file .env cmd # load .env before running (uv doesn't auto-load it)
```

`uv run` automatically creates/updates the venv — no manual activation needed.

### pyproject.toml structure

```toml
[project]
name = "my-project"
version = "0.1.0"
description = "My awesome project"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "httpx>=0.27",
    "pydantic>=2.0",
]

[project.optional-dependencies]
docs = ["sphinx", "sphinx-rtd-theme"]

[dependency-groups]
dev = ["pytest", "ruff", "mypy"]

[project.scripts]
my-cli = "my_project.cli:main"

[tool.uv]
dev-dependencies = ["pytest>=8"]   # alternative to [dependency-groups]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### The lockfile

`uv.lock` is a cross-platform TOML lockfile — commit it to git. It is **not** directly pip-installable; use `uv sync` or `uv pip sync` to install from it.

```bash
uv lock                    # create/refresh lockfile
uv lock --frozen           # verify lockfile is up to date (fails if changes needed)
uv export -o requirements.txt          # export lockfile → requirements.txt
uv export -o pylock.toml               # export to PEP 751 pylock format
```

---

## Scripts with inline metadata (PEP 723)

For self-contained single-file scripts that declare their own dependencies:

```bash
uv init --script fetch_data.py --python 3.12   # create script with inline header
uv add --script fetch_data.py requests rich    # add deps to script metadata
uv run fetch_data.py                           # run with auto-managed deps
uv run --with rich --with requests script.py  # ad-hoc deps without metadata
```

Inline script metadata format (PEP 723):
```python
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "requests<3",
#   "rich>=13",
# ]
# ///

import requests
from rich.pretty import pprint
...
```

uv automatically creates an isolated venv, installs deps, and runs the script — no manual setup.

---

## Tools (uvx / uv tool)

Tools are CLI applications distributed as Python packages. Use `uvx` for one-off runs; `uv tool install` for persistent tools.

> **Key fact**: `uvx` is an alias for `uv tool run`. They are exactly equivalent. `uvx` is just the short, convenient form.

```bash
uvx ruff check .          # same as: uv tool run ruff check .
uv tool run ruff check .  # same as uvx

# One-off (ephemeral, no permanent install)
uvx ruff check .
uvx black --check .
uvx --from httpie http GET https://example.com
uvx ruff@0.6.0 check .                  # pin version with @
uvx ruff@latest check .                 # force latest
uvx --with mkdocs-material mkdocs build # include extra packages

# Persistent install (added to PATH)
uv tool install ruff
uv tool install 'ruff>=0.6'
uv tool install --python 3.12 ruff

uv tool list                   # list installed tools
uv tool upgrade ruff           # upgrade a tool
uv tool upgrade --all          # upgrade all tools
uv tool uninstall ruff         # remove a tool
uv tool run ruff check .       # same as uvx
```

Key distinction: `uvx` / `uv tool run` runs in an isolated env separate from the project. For project-aware tools (pytest, mypy, coverage), use `uv run` instead.

---

## Python version management

uv can download and manage Python interpreters without pyenv.

```bash
uv python install 3.12          # install Python 3.12
uv python install 3.10 3.11 3.12  # install multiple versions
uv python install pypy@3.11     # install PyPy

uv python list                  # list available/installed versions
uv python list --only-installed # list only installed versions
uv python find 3.11             # find path to Python 3.11
uv python pin 3.11              # write .python-version (pins project)
uv python pin --global 3.12     # set global default

uv venv --python 3.12           # create venv with specific Python
uv run --python 3.10 script.py  # run with specific version
```

The `.python-version` file pins the Python version for a directory. Commit it to git.

---

## pip interface (drop-in replacement)

For teams migrating from pip without changing workflows:

```bash
uv pip install requests         # same as pip install
uv pip install -r requirements.txt
uv pip install -e .             # editable install
uv pip uninstall requests
uv pip freeze                   # list installed packages
uv pip list
uv pip show requests
uv pip check                    # verify dependency consistency

uv pip compile requirements.in -o requirements.txt   # like pip-compile
uv pip compile --universal requirements.in           # cross-platform resolution
uv pip sync requirements.txt    # sync venv to requirements.txt exactly

uv venv                         # create .venv in current dir
uv venv --python 3.12 myenv     # named venv with specific Python
```

---

## Workspaces (monorepo)

Workspaces let you manage multiple related packages under one lockfile:

```toml
# workspace root pyproject.toml
[project]
name = "my-app"
version = "0.1.0"
dependencies = ["my-lib"]

[tool.uv.sources]
my-lib = { workspace = true }  # depend on workspace member

[tool.uv.workspace]
members = ["packages/*"]       # glob pattern for members
exclude = ["packages/scratch"] # optional exclusions
```

```bash
uv run --package my-lib pytest   # run in specific workspace member
uv sync --package my-lib         # sync a specific member
```

---

## Build & Publish

```bash
uv build                         # build wheel + sdist in dist/
uv build --wheel                 # wheel only
uv build --sdist                 # sdist only

uv publish                       # publish to PyPI (uses dist/)
uv publish --token $PYPI_TOKEN
uv publish --index-url https://test.pypi.org/legacy/   # test PyPI
```

---

## Cache management

uv uses a global content-addressable cache (shared across projects):

```bash
uv cache dir                    # show cache location
uv cache clean                  # remove all cached data
uv cache prune                  # remove stale/unused entries
```

---

## Environment variables

| Variable | Purpose |
|---|---|
| `UV_PYTHON` | Override Python version (e.g. `3.12`) |
| `UV_PROJECT_ENVIRONMENT` | Custom path for project venv |
| `UV_CACHE_DIR` | Custom cache directory |
| `UV_INDEX_URL` | Primary package index (replaces PyPI) |
| `UV_EXTRA_INDEX_URL` | Additional package index |
| `UV_NO_SYNC` | Skip auto-sync when running `uv run` |
| `UV_FROZEN` | Equivalent to `--frozen` flag globally |
| `UV_SYSTEM_PYTHON` | Allow using system Python |

---

## Common patterns & recipes

### CI/CD (GitHub Actions)
```yaml
- uses: astral-sh/setup-uv@v5
  with:
    uv-version: "latest"
- run: uv sync --frozen --no-dev
- run: uv run pytest
```

### Docker
```dockerfile
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY . .
RUN uv sync --frozen --no-dev
CMD ["uv", "run", "gunicorn", "app:app"]
```

### Migration from pip/requirements.txt
```bash
uv init                         # create pyproject.toml
uv add -r requirements.txt      # import all deps
# uv.lock is now your lockfile — commit it
```

### Migration from Poetry
```bash
uv init --no-readme             # create minimal pyproject.toml
# manually move [tool.poetry.dependencies] → [project.dependencies]
uv lock                         # generate uv.lock
uv sync
```

### Self-update
```bash
uv self update
```

---

## Caveats & gotchas

- `uv.lock` is **not pip-installable** — always use `uv sync` to install from it
- `.env` files are **not auto-loaded** — use `uv run --env-file .env cmd`
- `uvx` runs in isolation from the project; for pytest/mypy use `uv run` instead
- Use `uv sync --frozen` in CI to catch lockfile drift early
- `uv pip install` installs into the **active venv** (or system Python if none active) — prefer `uv add` for project deps
- Don't manually edit `.venv` or `uv.lock`; let uv manage them

---
name: bandit
description: >
  Comprehensive reference for Bandit — the Python AST-based security linter from PyCQA that detects common security vulnerabilities in Python code. Use this skill whenever the user asks about running Bandit scans, interpreting Bandit findings, suppressing false positives with nosec, configuring Bandit via pyproject.toml or bandit.yaml, selecting or skipping specific test IDs (B101–B704), setting up Bandit in CI/CD, generating baselines to track new issues, or integrating Bandit with pre-commit. Trigger on any mention of bandit, Python security scanning, SAST for Python, hardcoded passwords in Python, SQL injection detection, shell injection in Python, pickle deserialization, or insecure Python imports.
---

# Bandit

Bandit is a Python security linter by PyCQA that walks the AST of each file and runs security-focused plugin tests against the nodes. It reports findings with both **severity** and **confidence** levels (LOW / MEDIUM / HIGH).

**Official docs:** https://bandit.readthedocs.io/en/latest/  
**Source:** https://github.com/PyCQA/bandit

## Installation

```bash
pip install bandit                  # core
pip install "bandit[toml]"          # adds pyproject.toml config support
pip install "bandit[baseline]"      # adds bandit-baseline CLI
pip install "bandit[sarif]"         # adds SARIF output formatter
```

## Core usage

```bash
# Recursively scan a project
bandit -r src/

# Scan specific files or glob
bandit app.py utils/*.py

# Read from stdin
cat app.py | bandit -
```

## Common flags

| Flag | Description |
|------|-------------|
| `-r` | Recurse into directories |
| `-l` / `--level` | Minimum severity: use `-l` (LOW+), `-ll` (MEDIUM+), `-lll` (HIGH only) |
| `-i` / `--confidence` | Minimum confidence: `-i` (LOW+), `-ii` (MEDIUM+), `-iii` (HIGH only) |
| `--severity-level LOW\|MEDIUM\|HIGH` | Filter by minimum severity (long form) |
| `--confidence-level LOW\|MEDIUM\|HIGH` | Filter by minimum confidence |
| `-t B101,B307` | Run only these test IDs |
| `-s B101,B311` | Skip these test IDs |
| `-n 3` | Show N lines of code context per finding |
| `-f text\|json\|csv\|xml\|html\|screen\|sarif` | Output format |
| `-o results.json` | Write output to file |
| `-c bandit.yaml` | Use a YAML or TOML config file |
| `--ini .bandit` | Use an INI config file |
| `--exclude tests,venv` | Comma-separated paths to exclude |
| `--baseline baseline.json` | Compare against a baseline; only show new issues |
| `-b baseline.json` | Short form of `--baseline` |
| `-p ShellInjection` | Run a named profile |
| `-q` | Quiet mode (suppress progress output) |
| `-v` | Verbose mode |

## Output formats

```bash
bandit -r src/ -f json -o bandit-results.json
bandit -r src/ -f html -o bandit-report.html
bandit -r src/ -f sarif -o bandit.sarif        # GitHub code scanning
bandit -r src/ -f screen                        # colored terminal output
```

## Severity & confidence filtering

```bash
# Only HIGH severity, any confidence
bandit -r . -lll

# MEDIUM+ severity AND MEDIUM+ confidence
bandit -r . -ll -ii

# HIGH severity and HIGH confidence only
bandit -r . -lll -iii

# Long-form equivalents
bandit -r . --severity-level HIGH --confidence-level HIGH
```

## Selecting / skipping tests

```bash
# Run only specific tests
bandit -r . -t B102,B307,B602

# Skip tests (e.g. skip assert_used in test directories)
bandit -r . -s B101

# Combine: run only B3xx blacklist calls, but skip B311 (random)
bandit -r . -t B301,B302,B303,B304,B305,B306,B307,B308,B310,B311 -s B311
```

## Configuration files

### pyproject.toml (recommended)

```toml
[tool.bandit]
exclude_dirs = ["tests", "venv", ".tox"]
skips = ["B101", "B311"]
tests = []   # empty = run all (after applying skips)

[tool.bandit.any_other_function_with_shell_equals_true]
shell = ["os.system", "os.popen"]
```

Run with: `bandit -c pyproject.toml -r .`

### bandit.yaml

```yaml
exclude_dirs: ['tests', 'path/to/file']
tests: ['B201', 'B301']
skips: ['B101', 'B601']
```

Run with: `bandit -c bandit.yaml -r .`

### .bandit (INI — auto-detected when using `-r`)

```ini
[bandit]
targets = src,lib
exclude = tests,build
skips = B101,B311
tests = B201,B301
```

Bandit auto-discovers `.bandit` only when invoked with `-r`. For other filenames: `bandit --ini tox.ini`.

### Generate a starter config

```bash
bandit-config-generator > bandit.yaml
bandit-config-generator -t B201,B301 -s B101 > bandit.yaml
```

## Inline suppression with `# nosec`

Mark a line to suppress all findings on it:

```python
self.proc = subprocess.Popen('/bin/sh', shell=True)  # nosec
```

Suppress specific test IDs (other findings on the line are still reported):

```python
self.proc = subprocess.Popen('/bin/ls *', shell=True)  # nosec B602, B607
```

Use the test name instead of ID:

```python
assert yaml.load("{}") == []  # nosec assert_used
```

**Best practice:** Always add a comment explaining *why* the suppression is justified:

```python
# The hash here is not in a security context — collisions are acceptable.
the_hash = md5(data).hexdigest()  # nosec B303
```

## Baseline workflow

Use a baseline to track only *new* issues introduced since a reference point. Useful in CI to avoid noise from pre-existing findings.

```bash
# 1. Generate a baseline from the current codebase (JSON format required)
bandit -r . -f json -o baseline.json

# 2. Commit baseline.json to the repo

# 3. In CI, compare against baseline — only new issues cause failure
bandit -r . --baseline baseline.json
```

Commit the baseline when you intentionally accept existing issues.

## Pre-commit integration

Add to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/PyCQA/bandit
    rev: '1.8.5'   # pin to a real release tag
    hooks:
      - id: bandit
```

With a pyproject.toml config:

```yaml
repos:
  - repo: https://github.com/PyCQA/bandit
    rev: '1.8.5'
    hooks:
      - id: bandit
        args: ["-c", "pyproject.toml"]
        additional_dependencies: ["bandit[toml]"]
```

## CI/CD example (GitHub Actions)

```yaml
- name: Run Bandit
  run: |
    pip install "bandit[toml]"
    bandit -r src/ -c pyproject.toml -f json -o bandit-results.json
  continue-on-error: false
```

For GitHub code scanning (SARIF upload):

```yaml
- name: Run Bandit (SARIF)
  run: |
    pip install "bandit[sarif]"
    bandit -r . -f sarif -o bandit.sarif

- name: Upload SARIF
  uses: github/codeql-action/upload-sarif@v3
  with:
    sarif_file: bandit.sarif
```

## Key plugin test IDs

See `references/plugins.md` for the full catalogue. Critical ones to know:

| ID | Name | What it catches | Severity |
|----|------|----------------|----------|
| B101 | assert_used | `assert` statements (stripped in `-O` mode) | LOW |
| B102 | exec_used | `exec()` built-in | MEDIUM |
| B104 | hardcoded_bind_all_interfaces | `0.0.0.0` as bind address | MEDIUM |
| B105/6/7 | hardcoded_password_* | Hardcoded passwords in strings/args/defaults | LOW |
| B110 | try_except_pass | `except: pass` silences errors | LOW |
| B201 | flask_debug_true | `app.run(debug=True)` | HIGH |
| B301 | pickle | `pickle.loads`, `dill`, `shelve`, `jsonpickle` | MEDIUM |
| B303 | md5 | `hashlib.md5`, `hashlib.sha1` (non-security context) | MEDIUM |
| B307 | eval | `eval()` usage | MEDIUM |
| B311 | random | `random.random()` etc. for security use | LOW |
| B324 | hashlib | `hashlib.new('md5', ...)` with insecure algo | MEDIUM |
| B401 | import_telnetlib | `import telnetlib` | HIGH |
| B501 | request_with_no_cert_validation | `verify=False` in requests | HIGH |
| B506 | yaml_load | `yaml.load()` without Loader | MEDIUM |
| B602 | subprocess_popen_with_shell_true | `subprocess.Popen(..., shell=True)` | HIGH |
| B608 | hardcoded_sql_expressions | String-formatted SQL queries | MEDIUM |
| B701 | jinja2_autoescape_false | Jinja2 autoescape disabled | HIGH |

## Common pitfalls & how to handle them

### B101 false positives in test files
`assert` is essential in pytest. Skip B101 for the test directory:
```bash
bandit -r . -s B101    # skip globally
# or exclude the tests dir entirely
bandit -r src/         # only scan source, not tests
```
Or in config: `skips = ["B101"]`

### B311 (random) in non-security contexts
`random` is fine for simulations, games, shuffling display order. Suppress with `# nosec B311` and explain why. Use `secrets` module for tokens, passwords, session IDs.

### B506 (yaml.load)
Always use `yaml.safe_load()` or `yaml.load(data, Loader=yaml.SafeLoader)` instead of bare `yaml.load()`.

### B602 / B603 (subprocess shell)
Prefer `subprocess.run(["cmd", "arg"])` (list form, `shell=False`) over `subprocess.run("cmd arg", shell=True)`. Shell=True + user input = shell injection.

### B324 vs B303
B303 fires on `hashlib.md5()` / `hashlib.sha1()`. B324 fires on `hashlib.new('md5')`. Both flag insecure hashes. For non-security uses (checksums, cache keys), suppress with `# nosec B303` or `# nosec B324`.

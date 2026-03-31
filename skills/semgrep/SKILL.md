---
name: semgrep
description: >
  Comprehensive reference for Semgrep — the open-source static analysis tool that finds bugs, enforces code patterns, and detects security vulnerabilities across 30+ languages using semantic pattern matching. Use this skill whenever the user asks about running Semgrep scans, writing custom Semgrep rules, configuring Semgrep in CI/CD, interpreting scan results, using the Semgrep registry, setting up pre-commit hooks, or understanding Semgrep's YAML rule syntax. Trigger on any mention of semgrep, static analysis rules, custom SAST rules, code pattern matching, security scanning with semgrep, or semgrep integration.
---

# Semgrep

Semgrep is a fast, open-source static analysis tool that finds bugs, security issues, and code quality problems by matching code patterns the way a developer thinks about code — not as plain text or AST dumps, but as structured code with semantic understanding. It supports 30+ languages and requires no compilation.

**Official docs:** https://semgrep.dev/docs/

## Installation

```bash
# macOS
brew install semgrep

# pip (any platform)
python3 -m pip install semgrep

# confirm
semgrep --version
```

## Core concepts

Semgrep works by matching **patterns** against an abstract syntax tree (AST), not raw text. This means `foo(1, 2)` and `foo( 1,  2 )` are equivalent. Patterns can include:

- **Metavariables** (`$X`, `$VAR`) — match any expression and bind it for reuse
- **Ellipsis** (`...`) — match any sequence of arguments, statements, or characters
- **Typed metavariables** (`$TYPE $VAR`) — language-specific type constraints

---

## Running scans

### Quick start (recommended)

```bash
# Scan current directory with auto-selected community rules
semgrep scan --config auto

# Scan a specific path
semgrep scan --config auto src/

# Use a registry ruleset
semgrep scan --config p/python src/
semgrep scan --config p/security-audit .
semgrep scan --config p/owasp-top-ten .
semgrep scan --config p/javascript .
```

### Common scan flags

| Flag | Description |
|------|-------------|
| `-c / --config` | Rules source: `auto`, `p/<ruleset>`, path to YAML, or URL |
| `-e / --pattern` | One-shot pattern (ephemeral rule); requires `--lang` |
| `-l / --lang` | Language for `--pattern` scans (e.g. `python`, `js`, `go`) |
| `--json` | Machine-readable JSON output |
| `--sarif` | SARIF format (used by GitHub code scanning) |
| `-o / --output` | Write results to a file instead of stdout |
| `--severity` | Filter: `ERROR`, `WARNING`, `INFO` |
| `--exclude` | Glob patterns to skip (e.g. `--exclude='*.min.js'`) |
| `--include` | Restrict to matching paths |
| `--no-git-ignore` | Scan gitignored files too |
| `--timeout` | Per-file timeout in seconds (default 5) |
| `--metrics` | `auto` / `on` / `off` — telemetry control |
| `-j / --jobs` | Parallelism (default: ~85% of logical cores) |
| `-v / --verbose` | Show which rules are running, parse errors, etc. |
| `--dataflow-traces` | Show how tainted data reaches findings (SARIF/text) |
| `--autofix` | Apply `fix:` patches from rules automatically |

### Ephemeral (one-shot) patterns

Great for quick checks without writing a YAML file:

```bash
# Find self-comparisons (likely bugs)
semgrep scan -e '$X == $X' --lang=python .

# Find any os.system call
semgrep scan -e 'os.system(...)' --lang=python .

# Find requests.get with verify=False
semgrep scan -e 'requests.get(..., verify=False, ...)' --lang=python .
```

### Multiple configs at once

```bash
semgrep scan --config p/python --config rules/my-custom.yaml src/
```

### Output to file

```bash
semgrep scan --config auto --json -o results.json .
semgrep scan --config auto --sarif -o results.sarif .
```

---

## Popular registry rulesets

Find rulesets at https://semgrep.dev/r

| Config | What it scans |
|--------|---------------|
| `auto` | Auto-selects rules for detected languages (recommended) |
| `p/python` | Python best practices and bugs |
| `p/javascript` | JavaScript / Node.js |
| `p/typescript` | TypeScript |
| `p/go` | Go |
| `p/java` | Java |
| `p/ruby` | Ruby |
| `p/rust` | Rust |
| `p/security-audit` | Cross-language security findings |
| `p/owasp-top-ten` | OWASP Top 10 categories |
| `p/python-command-injection` | Python command injection specifically |
| `p/secrets` | Hardcoded secrets and credentials |
| `p/ci` | CI/CD configuration issues |
| `p/terraform` | Infrastructure-as-code |
| `p/docker` | Dockerfile issues |

---

## Writing custom rules

Rules live in YAML files. See `references/rule-syntax.md` for full reference.

### Minimal rule

```yaml
rules:
  - id: no-eval
    languages: [python]
    severity: ERROR
    message: "Avoid eval() — it executes arbitrary code. Use ast.literal_eval() for safe parsing."
    pattern: eval(...)
```

### Patterns with AND logic (`patterns`)

```yaml
rules:
  - id: unverified-db-query
    languages: [python]
    severity: WARNING
    message: "db_query called without verify=True"
    patterns:
      - pattern: db_query(...)
      - pattern-not: db_query(..., verify=True, ...)
```

### OR logic (`pattern-either`)

```yaml
rules:
  - id: weak-hash
    languages: [python]
    severity: ERROR
    message: "MD5 and SHA1 are cryptographically weak. Use SHA-256 or better."
    pattern-either:
      - pattern: hashlib.md5(...)
      - pattern: hashlib.sha1(...)
```

### Scope restriction (`pattern-inside` / `pattern-not-inside`)

```yaml
rules:
  - id: exec-in-request-handler
    languages: [python]
    severity: ERROR
    message: "Executing shell commands inside a Flask route is dangerous"
    patterns:
      - pattern: os.system(...)
      - pattern-inside: |
          @app.route(...)
          def $FUNC(...):
              ...
```

### Auto-fix with `fix:`

```yaml
rules:
  - id: use-subprocess-not-os-system
    languages: [python]
    severity: WARNING
    message: "Prefer subprocess.run() over os.system()"
    pattern: os.system($CMD)
    fix: subprocess.run($CMD, shell=True)
```

### Metavariables and constraints

```yaml
rules:
  - id: hardcoded-password-arg
    languages: [python]
    severity: ERROR
    message: "Hardcoded password passed as argument"
    patterns:
      - pattern: $FUNC(..., password=$PASS, ...)
      - metavariable-regex:
          metavariable: $PASS
          regex: '"[^"]+"'   # matches a string literal
```

### Cross-statement tracking (taint analysis)

```yaml
rules:
  - id: user-input-to-system
    languages: [python]
    severity: ERROR
    message: "User input reaches a shell command"
    mode: taint
    pattern-sources:
      - pattern: input(...)
    pattern-sinks:
      - pattern: os.system(...)
```

### Rule with `paths:` restrictions

```yaml
rules:
  - id: no-debug-print
    languages: [python]
    severity: INFO
    message: "Remove debug print statements before merging"
    pattern: print(...)
    paths:
      exclude:
        - tests/
        - scripts/
```

---

## Ignoring findings

### Inline suppression

```python
result = os.system(cmd)  # nosem
result = os.system(cmd)  # nosem: rule-id-here
```

### .semgrepignore file

Works like `.gitignore`:

```
# .semgrepignore
tests/
vendor/
*.min.js
generated/
```

---

## CI/CD integration

### GitHub Actions (OSS, no account required)

```yaml
name: Semgrep
on:
  push:
    branches: [main]
  pull_request:

jobs:
  semgrep:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: returntocorp/semgrep-action@v1
        with:
          config: auto
```

### GitHub Actions with SARIF (code scanning)

```yaml
- name: Run Semgrep
  run: semgrep scan --config auto --sarif -o semgrep.sarif .

- name: Upload SARIF
  uses: github/codeql-action/upload-sarif@v3
  with:
    sarif_file: semgrep.sarif
```

### semgrep ci (managed, requires SEMGREP_APP_TOKEN)

```bash
SEMGREP_APP_TOKEN=<token> semgrep ci
```

In CI, `semgrep ci` only reports findings introduced by the current PR/MR (differential scan).

### Pre-commit hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/returntocorp/semgrep
    rev: v1.127.0   # use latest tag from https://github.com/returntocorp/semgrep/releases
    hooks:
      - id: semgrep
        args: ['--config', 'auto', '--error']
```

The `--error` flag makes semgrep exit non-zero when findings exist, blocking the commit.

---

## Output formats

| Format | Flag | Use case |
|--------|------|----------|
| Text (default) | `--text` | Human reading |
| JSON | `--json` | Scripts, parsing |
| SARIF | `--sarif` | GitHub/GitLab code scanning |
| JUnit XML | `--junit-xml` | Jenkins, CI test reports |
| GitLab SAST | `--gitlab-sast` | GitLab security dashboard |
| Emacs | `--emacs` | Emacs flycheck |
| Vim | `--vim` | Vim ale/syntastic |

---

## Performance tips

- Use `--include='*.py'` to restrict file types when scanning large repos
- Avoid overly broad `...` ellipsis in deeply-nested patterns — it can be slow
- `--timeout` (default 5s per file) prevents runaway rules
- Use `-j` to control parallelism; don't over-subscribe cores
- `.semgrepignore` to skip vendored/generated directories
- `--exclude-minified-files` to skip minified JS/CSS

---

## Common pitfalls

1. **False positives with complex patterns**: Use `pattern-not` and `pattern-not-inside` to narrow scope
2. **Missing matches due to equivalent syntax**: Semgrep normalizes whitespace/parens, but not semantic aliases (e.g. `open()` vs `Path.open()`)
3. **Metavariable scope**: `$X` in one `pattern` is shared with `$X` in sibling patterns under `patterns:`
4. **Language mismatch**: Always specify `languages:` correctly — wrong language = no matches
5. **Registry rules need internet**: `--config auto` / `--config p/X` downloads rules; use `--metrics=off` for airgapped environments

---

## Reference files

- `references/rule-syntax.md` — Complete YAML rule syntax with all operators and metavariable operators
- `references/languages.md` — All supported languages, file extensions, and `languages:` key values

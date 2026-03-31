# Semgrep Rule Syntax — Complete Reference

Source: https://semgrep.dev/docs/writing-rules/rule-syntax

## Top-level schema

```yaml
rules:
  - id: <string>              # REQUIRED: unique identifier, e.g. "no-eval"
    message: <string>         # REQUIRED: explanation + remediation advice
    severity: <string>        # REQUIRED: ERROR | WARNING | INFO (or HIGH | MEDIUM | LOW | CRITICAL)
    languages: [<string>]     # REQUIRED: list of language keys (see languages.md)

    # REQUIRED: exactly one of the following pattern keys:
    pattern: <string>
    patterns: [...]
    pattern-either: [...]
    pattern-regex: <string>

    # Optional:
    fix: <string>             # auto-fix replacement
    metadata: {}              # arbitrary key-value, ignored by engine
    paths:
      include: [...]
      exclude: [...]
    options: {}               # engine toggles
    min-version: <string>
    max-version: <string>
```

---

## Pattern operators

### `pattern`

Matches a single expression or statement. Semgrep normalizes whitespace, parentheses, and equivalent syntax.

```yaml
pattern: hashlib.md5(...)
pattern: $X == $X
pattern: os.system($CMD)
```

### `patterns` (AND)

All child conditions must be true. Order doesn't affect the result — Semgrep evaluates all positive patterns first, then applies negative filters.

```yaml
patterns:
  - pattern: db_query(...)
  - pattern-not: db_query(..., verify=True, ...)
  - pattern-inside: |
      def $HANDLER(...):
          ...
```

### `pattern-either` (OR)

Any child condition can match.

```yaml
pattern-either:
  - pattern: hashlib.md5(...)
  - pattern: hashlib.sha1(...)
  - pattern: Crypto.Hash.MD5.new(...)
```

### `pattern-not`

Removes matches from the result set. Must be nested inside `patterns`.

```yaml
patterns:
  - pattern: requests.get(...)
  - pattern-not: requests.get(..., verify=True, ...)
```

### `pattern-inside`

Keeps only findings that lie inside the given pattern. Useful for scoping findings to specific functions, classes, or blocks.

```yaml
patterns:
  - pattern: eval(...)
  - pattern-inside: |
      @app.route(...)
      def $FUNC(...):
          ...
```

### `pattern-not-inside`

Keeps only findings that do NOT lie inside the given pattern.

```yaml
patterns:
  - pattern: assert $X
  - pattern-not-inside: |
      def test_$FUNC(...):
          ...
```

### `pattern-regex`

PCRE2-compatible regex in multiline mode. Useful for catching patterns that aren't AST-level (comments, string contents, etc.).

```yaml
pattern-regex: "TODO|FIXME|HACK"
```

### `pattern-not-regex`

Excludes results matching the regex.

```yaml
patterns:
  - pattern: "$FUNC(...)"
  - pattern-not-regex: "^(safe_|trusted_)"
```

---

## Metavariables

Metavariables start with `$` followed by uppercase letters/digits/underscores. They bind to matched code and can be reused within the same rule.

| Syntax | Matches |
|--------|---------|
| `$X` | Any single expression, statement, or identifier |
| `$...ARGS` | Zero or more arguments (variadic) |
| `$TYPE $VAR` | Typed variable (language-specific) |
| `...` | Zero or more items in a sequence |

**Examples:**

```python
# pattern: $X == $X
# matches: x == x, foo.bar() == foo.bar(), etc.

# pattern: def $FUNC($...PARAMS): ...
# matches any function with any parameters

# pattern: $OBJ.$METHOD($...ARGS)
# matches any method call
```

### Metavariable operators (nested under `patterns`)

#### `metavariable-regex`

Tests a metavariable against a Python `re`-compatible regex. Matching is **left-anchored**.

```yaml
patterns:
  - pattern: $FUNC(..., timeout=$TIMEOUT, ...)
  - metavariable-regex:
      metavariable: $TIMEOUT
      regex: "^[0-9]+$"   # must be a number literal
```

#### `metavariable-pattern`

Applies a sub-pattern to a metavariable's value. Can even specify a different language.

```yaml
patterns:
  - pattern: execute($QUERY)
  - metavariable-pattern:
      metavariable: $QUERY
      pattern: "... + ..."   # string concatenation → SQL injection risk
```

#### `metavariable-comparison`

Compares a metavariable's value using Python comparison expressions.

```yaml
patterns:
  - pattern: $FUNC(..., port=$PORT, ...)
  - metavariable-comparison:
      metavariable: $PORT
      comparison: $PORT < 1024
```

#### `metavariable-name`

Constrains a metavariable to match a specific identifier name.

```yaml
patterns:
  - pattern: $CLASS($...ARGS)
  - metavariable-name:
      metavariable: $CLASS
      regex: ".*Factory$"
```

#### `focus-metavariable`

When a pattern matches a larger region, focus the finding highlight on a specific metavariable's location.

```yaml
patterns:
  - pattern: |
      $FUNC(..., $PASSWORD, ...)
  - focus-metavariable: $PASSWORD
  - metavariable-regex:
      metavariable: $PASSWORD
      regex: '"[^"]+"'
```

---

## Taint analysis (data flow)

Use `mode: taint` to track data from sources to sinks across statements.

```yaml
rules:
  - id: user-input-to-sql
    mode: taint
    languages: [python]
    severity: ERROR
    message: "User input flows into SQL query — possible SQL injection"
    pattern-sources:
      - pattern: request.args.get(...)
      - pattern: request.form.get(...)
    pattern-sinks:
      - pattern: db.execute(...)
      - pattern: cursor.execute(...)
    pattern-sanitizers:
      - pattern: escape($X)
```

---

## The `fix:` field (auto-remediation)

Provides a replacement for the matched code. Use metavariables to preserve matched values.

```yaml
rules:
  - id: use-https
    languages: [python]
    severity: WARNING
    message: "Use HTTPS, not HTTP"
    pattern: requests.get("http://...")
    fix: requests.get("https://...")  # Note: can't replace metavariables in strings easily
```

Better pattern with metavariable:

```yaml
pattern: os.system($CMD)
fix: subprocess.run($CMD, shell=True, check=True)
```

Run auto-fix: `semgrep scan --config rules.yaml --autofix .`

---

## The `paths:` field

Restrict which files a rule applies to, without touching `.semgrepignore`.

```yaml
paths:
  include:
    - src/
    - lib/
  exclude:
    - tests/
    - "**/*.test.js"
```

---

## The `options:` field

Engine toggles for matching behavior:

```yaml
options:
  constant_propagation: true   # default true; set false to disable
  symbolic_propagation: false
  interfile: false
```

---

## Severity levels

| New | Old equivalent | Meaning |
|-----|---------------|---------|
| `CRITICAL` | — | Must fix |
| `HIGH` | `ERROR` | Fix before merge |
| `MEDIUM` | `WARNING` | Should fix |
| `LOW` | `INFO` | Informational |

Both the old and new values are accepted.

---

## Multi-language rules

A single rule can apply to multiple languages:

```yaml
rules:
  - id: no-empty-catch
    languages: [python, javascript, java, go]
    severity: WARNING
    message: "Empty catch block silences errors"
    pattern: |
      try:
          ...
      except ...:
          pass
```

Note: `generic` language uses a text-based matcher, not AST.

---

## Complete advanced example

```yaml
rules:
  - id: unsafe-deserialization
    languages: [python]
    severity: ERROR
    message: >
      Deserializing untrusted data with pickle/yaml.load is dangerous.
      Use yaml.safe_load() or a safer format like JSON.
    metadata:
      category: security
      cwe: CWE-502
      owasp: A8:2017 Insecure Deserialization
    pattern-either:
      - patterns:
          - pattern: pickle.loads($DATA)
          - pattern-not-inside: |
              if $DATA_SOURCE == "trusted":
                  ...
      - patterns:
          - pattern: yaml.load($DATA, ...)
          - pattern-not: yaml.load($DATA, Loader=yaml.SafeLoader)
          - pattern-not: yaml.safe_load(...)
    fix: yaml.safe_load($DATA)
    paths:
      exclude:
        - tests/fixtures/
```

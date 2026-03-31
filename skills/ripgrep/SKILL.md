---
name: ripgrep
description: >
  Expert guide for using ripgrep (rg) — the blazing-fast, Rust-powered search tool that respects
  .gitignore and searches recursively by default. Use this skill whenever the user wants to search
  code, find files by content, grep for patterns, search logs, locate TODOs/FIXMEs, count
  occurrences, replace text in output, or do any kind of text search across a codebase or directory.
  Invoke this skill even when the user just says "find all X in my project", "search for Y", "where
  is Z used", "grep for", or "look for" — ripgrep is almost always the right tool. Also trigger for
  tasks involving file filtering by type, multiline patterns, JSON output from search, or when the
  user needs search results piped into other tools.
---

# ripgrep (rg) Expert Guide

ripgrep is a line-oriented search tool that recursively searches directories for a regex pattern.
It's typically 5–10× faster than grep, respects `.gitignore` automatically, skips binary/hidden
files by default, and prints results with color and line numbers.

## Core syntax

```
rg PATTERN [PATH...]
rg [OPTIONS] PATTERN [PATH...]
rg [OPTIONS] -e PATTERN... [PATH...]
rg [OPTIONS] -f PATTERNFILE [PATH...]
```

When PATH is omitted, ripgrep searches the current directory recursively.

## Essential flags — the ones you'll use most

### Matching behavior
| Flag | Meaning |
|------|---------|
| `-i` / `--ignore-case` | Case-insensitive match |
| `-S` / `--smart-case` | Case-insensitive unless pattern has uppercase (prefer over `-i`) |
| `-F` / `--fixed-strings` | Treat pattern as literal string, not regex (faster, safer) |
| `-w` / `--word-regexp` | Only match whole words (`\bPATTERN\b`) |
| `-x` / `--line-regexp` | Only match whole lines |
| `-v` / `--invert-match` | Show lines that do NOT match |
| `-e PATTERN` | Add a pattern (repeatable; lines matching any pattern are shown) |
| `-f FILE` | Read patterns from a file (one per line) |
| `-U` / `--multiline` | Allow patterns to span multiple lines |
| `-P` / `--pcre2` | Use PCRE2 engine (enables lookaheads, lookbehinds, `\K`, named groups) |

### Output control
| Flag | Meaning |
|------|---------|
| `-n` | Show line numbers (default; use `-N` to suppress) |
| `-l` / `--files-with-matches` | Print only file paths (not matching lines) |
| `-L` when used as `--files-without-match` | ... but note `-L` means `--follow`; use `--files-without-match` |
| `-c` / `--count` | Print count of matching lines per file |
| `--count-matches` | Print count of individual matches (not lines) per file |
| `-o` / `--only-matching` | Print only the matched part of each line |
| `-A N` | Print N lines after each match |
| `-B N` | Print N lines before each match |
| `-C N` | Print N lines before AND after each match |
| `--json` | Output structured JSON (useful for tooling) |
| `-p` / `--pretty` | Force color and headings even when piped |
| `--color WHEN` | `always` / `never` / `auto` |
| `-q` / `--quiet` | Suppress output; exit 0 if any match found |
| `--heading` / `--no-heading` | Group results under filename headers |
| `--sort PATH` | Sort results by path (also: `modified`, `accessed`, `created`) |
| `--sortr PATH` | Same, reversed |

### File filtering
| Flag | Meaning |
|------|---------|
| `-g GLOB` / `--glob GLOB` | Include (`*.rs`) or exclude (`!*.min.js`) files by glob |
| `-t TYPE` / `--type TYPE` | Restrict to a file type (e.g., `py`, `js`, `rust`, `go`, `ts`) |
| `-T TYPE` / `--type-not TYPE` | Exclude a file type |
| `--type-list` | List all built-in and custom file types |
| `--type-add 'NAME:GLOB'` | Define a custom file type for this invocation |
| `--hidden` / `-.` | Search hidden files and directories (dotfiles) |
| `--no-ignore` | Don't respect `.gitignore` / `.ignore` / `.rgignore` |
| `--no-ignore-vcs` | Only ignore non-VCS ignore files |
| `-u` | Disable `.gitignore` filtering (alias: `--unrestricted`) |
| `-uu` | Also search hidden files |
| `-uuu` | Also search binary files |
| `-a` / `--text` | Treat binary files as text |
| `-z` / `--search-zip` | Search inside compressed files (`.gz`, `.bz2`, etc.) |
| `--follow` / `-L` | Follow symbolic links |
| `--max-depth N` | Limit directory recursion depth |
| `--max-filesize N` | Skip files larger than N bytes (e.g., `1M`, `500K`) |
| `--files` | List files that would be searched (no search performed) |
| `-0` / `--null` | Separate filenames with NUL (for `xargs -0`) |

### Replacement (output only — never modifies files)
| Flag | Meaning |
|------|---------|
| `-r TEXT` / `--replace TEXT` | Replace matched text in output. Supports `$1`, `$2` or `${name}` for capture groups. Named groups: `(?P<name>...)` in pattern, `$name` in replacement |

## Automatic filtering (what ripgrep ignores by default)

ripgrep automatically ignores:
1. Patterns in `.gitignore`, `.ignore`, `.rgignore` (`.rgignore` wins over `.ignore` wins over `.gitignore`)
2. Hidden files and directories (names starting with `.`)
3. Binary files (containing NUL bytes)
4. Symbolic links (not followed)

**Precedence override for ignores:** `.rgignore` > `.ignore` > `.gitignore`

To override: use `!pattern` in a `.ignore` or `.rgignore` to un-ignore something your `.gitignore` hides.

## Common patterns and recipes

### Search for a literal string (fastest)
```bash
rg -F 'exact string here' path/to/dir
```

### Case-insensitive search in Python files
```bash
rg -i 'pattern' -t py
```

### Find all TODO/FIXME comments in JS/TS, with context
```bash
rg -t js -t ts 'TODO|FIXME|HACK|XXX' -C 2
```

### Count matches per file
```bash
rg -c 'pattern' --sort path
```

### List only file paths (no lines shown)
```bash
rg -l 'import React'
```

### Search hidden files and ignored dirs
```bash
rg --hidden --no-ignore 'pattern'
```

### Search including node_modules (ignore .gitignore)
```bash
rg -u 'require\(' -t js
```

### Multiline: find async function bodies (PCRE2)
```bash
rg -P -U 'async function \w+\([^)]*\)\s*\{[^}]*await' src/
```

### Multiline with -U (Rust regex engine, anchors work differently)
```bash
rg -U 'fn \w+\([^)]*\)\s*->\s*\w+' --multiline src/
```

### Replace in output (NOT in files)
```bash
# Simple replacement
rg 'old_api_call' -r 'new_api_call'

# With capture groups
rg 'import (\w+) from "old-pkg"' -r 'import $1 from "new-pkg"'

# Named groups
rg 'user_(?P<id>\d+)' -r 'account_$id'
```

### JSON output (for tooling / scripting)
```bash
rg --json 'pattern' | jq '.data.lines.text'
```

### Pipe to xargs (use -0 for safety)
```bash
rg -l -0 'pattern' | xargs -0 sed -i 's/old/new/g'
```

### Search by multiple patterns (OR logic)
```bash
rg -e 'pattern1' -e 'pattern2'
# or
rg 'pattern1|pattern2'
```

### Custom file type
```bash
rg --type-add 'web:*.{html,css,js,ts}' -t web 'pattern'
```

### Exclude specific directories
```bash
rg 'pattern' -g '!dist/' -g '!node_modules/'
```

### Sort results by modification time
```bash
rg -l 'pattern' --sort modified
```

## Regex engine notes

By default, ripgrep uses the [Rust `regex` crate](https://docs.rs/regex/*/regex/#syntax):
- Supports Unicode by default (`\w` matches Unicode word chars, `.` matches any codepoint)
- Supports lookahead/lookbehind with `-P` (PCRE2 only)
- No backtracking — always linear time — so no catastrophic backfill

Switch to PCRE2 with `-P` when you need:
- Lookaheads: `(?=...)`, `(?!...)`
- Lookbehinds: `(?<=...)`, `(?<!...)`
- `\K` (reset match start)
- Non-greedy `*?` and `+?` across lines with `-U`
- Backreferences: `\1`

## Configuration file

ripgrep reads from `~/.ripgreprc` (or `$RIPGREP_CONFIG_PATH`).

```ini
# ~/.ripgreprc
--smart-case
--hidden
--glob=!.git/*
--max-columns=150
--max-columns-preview
```

Override any config setting on the command line — command-line flags take precedence. Use `--no-config` to ignore the config file entirely.

## Troubleshooting: when you get no results

1. **File excluded by .gitignore?** Try `rg -u 'pattern'` or `rg --no-ignore 'pattern'`
2. **Hidden file/dir?** Add `--hidden`
3. **Binary file?** Add `-a` or `-uuu`
4. **Wrong file type?** Verify with `rg --files | head` or check `rg --type-list`
5. **Pattern needs escaping?** Use `-F` for literals or wrap regex in single quotes
6. **Path not searched?** Run `rg --files path/` to see what ripgrep would search
7. **Debug mode:** `rg --debug 'pattern'` shows why files are included/excluded

## Performance tips

- Use `-F` (fixed strings) for literal searches — 2–3× faster than regex
- Narrow with `-t TYPE` or `-g GLOB` to search only relevant files
- Specify a path rather than searching the whole project
- `-S` (smart-case) adds minimal overhead vs `-i` but is smarter
- `--mmap` can help on very large files (uses memory-mapped I/O)
- Avoid `-P` unless you need PCRE2 features — the Rust engine is faster

## File type shorthand

Common built-in types: `py`, `js`, `ts`, `rust`/`rs`, `go`, `java`, `cpp`, `c`, `cs`, `rb`,
`php`, `html`, `css`, `json`, `yaml`/`yml`, `toml`, `sh`, `sql`, `md`, `dockerfile`

```bash
rg --type-list          # show all types
rg --type-list | rg py  # show globs for 'py' type
```

## Detailed flag reference

For a comprehensive list of all flags with examples, see `references/flags.md`.


**Docs:** https://ripgrep.dev/docs/

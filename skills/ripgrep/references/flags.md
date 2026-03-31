# ripgrep Complete Flag Reference

This document provides a comprehensive reference for all notable ripgrep flags, organized by
category, with usage examples.

---

## Pattern selection flags

### `-e PATTERN` / `--regexp PATTERN`
Specify a pattern. Can be repeated to OR multiple patterns.
```bash
rg -e 'foo' -e 'bar'      # matches lines with foo OR bar
```

### `-f FILE` / `--file FILE`
Read patterns from a file (one per line). Can be combined with `-e`.
```bash
echo -e 'TODO\nFIXME\nHACK' > pats.txt
rg -f pats.txt src/
```

### `-i` / `--ignore-case`
Case-insensitive matching (all characters). Slightly slower than case-sensitive.

### `-S` / `--smart-case`
Case-insensitive if pattern is all lowercase; case-sensitive if any uppercase. The go-to default for interactive use.
```bash
rg -S 'http'      # matches http, HTTP, Http
rg -S 'HTTP'      # only matches HTTP
```

### `-F` / `--fixed-strings`
Treat pattern as a literal string — no regex metacharacters. Fast and safe for user-supplied strings.
```bash
rg -F 'print("hello")' src/    # finds the literal string
```

### `-w` / `--word-regexp`
Surround pattern with `\b` word boundaries. Prevents matching substrings.
```bash
rg -w 'log'    # matches 'log' but not 'logger' or 'blog'
```

### `-x` / `--line-regexp`
Pattern must match the entire line.
```bash
rg -x 'TODO'    # only lines that contain exactly "TODO"
```

### `-v` / `--invert-match`
Print lines that do NOT match the pattern.
```bash
rg -v 'DEBUG' app.log    # all non-debug log lines
```

### `-U` / `--multiline`
Allow patterns to span multiple lines. With this flag, `^` and `$` match start/end of each line;
use `\A` and `\z` for start/end of file. Dot (`.`) does not match `\n` unless you add `(?s)`.
```bash
rg -U 'start_block.*?end_block' --multiline-dotall
```

### `-P` / `--pcre2`
Use PCRE2 regex engine instead of Rust's `regex` crate. Required for lookaheads/lookbehinds,
`\K`, backreferences, and atomic groups.
```bash
rg -P '(?<=def )\w+'         # word after "def " (lookbehind)
rg -P '\bfoo\b(?!bar)'       # "foo" not followed by "bar" (negative lookahead)
rg -P -U '(?s)BEGIN.*?END'   # multiline with PCRE2 dot-all
```

---

## Output formatting flags

### `-n` / `--line-number`
Show line numbers (on by default). Use `-N` / `--no-line-number` to suppress.

### `-H` / `--with-filename`
Show filename on each match (default when searching multiple files). `-h` suppresses.

### `--heading` / `--no-heading`
Group results under a filename header instead of repeating filename per line.
Default: heading on when stdout is a TTY.

### `-l` / `--files-with-matches`
Print only paths of files with at least one match. No match lines printed.
```bash
rg -l 'TODO' | wc -l    # count files with TODOs
```

### `--files-without-match`
Print paths of files with zero matches.
```bash
rg --files-without-match 'Copyright' -t py    # Python files missing copyright
```

### `-c` / `--count`
Print count of matching *lines* per file (not matches).
```bash
rg -c 'error' logs/
```

### `--count-matches`
Print count of individual matches per file (multiple matches per line each counted).
```bash
rg --count-matches 'import' src/    # total import statements per file
```

### `-o` / `--only-matching`
Print only the matched portion of each line (not the whole line).
```bash
rg -o 'https?://[^\s"]+' README.md    # extract all URLs
```

### `-A N` / `--after-context N`
Print N lines after each match. Adds `--` separators between non-adjacent match groups.

### `-B N` / `--before-context N`
Print N lines before each match.

### `-C N` / `--context N`
Print N lines before and after. Equivalent to `-A N -B N`.

### `-p` / `--pretty`
Force color, headings, and line numbers even when output is piped.

### `--color WHEN`
Control color output: `always`, `never`, `auto` (default).

### `--colors SPEC`
Fine-grained color configuration:
```bash
rg --colors 'match:bg:yellow' --colors 'match:fg:black' 'pattern'
```

### `--json`
Output newline-delimited JSON. Each line is a JSON object with a `type` field:
- `"begin"` — start of a file
- `"match"` — a matching line with offsets
- `"context"` — a context line
- `"end"` — end of a file
- `"summary"` — aggregate stats

```bash
rg --json 'pattern' | jq 'select(.type=="match") | .data.lines.text'
```

### `--no-messages`
Suppress error messages (e.g., permission denied).

### `-q` / `--quiet`
Do not print matches. Exit code 0 if any match found, 1 if none. Useful in scripts:
```bash
rg -q 'TODO' && echo "TODOs found!"
```

### `--stats`
Print aggregate statistics after search (total matches, files searched, etc.).

### `--sort FIELD` / `--sortr FIELD`
Sort output by `path`, `modified`, `accessed`, or `created`. `--sortr` reverses order.
Note: this disables parallelism, so it's slower for large searches.

---

## File/directory filtering flags

### `-g GLOB` / `--glob GLOB`
Include (`*.rs`) or exclude (`!*.min.js`) by glob pattern. Repeatable; later globs win.
```bash
rg 'pattern' -g '*.{ts,tsx}'          # only TypeScript
rg 'pattern' -g '!*.test.*'           # exclude test files
rg 'pattern' -g '!dist/' -g '!build/' # exclude output dirs
```

### `-t TYPE` / `--type TYPE`
Restrict to built-in file type. Repeatable (OR logic). Use `--type-list` to see available types.
```bash
rg 'pattern' -t py -t js    # search Python and JavaScript files
```

### `-T TYPE` / `--type-not TYPE`
Exclude a file type.
```bash
rg 'pattern' -T html    # skip HTML files
```

### `--type-list`
Show all registered file types and their glob patterns.
```bash
rg --type-list | grep '^json'
```

### `--type-add 'NAME:GLOB'`
Define a custom type for the current invocation (not persisted).
```bash
rg --type-add 'infra:*.{tf,tfvars,hcl}' -t infra 'variable'
```

### `--hidden` / `-.`
Search hidden files/directories (those with a `.` prefix).
```bash
rg --hidden 'api_key' ~/.config/
```

### `--no-ignore`
Disable all ignore file processing (`.gitignore`, `.ignore`, `.rgignore`).

### `--no-ignore-vcs`
Disable only VCS ignore files (`.gitignore`, `$GIT_DIR/info/exclude`, `core.excludesFile`).

### `--ignore-file FILE`
Use an additional ignore file.

### `-u` / `--unrestricted`
Cumulative unrestriction:
- `-u`: ignore `.gitignore` rules
- `-uu`: also search hidden files
- `-uuu`: also search binary files

### `-a` / `--text`
Search binary files as if they were text. Can dump binary data to terminal — use carefully.

### `-z` / `--search-zip`
Search inside compressed files: `.gz`, `.bz2`, `.lzma`, `.xz`, `.lz4`, `.zst`.

### `--follow` / `-L`
Follow symbolic links during directory traversal.

### `--max-depth N` / `-d N`
Limit directory traversal depth. `--max-depth 1` searches only the given directory.

### `--max-filesize NUM`
Skip files larger than NUM bytes. Supports suffixes: `K`, `M`, `G`.
```bash
rg 'pattern' --max-filesize 1M
```

### `--files`
List files that would be searched (no actual search). Useful for debugging file selection.
```bash
rg --files -t py src/
```

### `--iglob GLOB`
Same as `--glob` but case-insensitive.

### `--ignore-file-case-insensitive`
Process ignore files case-insensitively (useful on macOS/Windows).

---

## Replacement flags

### `-r TEXT` / `--replace TEXT`
Replace matched text in ripgrep's *output* (files are never modified).

Supports capture group references in TEXT:
- `$0` or `$&` — the entire match
- `$1`, `$2`, ... — numbered capture groups
- `$name` or `${name}` — named capture groups (`(?P<name>...)` in pattern)

```bash
# Simple substitution
rg 'old_function' -r 'new_function'

# Swap first/last name: "Smith, John" → "John Smith"
rg '(\w+), (\w+)' names.txt -r '$2 $1'

# Named groups
rg '(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})' -r '$day/$month/$year'

# With -o: extract and reformat
rg -o '"version": "([^"]+)"' package.json -r '$1'
```

---

## Preprocessor

### `--pre COMMAND`
Run a command on each file before searching. The command receives the file path as its first
argument and the file content on stdin. Useful for searching PDFs, archives, etc.

### `--pre-glob GLOB`
Only run the preprocessor on files matching this glob (avoids overhead on irrelevant files).
```bash
rg --pre pdftotext --pre-glob '*.pdf' 'search term'
```

---

## Miscellaneous

### `--mmap`
Use memory-mapped I/O where possible (can speed up searches on large files).

### `--no-mmap`
Disable memory-mapped I/O (use for consistent binary file detection behavior).

### `-0` / `--null`
Print NUL byte after each file path (for use with `xargs -0`).
```bash
rg -l -0 'pattern' | xargs -0 wc -l
```

### `--null-data`
Use NUL bytes as line terminators (for processing NUL-delimited data).

### `--line-buffered`
Force line-by-line output buffering (useful when piping to `tail -f` or live monitoring).

### `-M N` / `--max-columns N`
Truncate lines longer than N characters. `--max-columns-preview` shows a truncated preview.

### `--max-count N` / `-m N`
Stop after N matches per file.

### `--encoding ENCODING` / `-E ENCODING`
Force a specific encoding (e.g., `utf-16`, `latin1`). Use `none` for raw bytes.

### `--no-config`
Ignore `~/.ripgreprc` and `RIPGREP_CONFIG_PATH`.

### `--debug`
Print debug information to stderr (shows which files are skipped and why).

### `--trace`
Even more verbose debug output.

### `--dfa-size-limit N`
Limit the DFA cache size (for pathological regex patterns that blow up the DFA).

### `--regex-size-limit N`
Limit the size of compiled regex.

---

## Exit codes

| Code | Meaning |
|------|---------|
| `0` | Match found |
| `1` | No match |
| `2` | Error |

---

## Environment variables

| Variable | Meaning |
|----------|---------|
| `RIPGREP_CONFIG_PATH` | Path to ripgrep config file |
| `RIPGREP_UNRESTRICTED` | Equivalent to `-u` if set |

---

## Config file format (`~/.ripgreprc`)

One flag per line. Comments with `#`. Flag+value on same line with `=` or on two lines:
```ini
# ~/.ripgreprc
--smart-case
--hidden
--glob=!.git/*
--glob=!node_modules/
--max-columns=200
--max-columns-preview
--follow
```

Override any config setting on the CLI — command-line flags are appended after config flags, so they win on conflicts.

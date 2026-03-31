---
name: gum
description: >
  Comprehensive reference for Charmbracelet `gum` — a CLI tool for building glamorous, interactive shell scripts. Use this skill whenever the user mentions gum, wants to build interactive shell scripts with prompts, menus, spinners, styled output, or asks how to make a terminal UI in Bash. Triggers on: `gum choose`, `gum input`, `gum confirm`, `gum filter`, `gum spin`, `gum style`, `gum write`, `gum file`, `gum pager`, `gum table`, `gum format`, `gum join`, `gum log`, interactive CLI wizards, shell script UX, Charmbracelet scripting, or any request to make a shell script more interactive or visually appealing. Always use this skill when the user is writing or debugging a script that uses gum — don't rely on memory alone.
---

# Gum — Glamorous Shell Scripts

`gum` is a CLI tool by Charmbracelet that adds interactive components and beautiful styling to shell scripts using [Bubbles](https://github.com/charmbracelet/bubbles) and [Lip Gloss](https://github.com/charmbracelet/lipgloss), with zero Go required.

**Docs:** https://github.com/charmbracelet/gum  
**Install:** `brew install gum` · `nix-env -iA nixpkgs.gum` · `go install github.com/charmbracelet/gum@latest`

---

## Commands at a Glance

| Command    | Purpose                                      |
|------------|----------------------------------------------|
| `choose`   | Pick one or more items from a list           |
| `confirm`  | Yes/No prompt (returns exit code 0 or 1)     |
| `file`     | Browse and pick a file from a directory tree |
| `filter`   | Fuzzy-search a piped list                    |
| `format`   | Render markdown, templates, code, or emoji   |
| `input`    | Single-line text prompt                      |
| `join`     | Compose styled blocks horizontally/vertically|
| `log`      | Structured log messages with levels          |
| `pager`    | Scrollable document viewer                   |
| `spin`     | Spinner while a command runs                 |
| `style`    | Apply colors, borders, padding to text       |
| `table`    | Render CSV/tabular data, return selected row |
| `write`    | Multi-line text prompt (Ctrl+D to finish)    |

---

## Core Patterns

### Capture user input
```bash
NAME=$(gum input --placeholder "Your name")
BODY=$(gum write --placeholder "Describe the change...")
```

### Make a choice
```bash
TYPE=$(gum choose "fix" "feat" "docs" "refactor" "chore")
# multi-select (Tab to mark, Enter to confirm)
ITEMS=$(gum choose --no-limit item1 item2 item3)
ITEMS=$(cat list.txt | gum choose --limit 3)
```

### Fuzzy filter a list
```bash
BRANCH=$(git branch | cut -c 3- | gum filter --placeholder "Switch to...")
FILE=$(find . -name "*.go" | gum filter)
SESSION=$(tmux list-sessions -F '#S' | gum filter --placeholder "Pick session...")
```

### Confirm before acting
```bash
# && / || idiom — clean and idiomatic
gum confirm "Deploy to production?" && ./deploy.sh || echo "Cancelled."

# if-block style
if gum confirm "Remove $FILE?"; then
  rm "$FILE"
fi
```

### Spinner while waiting
```bash
gum spin --spinner dot --title "Installing dependencies..." -- npm install
gum spin --spinner pulse --title "Fetching data..." --show-output -- curl -s https://api.example.com/data
```
Available spinners: `line` `dot` `minidot` `jump` `pulse` `points` `globe` `moon` `monkey` `meter` `hamburger`

### Styled output
```bash
gum style \
  --foreground 212 --border-foreground 212 --border double \
  --align center --width 50 --margin "1 2" --padding "2 4" \
  "Build complete!" "Deployed to production"

# Compose blocks side by side
LEFT=$(gum style --border double --padding "1 3" "Status: OK")
RIGHT=$(gum style --border double --padding "1 3" "Time: 4.2s")
gum join --horizontal "$LEFT" "$RIGHT"
```

### Format / render text
```bash
# Markdown
echo "# Title\n- item 1\n- item 2" | gum format

# Syntax-highlighted code
cat main.go | gum format -t code

# Template helpers (Bold, Italic, Color, etc.)
echo '{{ Bold "Important" }}: {{ Color "212" "0" " done " }}' | gum format -t template

# Emoji
echo "Build :white_check_mark: Tests :fire:" | gum format -t emoji
```

### Log messages
```bash
gum log --level info  "Starting deploy"
gum log --level warn  "Config file missing, using defaults"
gum log --level error "Connection failed" host db.example.com port 5432
gum log --structured --level debug "Query executed" rows 42 duration 12ms
gum log --time rfc822 --level info "Timestamped log entry"
```
Log levels: `debug` `info` `warn` `error` `fatal`

### File picker
```bash
FILE=$(gum file .)               # pick in current dir
FILE=$(gum file $HOME --all)     # include hidden files
$EDITOR $(gum file)
```

### Pager (scroll long output)
```bash
gum pager < README.md
man git | gum pager
```

### Table (CSV → interactive picker)
```bash
# Select a row, then extract a column
gum table < data.csv | cut -d',' -f1
# Pipe-delimited
cat report.txt | gum table --separator '|' --columns "Name,Status,Date"
```

### Password input
```bash
PASSWORD=$(gum input --password --placeholder "Enter password")
# sudo replacement
alias please="gum input --password | sudo -nS"
```

---

## Styling Reference

Every command supports Lip Gloss styling via flags or env vars.

### Color flags
```
--foreground <color>         Text color
--background <color>         Background color
--border-foreground <color>  Border color
```
Colors accept: ANSI 256 number (`212`), hex (`#FF87D7`), or ANSI name.

### Layout flags (for `style`)
```
--border <style>     none | hidden | normal | rounded | double | thick | block | outer-half | inner-half
--align <pos>        left | center | right | bottom | middle | top
--padding "V H"      Inner space (e.g. "1 2" = 1 top/bottom, 2 left/right)
--margin "V H"       Outer space
--width <int>        Force a fixed width
--height <int>       Force a fixed height
--bold               Bold text
--italic             Italic text
--strikethrough      Strikethrough
--underline          Underline
--faint              Dimmed text
```

### Environment variable overrides

Every flag maps to `GUM_<COMMAND>_<FLAG>` in env. Useful for setting defaults:

```bash
export GUM_INPUT_PROMPT="> "
export GUM_INPUT_CURSOR_FOREGROUND="#FF0"
export GUM_CHOOSE_CURSOR_FOREGROUND="#0FF"
export GUM_CONFIRM_PROMPT_FOREGROUND="#F5A97F"
```

Flags passed directly override env vars.

---

## Complete Workflow Example — Git Conventional Commit

```bash
#!/usr/bin/env bash
set -euo pipefail

TYPE=$(gum choose "feat" "fix" "docs" "style" "refactor" "test" "chore" "revert")
SCOPE=$(gum input --placeholder "scope (optional, press Enter to skip)")
[[ -n "$SCOPE" ]] && SCOPE="($SCOPE)"

SUMMARY=$(gum input --value "$TYPE$SCOPE: " --placeholder "Short summary of change")
BODY=$(gum write --placeholder "Longer description (Ctrl+D to finish, optional)")

gum confirm "Commit with this message?" || exit 0

git commit -m "$SUMMARY" ${BODY:+-m "$BODY"}
```

---

## `gum join` Layout Tips

- Always quote `gum style` output to preserve newlines when passing to `join`
- Use `--vertical` for stacking, `--horizontal` (default) for side-by-side
- Use `--align center | left | right` to control cross-axis alignment

```bash
TOP=$(gum style --border rounded --padding "0 2" "Header")
BOT=$(gum style --border rounded --padding "0 2" --width 20 "Body content")
gum join --vertical --align center "$TOP" "$BOT"
```

---

## `gum filter` Tips

- Reads from stdin; press Enter to confirm, Esc/Ctrl+C to cancel
- `--no-limit`: select any number; `--limit N`: up to N items
- `--select-if-one`: auto-select when only one match remains
- `--height N`: cap the list viewport

```bash
# Pick open GitHub PR to check out
gh pr list | cut -f1,2 | gum filter | cut -f1 | xargs gh pr checkout

# Browse history
gum filter < ~/.zsh_history --height 20
```

---

## `gum choose` Tips

- Items can come from args or stdin
- Use brace expansion: `gum choose {{A,K,Q,J},{10..2}}" "{♠,♥,♣,♦}`
- `--header "text"` adds a header above the list
- `--cursor "→ "` changes the cursor symbol

```bash
# Uninstall brew packages
brew list | gum choose --no-limit | xargs brew uninstall

# Delete local git branches
git branch | cut -c 3- | gum choose --no-limit | xargs git branch -D
```

---

## `gum spin` Tips

- Command comes after `--`: `gum spin --title "..." -- <cmd> [args...]`
- `--show-output`: print the command's stdout after spinner completes
- Exit code of the wrapped command is preserved

```bash
RESULT=$(gum spin --spinner globe --title "Fetching..." --show-output -- curl -s https://api.example.com)
```

---

## `gum input` & `gum write` Tips

| Flag | Effect |
|------|--------|
| `--value "text"` | Pre-fill input |
| `--placeholder "..."` | Ghost text when empty |
| `--char-limit N` | Max characters |
| `--width N` | Input box width |
| `--password` | Mask input |
| `--header "..."` | Label above the input |

---

## Subcommand Quick Help

Run `gum <command> --help` to see all flags and their env-var equivalents.

For deep reference on any subcommand, see: https://github.com/charmbracelet/gum#commands

---

## Common Gotchas

- **`gum confirm` returns exit code, not text.** Use `&&`/`||` or `if` — don't try to capture its output.
- **Always quote `gum style` output** in `gum join` calls or newlines collapse.
- **`gum write` ends on Ctrl+D**, not Enter. Remind users in your `--placeholder`.
- **Spinner wraps commands with `--`**: `gum spin --title "..." -- sleep 3` (not `gum spin sleep 3`).
- **Colors**: gum accepts ANSI 256 numbers, hex `#RRGGBB`, or ANSI color names. On terminals with limited palette, hex values get approximated.
- **Non-interactive / CI**: gum requires a TTY. In CI, pipe a default or use `echo "default" | gum choose` patterns, or skip the prompt entirely with a conditional.

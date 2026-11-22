#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib

from common import (
    IGNORE_REVS_FILENAME,
    IGNORE_REVS_HEADER,
    VERSION_KEY,
    git_root,
    has_key,
    resolve_target,
    selected_entries,
)


def render_entry(key: str, value: str, comment: str, needs_ignore_file: bool, indent: str = "  ") -> list[str]:
    lines = [f"{indent}# {comment}"]
    cmd = f"git config --local --get {key} >/dev/null 2>&1 || git config --local {key} {value}"
    if needs_ignore_file:
        lines.append(f'{indent}if [ -f "$top/{IGNORE_REVS_FILENAME}" ]; then')
        lines.append(f"{indent}  {cmd}")
        lines.append(f"{indent}fi")
    else:
        lines.append(f"{indent}{cmd}")
    return lines


def render_block(entries: list[tuple[str, str, str, bool]], ver: str = "1") -> str:
    lines = [
        f'ver="{ver}"',
        f'if [ "$(git config --local --get {VERSION_KEY} 2>/dev/null)" != "$ver" ]; then',
        "top=$(git rev-parse --show-toplevel)",
    ]
    for entry in entries:
        lines.extend(render_entry(*entry))
    lines.append(f'  git config --local {VERSION_KEY} "$ver"')
    lines.append("fi")
    return "\n".join(lines) + "\n"


def merge_into_script(existing: str, missing: list[tuple[str, str, str, bool]]) -> str:
    lines = existing.splitlines()
    if VERSION_KEY.lower() in existing.lower():
        for i, line in enumerate(lines):
            m = re.match(r'^([ \t]*)ver="(\d+)"', line)
            if m:
                lines[i] = f'{m.group(1)}ver="{int(m.group(2)) + 1}"'
                break
        for i, line in enumerate(lines):
            m = re.match(rf"^([ \t]*)git config --local {re.escape(VERSION_KEY)}\b", line, re.IGNORECASE)
            if m:
                indent = m.group(1)
                inserted: list[str] = []
                for entry in missing:
                    inserted.extend(render_entry(*entry, indent=indent))
                return "\n".join(lines[:i] + inserted + lines[i:]) + "\n"

    in_tree_idx = next(
        (i for i, ln in enumerate(lines) if "is-inside-work-tree" in ln and re.match(r"^[ \t]*if\b", ln)),
        None,
    )
    if in_tree_idx is not None:
        depth = 0
        fi_idx = None
        for i in range(in_tree_idx, len(lines)):
            s = lines[i].strip()
            if re.match(r"^if\b", s):
                depth += 1
            if re.match(r"^fi\b", s):
                depth -= 1
                if depth == 0:
                    fi_idx = i
                    break
        if fi_idx is not None:
            m_outer = re.match(r"^([ \t]*)", lines[in_tree_idx])
            inner_indent = (m_outer.group(1) if m_outer else "") + "  "
            inserted = []
            for entry in missing:
                inserted.extend(render_entry(*entry, indent=inner_indent))
            return "\n".join(lines[:fi_idx] + inserted + lines[fi_idx:]) + "\n"

    sep = "" if (not existing or existing.endswith("\n\n")) else ("\n" if existing.endswith("\n") else "\n\n")
    return existing + sep + render_block(missing)


def format_toml_multiline(s: str) -> str:
    esc = s.replace("\\", "\\\\").replace('"""', '\\"\\"\\"')
    esc = "".join(ch if ch in ("\n", "\t") or ord(ch) >= 32 else f"\\u{ord(ch):04x}" for ch in esc)
    if esc.endswith('"'):
        esc = esc[:-1] + '\\"'
    return f'"""\n{esc}"""'


def scan_string(text: str, pos: int) -> int:
    n = len(text)
    if text.startswith('"""', pos):
        i = pos + 3
        while i < n:
            if text[i] == "\\":
                i += 2
            elif text.startswith('"""', i):
                i += 3
                extra = 0
                while i < n and text[i] == '"' and extra < 2:
                    i += 1
                    extra += 1
                return i
            else:
                i += 1
        return n
    if text.startswith("'''", pos):
        i = pos + 3
        while i < n:
            if text.startswith("'''", i):
                i += 3
                extra = 0
                while i < n and text[i] == "'" and extra < 2:
                    i += 1
                    extra += 1
                return i
            i += 1
        return n
    quote = text[pos]
    i = pos + 1
    while i < n:
        if quote == '"' and text[i] == "\\":
            i += 2
        elif text[i] == quote:
            return i + 1
        else:
            i += 1
    return n


def scan_balanced(text: str, pos: int, open_ch: str, close_ch: str) -> int:
    n = len(text)
    depth = 1
    i = pos + 1
    while i < n and depth > 0:
        ch = text[i]
        if ch in ('"', "'"):
            i = scan_string(text, i)
        elif ch == "#":
            nl = text.find("\n", i)
            i = n if nl == -1 else nl + 1
        elif ch == open_ch:
            depth += 1
            i += 1
        elif ch == close_ch:
            depth -= 1
            i += 1
        else:
            i += 1
    return i


def parse_header_name(raw: str) -> str:
    parts: list[str] = []
    i = 0
    while i < len(raw):
        if raw[i] in " \t.":
            i += 1
        elif raw[i] in ('"', "'"):
            end = scan_string(raw, i)
            parts.append(tomllib.loads(f"k = {raw[i:end]}")["k"])
            i = end
        else:
            m = re.match(r"[A-Za-z0-9_-]+", raw[i:])
            if not m:
                break
            parts.append(m.group(0))
            i += len(m.group(0))
    return ".".join(parts)


def scan_toml_layout(text: str) -> tuple[dict[str, tuple[int, int]], dict[tuple[str, str], tuple[int, int]]]:
    n = len(text)
    i = 0
    section = ""
    sections: dict[str, tuple[int, int]] = {}
    section_start: int | None = None
    entries: dict[tuple[str, str], tuple[int, int]] = {}

    while i < n:
        ch = text[i]
        if ch in " \t\r\n":
            i += 1
        elif ch == "#":
            nl = text.find("\n", i)
            i = n if nl == -1 else nl + 1
        elif ch == "[":
            if section and section_start is not None:
                sections[section] = (section_start, i)
            is_aot = text.startswith("[[", i)
            start = i + (2 if is_aot else 1)
            end_tok = "]]" if is_aot else "]"
            j = start
            while j < n:
                if text[j] in ('"', "'"):
                    j = scan_string(text, j)
                elif text.startswith(end_tok, j):
                    break
                else:
                    j += 1
            name = parse_header_name(text[start:j].strip())
            section = f"[[{name}]]" if is_aot else name
            section_start = i
            nl = text.find("\n", j)
            i = n if nl == -1 else nl + 1
        else:
            key_parts: list[str] = []
            j = i
            while j < n:
                if text[j] in " \t.":
                    j += 1
                elif text[j] in ('"', "'"):
                    end = scan_string(text, j)
                    key_parts.append(tomllib.loads(f"k = {text[j:end]}")["k"])
                    j = end
                elif text[j] == "=":
                    j += 1
                    break
                else:
                    m = re.match(r"[A-Za-z0-9_-]+", text[j:])
                    if not m:
                        break
                    key_parts.append(m.group(0))
                    j += len(m.group(0))
            while j < n and text[j] in " \t":
                j += 1
            val_start = j
            if val_start >= n:
                break
            vc = text[val_start]
            if vc in ('"', "'"):
                val_end = scan_string(text, val_start)
            elif vc == "[":
                val_end = scan_balanced(text, val_start, "[", "]")
            elif vc == "{":
                val_end = scan_balanced(text, val_start, "{", "}")
            else:
                k = val_start
                while k < n and text[k] not in "\n#":
                    k += 1
                val_end = k
                while val_end > val_start and text[val_end - 1] in " \t\r":
                    val_end -= 1
            if key_parts:
                entries[(section, ".".join(key_parts))] = (val_start, val_end)
            i = val_end

    if section and section_start is not None:
        sections[section] = (section_start, n)
    return sections, entries


def scan_array_items(text: str, arr_start: int, arr_end: int) -> list[tuple[int, int, object]]:
    items: list[tuple[int, int, object]] = []
    i = arr_start + 1
    limit = arr_end - 1
    while i < limit:
        ch = text[i]
        if ch in " \t\r\n,":
            i += 1
        elif ch == "#":
            nl = text.find("\n", i)
            i = limit if nl == -1 else min(limit, nl + 1)
        elif ch in ('"', "'"):
            end = scan_string(text, i)
            items.append((i, end, tomllib.loads(f"x = {text[i:end]}")["x"]))
            i = end
        elif ch == "{":
            end = scan_balanced(text, i, "{", "}")
            items.append((i, end, tomllib.loads(f"x = {text[i:end]}")["x"]))
            i = end
        elif ch == "[":
            end = scan_balanced(text, i, "[", "]")
            items.append((i, end, tomllib.loads(f"x = {text[i:end]}")["x"]))
            i = end
        else:
            i += 1
    return items


def patch_toml(text: str, entries: list[tuple[str, str, str, bool]]) -> tuple[str, list[str], list[str]]:
    data = tomllib.loads(text) if text.strip() else {}
    hooks = data.get("hooks")

    if hooks is not None and not isinstance(hooks, dict):
        raise SystemExit("Error: [hooks] exists and is not a TOML table.")

    enter_val = hooks.get("enter") if isinstance(hooks, dict) else None
    existing_texts: list[str] = []
    if isinstance(enter_val, str):
        existing_texts.append(enter_val)
    elif isinstance(enter_val, list):
        for item in enter_val:
            if isinstance(item, str):
                existing_texts.append(item)
            elif isinstance(item, dict) and isinstance(item.get("run"), str):
                existing_texts.append(item["run"])
    elif isinstance(enter_val, dict):
        if "task" in enter_val and "run" not in enter_val:
            raise SystemExit("Error: hooks.enter uses a task reference; merge manually into that task.")
        if isinstance(enter_val.get("run"), str):
            existing_texts.append(enter_val["run"])
        else:
            raise SystemExit("Error: unsupported hooks.enter table format.")
    elif enter_val is not None:
        raise SystemExit(f"Error: unsupported hooks.enter type: {type(enter_val).__name__}")

    combined = "\n".join(existing_texts)
    present = [e[0] for e in entries if has_key(combined, e[0])]
    missing = [e for e in entries if not has_key(combined, e[0])]
    if not missing:
        return text, [], present

    sections, toml_entries = scan_toml_layout(text)

    if enter_val is None:
        block = f"enter = {format_toml_multiline(render_block(missing))}\n"
        if "hooks" in sections:
            start, end = sections["hooks"]
            insert_at = end
            while insert_at > start and text[insert_at - 1] in " \t\r\n":
                insert_at -= 1
            tail = text[insert_at:].lstrip("\r\n")
            suffix = f"\n{tail}" if tail else ""
            new_text = text[:insert_at] + "\n" + block + suffix
        else:
            prefix = "" if not text.strip() else (text.rstrip() + "\n\n")
            new_text = f"{prefix}[hooks]\n{block}"
    elif isinstance(enter_val, str):
        span = toml_entries.get(("hooks", "enter")) or toml_entries.get(("", "hooks.enter"))
        if not span:
            raise SystemExit("Error: could not locate hooks.enter in TOML source.")
        merged = merge_into_script(enter_val, missing)
        new_text = text[: span[0]] + format_toml_multiline(merged) + text[span[1] :]
    elif isinstance(enter_val, list):
        span = toml_entries.get(("hooks", "enter")) or toml_entries.get(("", "hooks.enter"))
        if not span:
            raise SystemExit("Error: could not locate hooks.enter array in TOML source.")
        items = scan_array_items(text, span[0], span[1])
        target_item = next(
            (it for it in items if isinstance(it[2], str) and (VERSION_KEY.lower() in it[2].lower() or "is-inside-work-tree" in it[2])),
            None,
        )
        if target_item:
            merged = merge_into_script(target_item[2], missing)
            new_text = text[: target_item[0]] + format_toml_multiline(merged) + text[target_item[1] :]
        else:
            new_item = format_toml_multiline(render_block(missing))
            if not items:
                new_text = text[: span[0] + 1] + f"\n  {new_item},\n" + text[span[1] - 1 :]
            else:
                last_end = items[-1][1]
                between = text[last_end : span[1] - 1]
                comma = "" if "," in between else ","
                new_text = text[:last_end] + f"{comma}\n  {new_item},\n" + text[span[1] - 1 :]
    else:
        span = toml_entries.get(("hooks.enter", "run")) or toml_entries.get(("hooks", "enter.run")) or toml_entries.get(("", "hooks.enter.run"))
        if not span:
            inline_span = toml_entries.get(("hooks", "enter")) or toml_entries.get(("", "hooks.enter"))
            if inline_span:
                _, inner_entries = scan_toml_layout(text[inline_span[0] + 1 : inline_span[1] - 1])
                rel = inner_entries.get(("", "run"))
                if rel:
                    span = (inline_span[0] + 1 + rel[0], inline_span[0] + 1 + rel[1])
        if not span:
            raise SystemExit("Error: could not locate hooks.enter.run in TOML source.")
        merged = merge_into_script(enter_val["run"], missing)
        new_text = text[: span[0]] + format_toml_multiline(merged) + text[span[1] :]

    if new_text and not new_text.endswith("\n"):
        new_text += "\n"
    tomllib.loads(new_text)
    return new_text, [e[0] for e in missing], present


def main() -> int:
    parser = argparse.ArgumentParser(description="Create .git-blame-ignore-revs and merge mise git defaults.")
    parser.add_argument("--file", help="Explicit mise config file path.")
    parser.add_argument("--local", action="store_true", help="Target mise.local.toml / .mise.local.toml.")
    parser.add_argument("--minimal", action="store_true", help="Use only the first 4 entries.")
    parser.add_argument("--skip-ignore-revs", action="store_true", help="Do not create .git-blame-ignore-revs.")
    parser.add_argument("--dry-run", action="store_true", help="Validate without writing.")
    parser.add_argument("--json", action="store_true", help="Output JSON summary.")
    args = parser.parse_args()

    root = git_root()
    target = resolve_target(root, args.file, args.local)
    selected = selected_entries(args.minimal)

    ignore_revs = root / IGNORE_REVS_FILENAME
    create_ignore_revs = (not args.local) and (not args.skip_ignore_revs) and (not ignore_revs.is_file())
    if create_ignore_revs and not args.dry_run:
        ignore_revs.write_text(IGNORE_REVS_HEADER, encoding="utf-8")

    existed = target.is_file()
    old_text = target.read_text(encoding="utf-8") if existed else ""
    new_text, added, already_present = patch_toml(old_text, selected)
    changed = (not existed) or (new_text != old_text)

    if changed and not args.dry_run:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(new_text, encoding="utf-8")

    if args.json:
        print(
            json.dumps(
                {
                    "file": str(target),
                    "created": not existed,
                    "changed": changed,
                    "ignore_revs_created": create_ignore_revs,
                    "dry_run": args.dry_run,
                    "added": added,
                    "already_present": already_present,
                },
                indent=2,
            )
        )
    else:
        status = "dry-run" if args.dry_run else ("created" if not existed else ("updated" if changed else "unchanged"))
        print(f"{status}: {target} (added={len(added)}, present={len(already_present)}, ignore_revs_created={create_ignore_revs})")
    return 0


if __name__ == "__main__":
    sys.exit(main())

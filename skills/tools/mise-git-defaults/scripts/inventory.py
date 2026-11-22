#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import platform
import re
import shutil
import subprocess
import sys
import tomllib

from common import (
    CONFIG_CANDIDATES,
    IGNORE_REVS_FILENAME,
    LOCAL_CANDIDATES,
    VERSION_KEY,
    extract_hook_scripts,
    git_root,
    has_key,
    local_git_config,
    resolve_target,
    selected_entries,
)


def cmd_version(cmd: list[str]) -> str | None:
    if not shutil.which(cmd[0]):
        return None
    res = subprocess.run(cmd, capture_output=True, text=True, check=False)
    out = (res.stdout or res.stderr).strip()
    return out.splitlines()[0] if out else None


def parse_mise_ymd(version_str: str | None) -> tuple[int, int, int] | None:
    if not version_str:
        return None
    m = re.search(r"(\d{4}).(\d+).(\d+)", version_str)
    return (int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only inventory for mise-git-defaults.")
    parser.add_argument("--file", help="Explicit mise config file path.")
    parser.add_argument("--local", action="store_true", help="Check personal/local mise config.")
    parser.add_argument("--minimal", action="store_true", help="Inspect only minimal 4-key set.")
    parser.add_argument("--json", action="store_true", help="Output JSON summary.")
    args = parser.parse_args()

    root = git_root()
    target = resolve_target(root, args.file, args.local)
    selected = selected_entries(args.minimal)

    git_ver = cmd_version(["git", "--version"])
    mise_ver = cmd_version(["mise", "--version"])
    existing_configs = [rel for rel in (*CONFIG_CANDIDATES, *LOCAL_CANDIDATES) if (root / rel).is_file()]

    warnings: list[str] = []
    if not mise_ver:
        warnings.append("mise is not installed in PATH; hook will still be patched and syntax-checked.")

    target_exists = target.is_file()
    hooks_shape = "absent"
    hook_keys_present: list[str] = []
    hook_keys_missing = [e[0] for e in selected]
    experimental_enabled = False

    if target_exists:
        with target.open("rb") as f:
            data = tomllib.load(f)
        experimental_enabled = bool(isinstance(data.get("settings"), dict) and data["settings"].get("experimental") is True)
        hooks = data.get("hooks")
        if isinstance(hooks, dict) and "enter" in hooks:
            hooks_shape = type(hooks["enter"]).__name__
            combined = "\n".join(extract_hook_scripts(data))
            hook_keys_present = [e[0] for e in selected if has_key(combined, e[0])]
            hook_keys_missing = [e[0] for e in selected if not has_key(combined, e[0])]
        elif hooks is not None:
            hooks_shape = "hooks_table_without_enter"

    ymd = parse_mise_ymd(mise_ver)
    if ymd and ymd < (2026, 6, 6) and not experimental_enabled:
        warnings.append(f"mise {ymd[0]}.{ymd[1]}.{ymd[2]} < 2026.6.6 requires [settings] experimental = true for hooks.")

    if not args.local:
        rel_target = str(target.relative_to(root)) if target.is_relative_to(root) else str(target)
        ig = subprocess.run(["git", "check-ignore", "-q", rel_target], cwd=root, check=False)
        if ig.returncode == 0:
            warnings.append(f"Shared target file {rel_target} is gitignored.")

    ignore_revs = root / IGNORE_REVS_FILENAME
    ignore_revs_info: dict[str, object] = {"exists": ignore_revs.is_file(), "path": str(ignore_revs)}
    if ignore_revs.is_file():
        lines = ignore_revs.read_text(encoding="utf-8", errors="replace").splitlines()
        ignore_revs_info["line_count"] = len(lines)
        ignore_revs_info["preview"] = lines[:5]

    git_cfg = local_git_config()
    git_keys_present = [e[0] for e in selected if e[0].lower() in git_cfg]
    git_keys_missing = [e[0] for e in selected if e[0].lower() not in git_cfg]

    report = {
        "root": str(root),
        "target": str(target),
        "target_exists": target_exists,
        "existing_configs": existing_configs,
        "hooks_enter_shape": hooks_shape,
        "hook_keys_present": hook_keys_present,
        "hook_keys_missing": hook_keys_missing,
        "ignore_revs": ignore_revs_info,
        "git_local_keys_present": git_keys_present,
        "git_local_keys_missing": git_keys_missing,
        "git_defaults_version": git_cfg.get(VERSION_KEY.lower()),
        "tools": {
            "git": git_ver,
            "mise": mise_ver,
            "python": platform.python_version(),
        },
        "warnings": warnings,
    }

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"root: {report['root']}")
        print(f"target: {report['target']} (exists={target_exists}, enter={hooks_shape})")
        print(f"ignore-revs: {'exists' if ignore_revs_info['exists'] else 'missing'}")
        print(f"hook keys: {len(hook_keys_present)} present, {len(hook_keys_missing)} missing")
        print(f"git local keys: {len(git_keys_present)} present, {len(git_keys_missing)} missing")
        for w in warnings:
            print(f"warning: {w}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tomllib

from common import (
    IGNORE_REVS_FILENAME,
    VERSION_KEY,
    extract_hook_scripts,
    git_root,
    has_key,
    local_git_config,
    resolve_target,
    selected_entries,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify patched mise enter hook and local git config.")
    parser.add_argument("--file", help="Explicit mise config file path.")
    parser.add_argument("--local", action="store_true", help="Target mise.local.toml / .mise.local.toml.")
    parser.add_argument("--minimal", action="store_true", help="Verify only minimal 4-key set.")
    parser.add_argument("--no-exec", action="store_true", help="Skip running the hook script once.")
    parser.add_argument("--json", action="store_true", help="Output JSON summary.")
    args = parser.parse_args()

    root = git_root()
    target = resolve_target(root, args.file, args.local)
    if not target.is_file():
        raise SystemExit(f"Error: target file not found: {target}")

    with target.open("rb") as f:
        data = tomllib.load(f)

    scripts = extract_hook_scripts(data)
    if not scripts:
        raise SystemExit(f"Error: no hooks.enter script found in {target}")
    hook_sh = "\n".join(scripts)

    selected = selected_entries(args.minimal)
    missing_in_hook = [e[0] for e in selected if not has_key(hook_sh, e[0])]

    sh_check = subprocess.run(["sh", "-n"], input=hook_sh, text=True, capture_output=True, check=False)
    syntax_ok = sh_check.returncode == 0

    mise_available = bool(shutil.which("mise"))
    mise_trusted = None
    mise_config_ok = None
    mise_error = None
    if mise_available:
        t_res = subprocess.run(["mise", "trust", str(target)], cwd=root, capture_output=True, text=True, check=False)
        mise_trusted = t_res.returncode == 0
        c_res = subprocess.run(["mise", "config", "ls"], cwd=root, capture_output=True, text=True, check=False)
        mise_config_ok = c_res.returncode == 0
        if not (mise_trusted and mise_config_ok):
            mise_error = (t_res.stderr or c_res.stderr).strip()

    hook_executed = False
    exec_error = None
    if not args.no_exec and syntax_ok:
        env = os.environ.copy()
        env["MISE_CONFIG_ROOT"] = str(root)
        ex = subprocess.run(["sh", "-e", "-c", hook_sh], cwd=root, env=env, capture_output=True, text=True, check=False)
        hook_executed = ex.returncode == 0
        if not hook_executed:
            exec_error = ex.stderr.strip() or f"Hook exited with status {ex.returncode}"

    ignore_revs_exists = (root / IGNORE_REVS_FILENAME).is_file()
    git_cfg = local_git_config()
    expected_git_keys = [e[0] for e in selected if not (e[3] and not ignore_revs_exists)]
    configured_git_keys = {k: git_cfg[k.lower()] for k in expected_git_keys if k.lower() in git_cfg}
    missing_git_keys = [k for k in expected_git_keys if k.lower() not in git_cfg]

    ok = (
        syntax_ok
        and not missing_in_hook
        and (mise_trusted is not False)
        and (mise_config_ok is not False)
        and (args.no_exec or (hook_executed and not missing_git_keys))
    )

    result = {
        "ok": ok,
        "file": str(target),
        "syntax_ok": syntax_ok,
        "syntax_error": None if syntax_ok else sh_check.stderr.strip(),
        "missing_in_hook": missing_in_hook,
        "mise_available": mise_available,
        "mise_trusted": mise_trusted,
        "mise_config_ok": mise_config_ok,
        "mise_error": mise_error,
        "hook_executed": hook_executed,
        "exec_error": exec_error,
        "git_defaults_version": git_cfg.get(VERSION_KEY.lower()),
        "configured_git_keys": configured_git_keys,
        "missing_git_keys": missing_git_keys,
    }

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"ok={ok} file={target} syntax={syntax_ok} executed={hook_executed} missing_hook={missing_in_hook} missing_git={missing_git_keys}")
        if not syntax_ok:
            print(result["syntax_error"], file=sys.stderr)
        if exec_error:
            print(exec_error, file=sys.stderr)
        if mise_error:
            print(mise_error, file=sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

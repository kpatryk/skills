#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys

from common import absolutize, commit_exists, display_path, effective_config, git_root, parse_revs_file, resolve_revs_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the git-blame ignore-revs setup.")
    parser.add_argument("--file", help="Explicit ignore-revs file path (overrides git config).")
    parser.add_argument("--json", action="store_true", help="Output JSON summary.")
    args = parser.parse_args()

    root = git_root()
    target = resolve_revs_file(root, args.file)
    exists = target.is_file()
    active, malformed = parse_revs_file(target)

    dangling = [sha for sha in active if not commit_exists(sha)]

    effective, origin = effective_config()
    config_ok = bool(effective) and absolutize(root, effective or "") == target

    blame_ok: bool | None = None
    blame_error: str | None = None
    if exists and active:
        tracked = subprocess.run(
            ["git", "ls-files"], cwd=root, capture_output=True, text=True, check=False
        ).stdout.splitlines()
        candidates = [f for f in tracked if f and not f.startswith(".")] or [f for f in tracked if f]
        for probe in candidates[:5]:
            blame = subprocess.run(
                ["git", "blame", "--ignore-revs-file", str(target), "-L", "1,1", "--", probe],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )
            if blame.returncode == 0:
                blame_ok = True
                break
            blame_error = (blame.stderr or f"git blame exited {blame.returncode}").strip()
        if blame_ok is None:
            blame_ok = not candidates
    elif exists:
        blame_ok = True

    ok = bool(exists and not malformed and not dangling and config_ok and blame_ok)

    result: dict[str, object] = {
        "ok": ok,
        "file": str(target),
        "file_display": display_path(root, target),
        "exists": exists,
        "active_count": len(active),
        "malformed": malformed,
        "dangling": dangling,
        "config_effective": effective,
        "config_origin": origin,
        "config_ok": config_ok,
        "blame_ok": blame_ok,
        "blame_error": blame_error,
    }
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"ok={ok} file={display_path(root, target)} active={len(active)} config_ok={config_ok} blame_ok={blame_ok}")
        for line in malformed:
            print(f"malformed: {line}")
        for sha in dangling:
            print(f"dangling: {sha}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

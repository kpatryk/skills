#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys

from common import (
    FORMATTER_SIGNALS,
    config_report,
    display_path,
    git_root,
    parse_revs_file,
    resolve_revs_file,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only inventory for git-blame-ignore-revs.")
    parser.add_argument("--file", help="Explicit ignore-revs file path (overrides git config).")
    parser.add_argument("--json", action="store_true", help="Output JSON summary.")
    args = parser.parse_args()

    root = git_root()
    cfg = config_report()
    target = resolve_revs_file(root, args.file)

    branch_res = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    branch = branch_res.stdout.strip() if branch_res.returncode == 0 else "(detached)"

    count_res = subprocess.run(
        ["git", "rev-list", "--count", "HEAD"], capture_output=True, text=True, check=False
    )
    commit_count = int(count_res.stdout.strip()) if count_res.returncode == 0 else 0

    exists = target.is_file()
    active, malformed = parse_revs_file(target)
    tracked = False
    ignored = False
    if exists:
        rel = display_path(root, target)
        tracked = (
            subprocess.run(["git", "ls-files", "--error-unmatch", rel], cwd=root, capture_output=True, check=False).returncode
            == 0
        )
        ignored = (
            subprocess.run(["git", "check-ignore", "-q", rel], cwd=root, check=False).returncode == 0
        )

    signals = [s for s in FORMATTER_SIGNALS if (root / s).is_file()]

    warnings: list[str] = []
    if not cfg["effective"]:
        warnings.append("blame.ignoreRevsFile is not set in git config.")
    elif not exists:
        warnings.append(f"Configured file {display_path(root, target)} does not exist.")
    if malformed:
        warnings.append(f"{len(malformed)} malformed line(s) in {display_path(root, target)}.")
    if ignored:
        warnings.append(f"{display_path(root, target)} is gitignored and will not be shared.")

    report: dict[str, object] = {
        "root": str(root),
        "branch": branch,
        "commit_count": commit_count,
        "config": cfg,
        "file": str(target),
        "file_display": display_path(root, target),
        "file_exists": exists,
        "file_tracked": tracked,
        "file_ignored": ignored,
        "active_count": len(active),
        "malformed_count": len(malformed),
        "malformed_preview": malformed[:5],
        "formatter_signals": signals,
        "warnings": warnings,
    }

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"root: {root} (branch={branch}, commits={commit_count})")
        print(f"config: effective={cfg['effective']} origin={cfg['origin']}")
        print(f"file: {display_path(root, target)} (exists={exists}, tracked={tracked}, active={len(active)})")
        for w in warnings:
            print(f"warning: {w}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

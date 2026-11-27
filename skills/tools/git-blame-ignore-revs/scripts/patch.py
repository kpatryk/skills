#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys

from common import (
    HEADER,
    commit_exists,
    display_path,
    git_root,
    parse_revs_file,
    resolve_revs_file,
    run_git,
    scan_history,
    scoped_config,
)


def expand_sha(token: str) -> str | None:
    res = run_git("rev-parse", "--verify", f"{token}^{{commit}}")
    sha = res.stdout.strip()
    if res.returncode != 0 or not sha:
        return None
    return sha


def main() -> int:
    parser = argparse.ArgumentParser(description="Add formatting commits to the git-blame ignore-revs file.")
    parser.add_argument("--file", help="Explicit ignore-revs file path (overrides git config).")
    parser.add_argument("--auto-high", action="store_true", help="Add all high-confidence formatting commits.")
    parser.add_argument("--add", nargs="*", default=[], help="Explicit commit SHAs to add (approved medium-confidence).")
    parser.add_argument("--create", action="store_true", help="Create the ignore-revs file if missing (requires user approval).")
    parser.add_argument("--no-config", action="store_true", help="Do not update git config.")
    parser.add_argument("--dry-run", action="store_true", help="Report without writing.")
    parser.add_argument("--json", action="store_true", help="Output JSON summary.")
    args = parser.parse_args()

    root = git_root()
    target = resolve_revs_file(root, args.file)
    existed = target.is_file()
    if not existed and not args.create and not args.dry_run:
        raise SystemExit(
            f"Error: {display_path(root, target)} does not exist. "
            "Ask the user for approval to create it, then re-run with --create."
        )

    active, _ = parse_revs_file(target)
    existing = set(active)

    requested: list[str] = []
    for token in args.add:
        sha = expand_sha(token)
        if sha is None or not commit_exists(sha):
            raise SystemExit(f"Error: cannot resolve commit '{token}'.")
        if sha not in existing and sha not in requested:
            requested.append(sha)

    auto: list[dict[str, object]] = []
    if args.auto_high:
        result = scan_history(existing | set(requested))
        raw = result["to_add"]
        assert isinstance(raw, list)
        auto = [e for e in raw if isinstance(e, dict)]

    additions = requested + [str(e["sha"]) for e in auto if str(e["sha"]) not in existing and str(e["sha"]) not in requested]
    if not additions and not (args.create and not existed):
        summary = {"file": str(target), "changed": False, "added": [], "config_updated": False}
        if args.json:
            print(json.dumps(summary, indent=2))
        else:
            print(f"unchanged: {display_path(root, target)} (nothing new to add)")
        return 0

    subjects: dict[str, str] = {}
    dates: dict[str, str] = {}
    if auto:
        for e in auto:
            subjects[str(e["sha"])] = str(e["subject"])
            dates[str(e["sha"])] = str(e["date"])
    for sha in requested:
        if sha not in subjects:
            res = run_git("show", "-s", "--format=%ad%x01%s", "--date=short", sha)
            if res.returncode == 0 and "\x01" in res.stdout:
                date, _, subject = res.stdout.strip().partition("\x01")
                dates[sha] = date
                subjects[sha] = subject

    changed = bool(additions) or (not existed)
    config_updated = False
    if changed and not args.dry_run:
        if not existed:
            target.parent.mkdir(parents=True, exist_ok=True)
        lines: list[str] = []
        if existed:
            lines = target.read_text(encoding="utf-8", errors="replace").splitlines()
        if not existed or not any(line.strip() for line in lines):
            lines = HEADER.rstrip("\n").splitlines()
        seen = set(existing)
        for sha in additions:
            if sha in seen:
                continue
            seen.add(sha)
            short = sha[:12]
            lines.append(f"# {short} {dates.get(sha, '')} {subjects.get(sha, '')}".rstrip())
            lines.append(sha)
        target.write_text("\n".join(lines).rstrip("\n") + "\n", encoding="utf-8")

        if not args.no_config:
            rel = display_path(root, target)
            if scoped_config("local") != rel:
                res = run_git("config", "--local", "blame.ignoreRevsFile", rel)
                if res.returncode != 0:
                    raise SystemExit(f"Error: failed to set local blame.ignoreRevsFile: {res.stderr.strip()}")
                config_updated = True

    summary = {
        "file": str(target),
        "created": not existed,
        "changed": changed,
        "dry_run": args.dry_run,
        "added": additions,
        "config_updated": config_updated,
    }
    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        status = "dry-run" if args.dry_run else ("created" if not existed else "updated")
        print(f"{status}: {display_path(root, target)} (added={len(additions)}, config_updated={config_updated})")
    return 0


if __name__ == "__main__":
    sys.exit(main())

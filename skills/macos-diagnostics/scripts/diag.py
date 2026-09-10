#!/usr/bin/env python3
"""Scaffold and maintain the macOS diagnostics workspace.

Subcommands:
    init       Create diagnostics/working/<slug>/ with traces and a report stub.
    log        Append a timestamped block to a trace file (reads stdin).
    finalize   Move a finished issue into resolved/ or unresolved/ and update index.md.
    status     Show where an issue currently lives.

Only the Python standard library is used.

Examples:
    python3 diag.py init --root diagnostics --slug m2-battery-drain --title "Overnight battery drain"
    pmset -g log | python3 diag.py log --slug m2-battery-drain --stream system --label "pmset -g log"
    python3 diag.py finalize --slug m2-battery-drain --status resolved \
        --machine "MacBook Pro (Apple Silicon)" --os "macOS 15.5" \
        --description "Overnight drain from runaway mdworker"
"""

from __future__ import annotations

import argparse
import shutil
import sys
from datetime import date, datetime
from pathlib import Path

TRACE_FILES = {
    "command": "command_outputs.log",
    "system": "system_logs.log",
}

INDEX_HEADING = {
    "resolved": "# Resolved MacBook Issues Index",
    "unresolved": "# Unresolved MacBook Issues Index",
}

INDEX_TABLE_HEADER = """| Issue / Slug | Description | Machine / OS | Date | Action |
|--------------|-------------|--------------|------|--------|
"""

REPORT_STUB = """# Diagnostic Report: {title}

- **Status**: [RESOLVED | UNRESOLVED]
- **Target Machine**: [MacBook Model, Architecture, macOS Version]
- **Issue Folder**: `{slug}`
- **Navigation**: [← Back to Master Index](../index.md)

---

## 1. Executive Summary

[TODO: concise summary of the problem, findings, outcome, and whether the root
cause was confirmed or remains a hypothesis.]

## 2. Root Cause Analysis (RCA)

- **Primary Root Cause**: [TODO]
- **Trigger**: [TODO]

## 3. Chronological Attempts Log

| Attempt # | Target / Hypothesis | Command Executed | Purpose / Description | Result |
|-----------|---------------------|------------------|-----------------------|--------|
| 1 |  |  |  |  |

## 4. Raw Logs & Traces

All raw diagnostic outputs are preserved in:

- `./traces/system_logs.log`
- `./traces/command_outputs.log`

## 5. Incidental / Secondary Findings

- [TODO]

## 6. Lessons Learned & Preventive Recommendations

- **Lesson**: [TODO]
- **Preventive Maintenance**: [TODO]

---
[← Return to Index](../index.md)
"""


def _stamp() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _trace_path(root: Path, slug: str, stream: str) -> Path:
    for area in ("working", "resolved", "unresolved"):
        candidate = root / area / slug / "traces" / TRACE_FILES[stream]
        if candidate.exists():
            return candidate
    return root / "working" / slug / "traces" / TRACE_FILES[stream]


def cmd_init(args: argparse.Namespace) -> int:
    root = Path(args.root).expanduser().resolve()
    working = root / "working" / args.slug
    traces = working / "traces"
    traces.mkdir(parents=True, exist_ok=True)

    created: list[str] = []
    for name in TRACE_FILES.values():
        path = traces / name
        if not path.exists():
            path.write_text(f"# {name} — created {_stamp()}\n", encoding="utf-8")
            created.append(str(path.relative_to(root)))

    report = working / "report.md"
    if not report.exists():
        report.write_text(
            REPORT_STUB.format(title=args.title or args.slug, slug=args.slug),
            encoding="utf-8",
        )
        created.append(str(report.relative_to(root)))

    print(f"Workspace ready: {working}")
    if created:
        print("Created:")
        for item in created:
            print(f"  - {item}")
    else:
        print("Already existed; nothing overwritten.")
    print(f"\nNext: append evidence, e.g.")
    print(f"  <command> | python3 scripts/diag.py log --root {args.root} "
          f"--slug {args.slug} --stream command --label \"<what you ran>\"")
    return 0


def cmd_log(args: argparse.Namespace) -> int:
    root = Path(args.root).expanduser().resolve()
    content = sys.stdin.read()
    path = _trace_path(root, args.slug, args.stream)
    path.parent.mkdir(parents=True, exist_ok=True)

    label = args.label or "(no label)"
    header = (
        "=" * 78
        + f"\n[{_stamp()}] {label}\n"
        + "-" * 78
        + "\n"
    )
    with path.open("a", encoding="utf-8") as fh:
        fh.write(header)
        fh.write(content)
        if content and not content.endswith("\n"):
            fh.write("\n")

    location = path
    print(f"Appended {len(content)} chars to {location}")
    return 0


def cmd_finalize(args: argparse.Namespace) -> int:
    root = Path(args.root).expanduser().resolve()
    working = root / "working" / args.slug
    area = "resolved" if args.status == "resolved" else "unresolved"
    destination = root / area / args.slug

    if working.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            shutil.rmtree(destination)
        shutil.move(str(working), str(destination))
        moved = True
    elif destination.exists():
        moved = False  # idempotent re-run
    else:
        print(f"Error: no working or {area} folder found for slug '{args.slug}'", file=sys.stderr)
        return 1

    report = destination / "report.md"
    if not report.exists():
        report.write_text(
            REPORT_STUB.format(title=args.slug, slug=args.slug), encoding="utf-8"
        )
        print(f"Warning: report.md was missing; wrote a stub at {report}", file=sys.stderr)

    # Ensure traces exist so the report's references are valid.
    traces = destination / "traces"
    traces.mkdir(parents=True, exist_ok=True)
    for name in TRACE_FILES.values():
        (traces / name).touch(exist_ok=True)

    index = root / area / "index.md"
    if not index.exists():
        index.write_text(
            INDEX_HEADING[area] + "\n\n" + INDEX_TABLE_HEADER,
            encoding="utf-8",
        )

    link = f"./{args.slug}/report.md"
    existing = index.read_text(encoding="utf-8")
    if link not in existing:
        machine_os = args.machine or "[machine]"
        if args.os:
            machine_os = f"{machine_os} / {args.os}"
        row = (
            f"| [{args.slug}]({link}) | {args.description or '[description]'} "
            f"| {machine_os} | {args.date} | [View Full Report]({link}) |\n"
        )
        with index.open("a", encoding="utf-8") as fh:
            fh.write(row)

    verb = "Moved" if moved else "Already finalized"
    print(f"{verb}: {args.slug} -> {destination}")
    print(f"Report:  {report}")
    print(f"Index:   {index}")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    root = Path(args.root).expanduser().resolve()
    for area in ("working", "resolved", "unresolved"):
        candidate = root / area / args.slug
        if candidate.exists():
            print(f"{args.slug}: {area} ({candidate})")
            return 0
    print(f"{args.slug}: not found under {root}")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="macOS diagnostics workspace helper")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--root", default="diagnostics",
        help="Diagnostics root directory (default: diagnostics)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", parents=[common], help="Scaffold a new issue workspace")
    p_init.add_argument("--slug", required=True)
    p_init.add_argument("--title", default="", help="Human title for the report")
    p_init.set_defaults(func=cmd_init)

    p_log = sub.add_parser("log", parents=[common], help="Append a trace block from stdin")
    p_log.add_argument("--slug", required=True)
    p_log.add_argument("--stream", choices=sorted(TRACE_FILES), default="command")
    p_log.add_argument("--label", default="", help="Command or description for this block")
    p_log.set_defaults(func=cmd_log)

    p_fin = sub.add_parser("finalize", parents=[common], help="File the issue as resolved/unresolved")
    p_fin.add_argument("--slug", required=True)
    p_fin.add_argument("--status", choices=("resolved", "unresolved"), required=True)
    p_fin.add_argument("--machine", default="")
    p_fin.add_argument("--os", default="")
    p_fin.add_argument("--description", default="")
    p_fin.add_argument("--date", default=date.today().isoformat())
    p_fin.set_defaults(func=cmd_finalize)

    p_status = sub.add_parser("status", parents=[common], help="Locate an issue by slug")
    p_status.add_argument("--slug", required=True)
    p_status.set_defaults(func=cmd_status)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

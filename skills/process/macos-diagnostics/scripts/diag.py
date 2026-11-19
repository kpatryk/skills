#!/usr/bin/env python3
"""Maintain the macOS diagnostics workspace (standard library only).

diag.py init --slug m2-battery-drain
pmset -g log | diag.py log --slug m2-battery-drain --stream system --label "pmset -g log"
diag.py finalize --slug m2-battery-drain --status resolved --description "Overnight drain"
"""

import argparse
import os
import platform
import re
import shutil
import sys
from datetime import date, datetime
from pathlib import Path

TRACE_FILES = {"command": "command_outputs.log", "system": "system_logs.log"}
INDEX_HEADING = {"resolved": "# Resolved MacBook Issues Index", "unresolved": "# Unresolved MacBook Issues Index"}
INDEX_TABLE_HEADER = "| Issue / Slug | Description | Machine / OS | Date | Action |\n|--------------|-------------|--------------|------|--------|\n"
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
DEFAULT_ROOT = os.environ.get("MACOS_DIAGNOSTICS_ROOT") or "diagnostics"


def _slug(value: str) -> str:
    if not SLUG_RE.fullmatch(value):
        raise argparse.ArgumentTypeError("slug must be kebab-case: ^[a-z0-9][a-z0-9-]*$")
    return value


def _trace_path(root: Path, slug: str, stream: str) -> Path:
    path = root / "working" / slug / "traces" / TRACE_FILES[stream]
    if not path.is_file():
        raise SystemExit(f"Error: no trace at {path}; run 'init --slug {slug}' first")
    return path


def _preflight(folder: Path, status: str, slug: str) -> None:
    report = folder / "report.md"
    if not report.is_file():
        raise SystemExit(f"Error: missing {report}")
    lines = report.read_text(encoding="utf-8").splitlines()
    line = next((ln for ln in lines if ln.strip().startswith("- **Status**:")), "")
    value = line.split("**Status**:", 1)[-1].strip().strip("[]*_` ")
    if value.split()[:1] != [status.upper()] or "|" in value:
        raise SystemExit(f"Error: {report} must say '- **Status**: {status.upper()}'")
    slug_line = next((ln for ln in lines if ln.strip().startswith("- **Issue Folder**:")), "")
    slug_value = slug_line.split("**Issue Folder**:", 1)[-1].strip().strip("[]*_` ").strip("/")
    if slug_value and slug_value != slug:
        raise SystemExit(f"Error: {report} must say '- **Issue Folder**: `{slug}`'")
    for name in TRACE_FILES.values():
        trace = folder / "traces" / name
        if not trace.is_file() or not trace.stat().st_size:
            raise SystemExit(f"Error: trace {trace} is empty; log evidence before finalizing")


def cmd_init(args: argparse.Namespace) -> int:
    traces = Path(args.root).expanduser().resolve() / "working" / args.slug / "traces"
    traces.mkdir(parents=True, exist_ok=True)
    for name in TRACE_FILES.values():
        (traces / name).touch(exist_ok=True)
    print(traces.parent)
    return 0


def cmd_log(args: argparse.Namespace) -> int:
    path = _trace_path(Path(args.root).expanduser().resolve(), args.slug, args.stream)
    content = sys.stdin.read()
    stamp = datetime.now().astimezone().isoformat(timespec="seconds")
    header = "=" * 78 + f"\n[{stamp}] {args.label or '(no label)'}\n" + "-" * 78 + "\n"
    with path.open("a", encoding="utf-8") as fh:
        fh.write(header + content)
        if content and not content.endswith("\n"):
            fh.write("\n")
    print(f"Appended {len(content)} chars to {path}")
    return 0


def cmd_finalize(args: argparse.Namespace) -> int:
    root = Path(args.root).expanduser().resolve()
    working, destination = root / "working" / args.slug, root / args.status / args.slug
    moved = working.is_dir()
    if moved:
        if destination.exists():
            raise SystemExit(f"Error: {destination} already exists; move or remove it manually")
        _preflight(working, args.status, args.slug)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(working), str(destination))
    elif destination.is_dir():
        _preflight(destination, args.status, args.slug)
    else:
        raise SystemExit(f"Error: no workspace for '{args.slug}' under working/ or {args.status}/")

    index = root / args.status / "index.md"
    if not index.exists():
        index.write_text(f"{INDEX_HEADING[args.status]}\n\n{INDEX_TABLE_HEADER}", encoding="utf-8")
    text = index.read_text(encoding="utf-8")
    link = f"./{args.slug}/report.md"
    if link not in text:
        description = " ".join((args.description or args.slug).replace("|", "\\|").split())
        machine = f"{platform.machine()} / macOS {platform.mac_ver()[0] or 'unknown'}"
        row = f"| [{args.slug}]({link}) | {description} | {machine} | {date.today()} | [View Full Report]({link}) |\n"
        index.write_text(text + ("" if text.endswith("\n") else "\n") + row, encoding="utf-8")
    print(f"{'Moved' if moved else 'Already finalized'}: {args.slug} -> {destination}")
    print(f"Report: {destination / 'report.md'} | Index: {index}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="macOS diagnostics workspace helper")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root", default=DEFAULT_ROOT, help="Diagnostics root (default: $MACOS_DIAGNOSTICS_ROOT or diagnostics)")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("init", parents=[common], help="Scaffold working/<slug>/ with empty traces")
    p.add_argument("--slug", required=True, type=_slug)
    p.set_defaults(func=cmd_init)
    p = sub.add_parser("log", parents=[common], help="Append a trace block from stdin")
    p.add_argument("--slug", required=True, type=_slug)
    p.add_argument("--stream", choices=sorted(TRACE_FILES), default="command")
    p.add_argument("--label", default="", help="Command or description for this block")
    p.set_defaults(func=cmd_log)
    p = sub.add_parser("finalize", parents=[common], help="Validate and file the issue as resolved/unresolved")
    p.add_argument("--slug", required=True, type=_slug)
    p.add_argument("--status", choices=("resolved", "unresolved"), required=True)
    p.add_argument("--description", default="", help="One-line index description (default: slug)")
    p.set_defaults(func=cmd_finalize)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

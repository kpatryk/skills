#!/usr/bin/env python3
"""Find broken skill symlinks in global agent skill directories.

Scans the global (personal) skill locations for every agent in the
vercel-labs/skills registry
(https://github.com/vercel-labs/skills/blob/main/docs/agents.md),
prints a human-readable preview of the broken symlinks found, and asks
for confirmation before removing anything.

Only the Python standard library is used. Blocking directory scans are
offloaded with asyncio.to_thread so all roots are scanned concurrently.

Exit codes:
    0  no broken symlinks found (or all were removed successfully)
    1  broken symlinks found (dry run, declined, or removal failed)
    2  usage error (argparse exits 2 on its own for bad flags)
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

REGISTRY_URL = "https://github.com/vercel-labs/skills/blob/main/docs/agents.md"


@dataclass(frozen=True)
class AgentSkills:
    """One registry row: installer flags, display label, global path."""

    flags: tuple[str, ...]
    label: str
    global_path: str
    env_var: str | None = None
    env_suffix: str | None = None


# Global paths mirror the registry's "Global Path" column. "N/A
# (project-only)" rows (Eve, PromptScript) have no global dir and are
# intentionally absent here.
AGENTS: tuple[AgentSkills, ...] = (
    AgentSkills(("aider-desk",), "AiderDesk", "~/.aider-desk/skills"),
    AgentSkills(
        ("amp", "replit", "universal"),
        "Amp / Replit / Universal",
        "~/.config/agents/skills",
    ),
    AgentSkills(("antigravity",), "Antigravity", "~/.gemini/antigravity/skills"),
    AgentSkills(("antigravity-cli",), "Antigravity CLI", "~/.gemini/antigravity-cli/skills"),
    AgentSkills(("astrbot",), "AstrBot", "~/.astrbot/data/skills"),
    AgentSkills(("autohand-code",), "Autohand Code CLI", "~/.autohand/skills"),
    AgentSkills(("augment",), "Augment", "~/.augment/skills"),
    AgentSkills(("bob",), "IBM Bob", "~/.bob/skills"),
    AgentSkills(
        ("claude-code",),
        "Claude Code",
        "~/.claude/skills",
        env_var="CLAUDE_CONFIG_DIR",
        env_suffix="skills",
    ),
    AgentSkills(("openclaw",), "OpenClaw", "~/.openclaw/skills"),
    AgentSkills(
        (
            "cline",
            "codex",
            "dexto",
            "fx",
            "kimi-code-cli",
            "loaf",
            "pi",
            "sarvam-code",
            "warp",
            "zed",
        ),
        "Cline / Codex / Dexto / fx / Kimi / Loaf / Pi / Sarvam / Warp / Zed",
        "~/.agents/skills",
    ),
    AgentSkills(("codearts-agent",), "CodeArts Agent", "~/.codeartsdoer/skills"),
    AgentSkills(("codebuddy",), "CodeBuddy", "~/.codebuddy/skills"),
    AgentSkills(("codemaker",), "Codemaker", "~/.codemaker/skills"),
    AgentSkills(("codestudio",), "Code Studio", "~/.codestudio/skills"),
    AgentSkills(("command-code",), "Command Code", "~/.commandcode/skills"),
    AgentSkills(("continue",), "Continue", "~/.continue/skills"),
    AgentSkills(("cortex",), "Cortex Code", "~/.snowflake/cortex/skills"),
    AgentSkills(("crush",), "Crush", "~/.config/crush/skills"),
    AgentSkills(("cursor",), "Cursor", "~/.cursor/skills"),
    AgentSkills(("deepagents",), "Deep Agents", "~/.deepagents/agent/skills"),
    AgentSkills(("devin",), "Devin for Terminal", "~/.config/devin/skills"),
    AgentSkills(("droid",), "Droid", "~/.factory/skills"),
    AgentSkills(("firebender",), "Firebender", "~/.firebender/skills"),
    AgentSkills(("forgecode",), "ForgeCode", "~/.forge/skills"),
    AgentSkills(("gemini-cli",), "Gemini CLI", "~/.gemini/skills"),
    AgentSkills(
        ("github-copilot",),
        "GitHub Copilot",
        "~/.copilot/skills",
        env_var="COPILOT_HOME",
        env_suffix="skills",
    ),
    AgentSkills(("goose",), "Goose", "~/.config/goose/skills"),
    AgentSkills(("grok",), "Grok Build", "~/.grok/skills"),
    AgentSkills(("hermes-agent",), "Hermes Agent", "~/.hermes/skills"),
    AgentSkills(("inference-sh",), "inference.sh", "~/.inferencesh/skills"),
    AgentSkills(("jazz",), "Jazz", "~/.jazz/skills"),
    AgentSkills(("junie",), "Junie", "~/.junie/skills"),
    AgentSkills(("iflow-cli",), "iFlow CLI", "~/.iflow/skills"),
    AgentSkills(("kilo",), "Kilo Code", "~/.kilo/skills"),
    AgentSkills(("kimchi",), "Kimchi", "~/.config/kimchi/harness/skills"),
    AgentSkills(
        ("kiro-cli",),
        "Kiro CLI",
        "~/.kiro/skills",
        env_var="KIRO_HOME",
        env_suffix="skills",
    ),
    AgentSkills(("kode",), "Kode", "~/.kode/skills"),
    AgentSkills(("lingma",), "Lingma", "~/.lingma/skills"),
    AgentSkills(("mcpjam",), "MCPJam", "~/.mcpjam/skills"),
    AgentSkills(("minimax-code",), "MiniMax Code", "~/.minimax/skills"),
    AgentSkills(("mistral-vibe",), "Mistral Vibe", "~/.vibe/skills"),
    AgentSkills(("moxby",), "Moxby", "~/.moxby/skills"),
    AgentSkills(("mux",), "Mux", "~/.mux/skills"),
    AgentSkills(("opencode",), "OpenCode", "~/.config/opencode/skills"),
    AgentSkills(("openhands",), "OpenHands", "~/.openhands/skills"),
    AgentSkills(("ona",), "Ona", "~/.ona/skills"),
    AgentSkills(("posit-assistant",), "Posit Assistant", "~/.posit/assistant/skills"),
    AgentSkills(("qoder",), "Qoder", "~/.qoder/skills"),
    AgentSkills(("qoder-cn",), "Qoder CN", "~/.qoder-cn/skills"),
    AgentSkills(("qwen-code",), "Qwen Code", "~/.qwen/skills"),
    AgentSkills(("reasonix",), "Reasonix", "~/.reasonix/skills"),
    AgentSkills(("rovodev",), "Rovo Dev", "~/.rovodev/skills"),
    AgentSkills(("roo",), "Roo Code", "~/.roo/skills"),
    AgentSkills(("tabnine-cli",), "Tabnine CLI", "~/.tabnine/agent/skills"),
    AgentSkills(("terramind",), "Terramind", "~/.terramind/skills"),
    AgentSkills(("tinycloud",), "Tinycloud", "~/.tinycloud/skills"),
    AgentSkills(("trae",), "Trae", "~/.trae/skills"),
    AgentSkills(("trae-cn",), "Trae CN", "~/.trae-cn/skills"),
    AgentSkills(("windsurf",), "Windsurf", "~/.codeium/windsurf/skills"),
    AgentSkills(("zcode",), "ZCode", "~/.zcode/skills"),
    AgentSkills(("zencoder", "zenflow"), "Zencoder / Zenflow", "~/.zencoder/skills"),
    AgentSkills(("neovate",), "Neovate", "~/.neovate/skills"),
    AgentSkills(("pochi",), "Pochi", "~/.pochi/skills"),
    AgentSkills(("adal",), "AdaL", "~/.adal/skills"),
)


@dataclass
class BrokenLink:
    """A dangling symlink found under a scanned skill root."""

    label: str
    link: Path
    target: str


@dataclass
class ScanRoot:
    """An existing global skill dir with the agent labels mapped to it."""

    labels: list[str] = field(default_factory=list)
    path: Path = field(default_factory=Path)


@dataclass(frozen=True)
class Colors:
    red: str = ""
    green: str = ""
    yellow: str = ""
    bold: str = ""
    reset: str = ""


def detect_colors() -> Colors:
    if os.environ.get("NO_COLOR") or os.environ.get("TERM") == "dumb" or not sys.stdout.isatty():
        return Colors()
    return Colors(
        red="\033[31m",
        green="\033[32m",
        yellow="\033[33m",
        bold="\033[1m",
        reset="\033[0m",
    )


def shorten_home(path: Path) -> str:
    try:
        return f"~/{path.relative_to(Path.home())}"
    except ValueError:
        return str(path)


def expand_global_path(template: str) -> Path:
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg and (template == "~/.config" or template.startswith("~/.config/")):
        return Path(xdg).expanduser() / template[len("~/.config") :].lstrip("/")
    return Path(template).expanduser()


def resolve_entry(entry: AgentSkills) -> Path:
    if entry.env_var and os.environ.get(entry.env_var):
        base = Path(os.environ[entry.env_var]).expanduser()
        return base / (entry.env_suffix or "")
    return expand_global_path(entry.global_path)


def select_entries(agent_filter: list[str] | None) -> list[AgentSkills]:
    if not agent_filter:
        return list(AGENTS)
    wanted: list[str] = []
    for group in agent_filter:
        wanted.extend(t.strip().lower() for t in group.split(",") if t.strip())
    unknown = [token for token in wanted if not any(token in e.flags or token == e.label.lower() for e in AGENTS)]
    if unknown:
        valid = sorted(flag for e in AGENTS for flag in e.flags)
        raise ValueError(f"unknown agent(s): {', '.join(unknown)}\nvalid --agent values: {', '.join(valid)}")
    return [e for e in AGENTS if any(t in e.flags or t == e.label.lower() for t in wanted)]


def collect_roots(entries: list[AgentSkills], verbose: bool) -> list[ScanRoot]:
    by_key: dict[str, ScanRoot] = {}
    for entry in entries:
        path = resolve_entry(entry)
        if not path.is_dir():
            if verbose:
                print(
                    f"skip (missing): {entry.label}: {shorten_home(path)}",
                    file=sys.stderr,
                )
            continue
        key = str(path.resolve())
        if key in by_key:
            existing = by_key[key]
            if entry.label not in existing.labels:
                existing.labels.append(entry.label)
            if verbose:
                print(
                    f"skip (duplicate of {existing.labels[0]}): {entry.label}: {shorten_home(path)}",
                    file=sys.stderr,
                )
            continue
        by_key[key] = ScanRoot(labels=[entry.label], path=path)
        if verbose:
            print(f"scan: {entry.label}: {shorten_home(path)}", file=sys.stderr)
    return [by_key[key] for key in sorted(by_key)]


def find_broken(root: Path) -> list[tuple[Path, str]]:
    """Blocking walk: dangling symlinks directly under root (no -L descent)."""
    found: list[tuple[Path, str]] = []
    stack = [root]
    while stack:
        current = stack.pop()
        try:
            with os.scandir(current) as it:
                entries = list(it)
        except OSError:
            continue
        for entry in entries:
            try:
                is_link = entry.is_symlink()
            except OSError:
                continue
            if is_link:
                if not os.path.exists(entry.path):
                    try:
                        target = os.readlink(entry.path)
                    except OSError:
                        target = "(unreadable)"
                    found.append((Path(entry.path), target))
            else:
                try:
                    if entry.is_dir(follow_symlinks=False):
                        stack.append(Path(entry.path))
                except OSError:
                    continue
    found.sort(key=lambda item: str(item[0]))
    return found


async def scan_roots(roots: list[ScanRoot]) -> list[BrokenLink]:
    semaphore = asyncio.Semaphore(32)

    async def _one(root: ScanRoot) -> list[BrokenLink]:
        async with semaphore:
            pairs = await asyncio.to_thread(find_broken, root.path)
        label = " / ".join(root.labels)
        return [BrokenLink(label, link, target) for link, target in pairs]

    groups = await asyncio.gather(*(_one(root) for root in roots))
    return [link for group in groups for link in group]


async def remove_links(links: list[BrokenLink]) -> int:
    async def _one(link: BrokenLink) -> tuple[BrokenLink, str | None]:
        try:
            await asyncio.to_thread(link.link.unlink)
        except OSError as exc:
            return (link, str(exc))
        return (link, None)

    return await asyncio.gather(*(_one(link) for link in links))


def ask_confirmation(count: int) -> bool:
    prompt = f"Remove all {count} broken symlink(s)? [y/N] "
    answer: str | None = None
    if sys.stdin.isatty():
        try:
            answer = input(prompt)
        except (EOFError, OSError):
            answer = ""
    else:
        try:
            with open("/dev/tty", "r+") as tty:
                tty.write(prompt)
                tty.flush()
                answer = tty.readline()
        except OSError:
            answer = None
    if answer is None:
        print(
            "Not a tty: refusing to prompt. Re-run with --yes to remove, or --dry-run to report only.",
            file=sys.stderr,
        )
        return False
    return answer.strip().lower() in ("y", "yes")


def print_report(broken: list[BrokenLink], colors: Colors) -> None:
    count = len(broken)
    print(f"{colors.bold}{colors.yellow}Found {count} broken skill symlink(s) to be removed:{colors.reset}\n")
    grouped: dict[str, list[BrokenLink]] = {}
    for item in broken:
        grouped.setdefault(item.label, []).append(item)
    for label, items in grouped.items():
        print(f"{label} ({len(items)}):")
        for item in items:
            print(f"  {shorten_home(item.link)} {colors.red}->{colors.reset} {item.target}")
    print()


def print_agents() -> None:
    width = max(len(",".join(e.flags)) for e in AGENTS)
    for entry in AGENTS:
        print(f"{','.join(entry.flags):<{width}}  {entry.label}  {entry.global_path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Preview broken global skill symlinks and remove them only after confirmation.")
    parser.add_argument("--yes", "-y", action="store_true", help="Remove without prompting")
    parser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="Preview only; never remove anything",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show scanned and skipped directories",
    )
    parser.add_argument(
        "--agent",
        action="append",
        default=None,
        help="Limit to agent(s) by --agent flag (repeatable, comma-separated)",
    )
    parser.add_argument("--list-agents", action="store_true", help="List supported agents and exit")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    colors = detect_colors()

    if args.list_agents:
        print_agents()
        return 0

    try:
        entries = select_entries(args.agent)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    if args.yes and args.dry_run:
        print("Error: --yes and --dry-run are mutually exclusive.", file=sys.stderr)
        return 2

    roots = collect_roots(entries, verbose=args.verbose)
    if not roots:
        print("No global skill directories found. Nothing to check.")
        return 0

    broken = asyncio.run(scan_roots(roots))
    if not broken:
        print(f"{colors.green}OK:{colors.reset} no broken skill symlinks found ({len(roots)} location(s) scanned).")
        return 0

    print_report(broken, colors)

    if args.dry_run:
        print("Dry run: nothing removed. Re-run without --dry-run to clean up.")
        return 1

    if not args.yes and not ask_confirmation(len(broken)):
        print("Aborted. Nothing removed.")
        return 1

    failures = 0
    for item, error in asyncio.run(remove_links(broken)):
        if error is None:
            print(f"{colors.green}Removed:{colors.reset} {shorten_home(item.link)}")
        else:
            failures += 1
            print(
                f"{colors.red}Failed:{colors.reset} {shorten_home(item.link)}: {error}",
                file=sys.stderr,
            )

    if failures:
        print(
            f"{colors.red}Done with errors:{colors.reset} {failures} of {len(broken)} removal(s) failed.",
            file=sys.stderr,
        )
        return 1
    print(f"Done. Removed {len(broken)} broken symlink(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

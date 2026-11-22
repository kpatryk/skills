from __future__ import annotations

import re
import subprocess
from pathlib import Path

CONFIG_CANDIDATES = (
    "mise.toml",
    ".mise.toml",
    ".config/mise.toml",
    ".mise/config.toml",
    "mise/config.toml",
)
LOCAL_CANDIDATES = ("mise.local.toml", ".mise.local.toml")
IGNORE_REVS_FILENAME = ".git-blame-ignore-revs"
IGNORE_REVS_HEADER = "# Bulk formatting commits excluded from git blame.\n# Add full commit SHAs below, one per line.\n"
VERSION_KEY = "mise.gitDefaultsVersion"
MINIMAL_COUNT = 4
ENTRIES: list[tuple[str, str, str, bool]] = [
    ("blame.ignoreRevsFile", IGNORE_REVS_FILENAME, "Skip bulk reformatting commits in git blame", True),
    ("diff.algorithm", "histogram", "Clearer diffs for moved code blocks", False),
    ("merge.conflictstyle", "zdiff3", "Show common ancestor in conflict markers", False),
    ("rerere.enabled", "true", "Remember resolved conflicts for reuse", False),
    ("rerere.autoUpdate", "true", "Auto-stage reused conflict resolutions", False),
    ("fetch.prune", "true", "Prune deleted remote branches on fetch", False),
    ("push.autoSetupRemote", "true", "Set upstream on first push automatically", False),
    ("pull.rebase", "true", "Replay local commits on pull for linear history", False),
    ("commit.verbose", "true", "Show diff in commit message editor", False),
    ("column.ui", "auto", "Auto column layout for branch/tag listings", False),
]


def selected_entries(minimal: bool) -> list[tuple[str, str, str, bool]]:
    return ENTRIES[:MINIMAL_COUNT] if minimal else ENTRIES


def git_root() -> Path:
    res = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        capture_output=True,
        text=True,
        check=False,
    )
    if res.returncode != 0 or res.stdout.strip() != "true":
        raise SystemExit("Error: not inside a git work tree.")
    top = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=True,
    )
    return Path(top.stdout.strip())


def resolve_target(root: Path, file_arg: str | None, local_only: bool) -> Path:
    if file_arg:
        p = Path(file_arg)
        return p if p.is_absolute() else (Path.cwd() / p).resolve()
    candidates = LOCAL_CANDIDATES if local_only else CONFIG_CANDIDATES
    for rel in candidates:
        p = root / rel
        if p.is_file():
            return p
    return root / candidates[0]


def has_key(text: str, key: str) -> bool:
    return bool(re.search(rf"(?i)(?<![\w.-]){re.escape(key)}(?![\w.-])", text))


def local_git_config() -> dict[str, str]:
    res = subprocess.run(
        ["git", "config", "--local", "--list"],
        capture_output=True,
        text=True,
        check=False,
    )
    if res.returncode != 0:
        return {}
    cfg: dict[str, str] = {}
    for line in res.stdout.splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            cfg[k.strip().lower()] = v
        elif line.strip():
            cfg[line.strip().lower()] = ""
    return cfg


def extract_hook_scripts(data: dict) -> list[str]:
    hooks = data.get("hooks")
    if hooks is None:
        return []
    if not isinstance(hooks, dict):
        raise SystemExit("Error: [hooks] exists and is not a TOML table.")
    enter = hooks.get("enter")
    if enter is None:
        return []
    if isinstance(enter, str):
        return [enter]
    if isinstance(enter, list):
        scripts: list[str] = []
        for item in enter:
            if isinstance(item, str):
                scripts.append(item)
            elif isinstance(item, dict) and isinstance(item.get("run"), str):
                scripts.append(item["run"])
        return scripts
    if isinstance(enter, dict):
        if "task" in enter and "run" not in enter:
            raise SystemExit("Error: hooks.enter references an external task; inspect that task directly.")
        if isinstance(enter.get("run"), str):
            return [enter["run"]]
        raise SystemExit("Error: unsupported hooks.enter table format.")
    raise SystemExit(f"Error: unsupported hooks.enter type: {type(enter).__name__}")

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

DEFAULT_FILENAME = ".git-blame-ignore-revs"
HEADER = "# Bulk formatting commits excluded from git blame.\n# Add full commit SHAs below, one per line.\n"
FULL_SHA = re.compile(r"\A[0-9a-f]{40}\Z")
FORMAT_KEYWORDS = re.compile(
    r"format|prettier|eslint|biome|oxfmt|dprint|deno fmt"
    r"|black|ruff|isort|autopep8|yapf"
    r"|gofmt|gofumpt|goimports"
    r"|rustfmt|cargo fmt|stylua|shfmt|clang-format|ktlint|scalafmt"
    r"|reformat|whitespace|indent|line.?ending",
    re.IGNORECASE,
)
FORMATTER_SIGNALS = (
    ".prettierrc",
    ".prettierrc.json",
    ".prettierrc.yaml",
    ".prettierrc.yml",
    "prettier.config.js",
    "biome.json",
    "biome.jsonc",
    "eslint.config.js",
    "eslint.config.mjs",
    ".eslintrc.json",
    "deno.json",
    "go.mod",
    ".editorconfig",
    "pyproject.toml",
    "setup.cfg",
    ".isort.cfg",
    ".black",
    "rustfmt.toml",
    ".rustfmt.toml",
    ".pre-commit-config.yaml",
    ".pre-commit-config.yml",
    "prek.toml",
)


def run_git(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=False)


def git_root() -> Path:
    res = run_git("rev-parse", "--is-inside-work-tree")
    if res.returncode != 0 or res.stdout.strip() != "true":
        raise SystemExit("Error: not inside a git work tree.")
    top = run_git("rev-parse", "--show-toplevel")
    if top.returncode != 0:
        raise SystemExit("Error: cannot determine git top level.")
    return Path(top.stdout.strip())


def scoped_config(scope: str) -> str | None:
    res = run_git("config", f"--{scope}", "--get", "blame.ignoreRevsFile")
    value = res.stdout.strip()
    return value or None


def effective_config() -> tuple[str | None, str | None]:
    """Return (effective value, origin) for blame.ignoreRevsFile."""
    res = run_git("config", "--show-origin", "--get", "blame.ignoreRevsFile")
    line = res.stdout.strip()
    if res.returncode != 0 or not line:
        return None, None
    origin, _, value = line.partition("\t")
    return (value or None), (origin or None)


def config_report() -> dict[str, str | None]:
    effective, origin = effective_config()
    return {
        "effective": effective,
        "origin": origin,
        "local": scoped_config("local"),
        "global": scoped_config("global"),
        "system": scoped_config("system"),
    }


def absolutize(root: Path, value: str) -> Path:
    """Resolve a git config path: expand ~, join relative paths to the repo root."""
    p = Path(os.path.expanduser(value))
    if p.is_absolute():
        return p
    return root / p


def resolve_revs_file(root: Path, override: str | None = None) -> Path:
    if override:
        p = Path(os.path.expanduser(override))
        return p if p.is_absolute() else (Path.cwd() / p).resolve()
    effective, _ = effective_config()
    name = effective or DEFAULT_FILENAME
    return absolutize(root, name)


def display_path(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def parse_revs_file(path: Path) -> tuple[list[str], list[str]]:
    """Return (active full-SHA lines in order, malformed lines)."""
    active: list[str] = []
    malformed: list[str] = []
    if not path.is_file():
        return active, malformed
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        token = stripped.split()[0]
        if FULL_SHA.match(token):
            active.append(token)
        else:
            malformed.append(line)
    return active, malformed


def commit_exists(sha: str) -> bool:
    res = run_git("cat-file", "-e", f"{sha}^{{commit}}")
    return res.returncode == 0


def numstat(sha: str, ignore_ws: bool = False) -> list[tuple[str, str, str]] | None:
    args = ["diff-tree", "--no-commit-id", "--numstat", "--root"]
    if ignore_ws:
        args.append("-w")
    args.append(sha)
    res = run_git(*args)
    if res.returncode != 0:
        return None
    rows: list[tuple[str, str, str]] = []
    for line in res.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) == 3:
            rows.append((parts[0], parts[1], parts[2]))
    return rows


def list_history() -> list[dict[str, str]]:
    """All non-merge commits reachable from HEAD, newest first, one git call."""
    res = run_git("log", "--no-merges", "--format=%H%x01%ad%x01%s", "--date=short", "HEAD")
    if res.returncode != 0:
        raise SystemExit("Error: cannot list git history (is HEAD unborn?).")
    commits: list[dict[str, str]] = []
    for line in res.stdout.splitlines():
        parts = line.split("\x01")
        if len(parts) == 3:
            commits.append({"sha": parts[0], "date": parts[1], "subject": parts[2]})
    return commits


def classify_commit(sha: str, subject: str) -> tuple[str, str, dict[str, int]]:
    stats = numstat(sha)
    if stats is None:
        return ("skip", "cannot read diff", {"files": 0, "added": 0, "deleted": 0})
    if not stats:
        return ("skip", "no content changes", {"files": 0, "added": 0, "deleted": 0})
    files = len(stats)
    added = sum(int(a) for a, _, _ in stats if a != "-")
    deleted = sum(int(d) for _, d, _ in stats if d != "-")
    summary = {"files": files, "added": added, "deleted": deleted}
    ws_stats = numstat(sha, ignore_ws=True)
    if ws_stats is not None and not ws_stats:
        return ("high", "whitespace-only changes (git diff -w is empty)", summary)
    if FORMAT_KEYWORDS.search(subject):
        return ("medium", f"message suggests formatting: {subject}", summary)
    return ("low", "code changes with no formatting signal", summary)


def scan_history(existing: set[str]) -> dict[str, object]:
    commits = list_history()
    to_add: list[dict[str, object]] = []
    propose: list[dict[str, object]] = []
    low_count = 0
    skipped = 0
    for commit in commits:
        sha = commit["sha"]
        if sha in existing:
            skipped += 1
            continue
        level, evidence, summary = classify_commit(sha, commit["subject"])
        if level == "skip":
            skipped += 1
            continue
        entry: dict[str, object] = {
            "sha": sha,
            "short": sha[:12],
            "date": commit["date"],
            "subject": commit["subject"],
            "evidence": evidence,
            **summary,
        }
        if level == "high":
            to_add.append(entry)
        elif level == "medium":
            propose.append(entry)
        else:
            low_count += 1
    return {
        "scanned": len(commits),
        "already_ignored_or_skipped": skipped,
        "to_add": to_add,
        "propose": propose,
        "low_count": low_count,
    }

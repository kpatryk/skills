[![Scan Skills](https://github.com/kpatryk/skills/actions/workflows/scan-skills.yml/badge.svg)](https://github.com/kpatryk/skills/actions/workflows/scan-skills.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue?logo=python&logoColor=white&style=flat-square)](https://www.python.org/)
[![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-yellow.svg?style=flat-square)](https://conventionalcommits.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white&style=flat-square)](https://github.com/pre-commit/pre-commit)
[![mise](https://img.shields.io/badge/mise-enabled-FF6F00?logo=gnubash&logoColor=white&style=flat-square)](https://mise.jdx.dev)
[![uv](https://img.shields.io/badge/uv-enabled-DE5FE9?logo=python&logoColor=white&style=flat-square)](https://docs.astral.sh/uv)

- [Install as Copilot CLI Plugin](#install-as-copilot-cli-plugin)
- [Skills](#skills)
  - [What is a skill?](#what-is-a-skill)
  - [Skills Included](#skills-included)
    - [Python Development](#python-development)
    - [JavaScript/TypeScript Development](#javascripttypescript-development)
    - [Code Quality \& Security](#code-quality--security)
    - [Developer Workflow \& Tooling](#developer-workflow--tooling)

# Install as Copilot CLI Plugin

This repository is packaged as a GitHub Copilot CLI plugin (`kpatryk-skills`). Install all skills at once:

```bash
# Install directly from GitHub
copilot plugin install gh:kpatryk/skills

# Or install from a local clone
copilot plugin install ./skills

# Verify the plugin is loaded
copilot plugin list
```

Once installed, all skills in this repository become available in your Copilot CLI session. You can verify with:

```bash
# In an interactive Copilot session
/skills list
```

To update to the latest version, re-run the install command. To remove the plugin:

```bash
copilot plugin uninstall kpatryk-skills
```

# Skills
This repository hosts AI skills for developer tools and agentic systems. The list of skills is curated to cover a broad range of essential tools across the Python ecosystem, JavaScript/TypeScript, security & DevOps, and terminal productivity. Each skill is defined in a `SKILL.md` file with YAML frontmatter specifying trigger patterns and comprehensive documentation covering CLI commands, key patterns, configuration, gotchas, and best practices.

## What is a skill?
Each skill is a specialized knowledge domain for AI assistants. The `SKILL.md` frontmatter defines trigger patterns (when the skill should be invoked), and the body provides comprehensive, canonical documentation covering:
- CLI commands and quick references
- Key patterns and idioms
- Configuration and integration points
- Common gotchas and best practices

## Skills Included

Skills are organized into categories based on their primary use case:

### Python Development

| Skill | Purpose |
|-------|---------|
| **bandit** | Python AST-based security linting and vulnerability detection |
| **cosmic-ray** | Session-based distributed mutation testing with pluggable executors and reporters |
| **mutmut** | Incremental mutation testing with TUI-driven workflow and type-checker filtering |
| **pyrefly** | Type checking by Meta (Rust-based, baseline file support) |
| **pytest** | Python testing framework with fixtures, parametrize, and mocking |
| **ruff** | Fast Python linting and formatting (Rust-based) |
| **ty** | Ultra-fast type checking by Astral (Rust, 10-100x faster than mypy) |
| **uv** | Ultra-fast Python package and project manager (Rust-based) |

### JavaScript/TypeScript Development

| Skill | Purpose |
|-------|---------|
| **bun** | All-in-one JS/TS runtime, bundler, and test runner |

### Code Quality & Security

| Skill | Purpose |
|-------|---------|
| **semgrep** | Semantic pattern matching across 30+ programming languages for static analysis |
| **skill-scanner** | Security scanner for Agent Skills detecting prompt injection, exfiltration, and command abuse (Cisco AI Defense) |
| **trufflehog** | Secrets detection in repos, filesystems, S3, and Docker containers |

### Developer Workflow & Tooling

| Skill | Purpose |
|-------|---------|
| **copier** | Project scaffolding and initialization via Jinja2 templating |
| **git-cliff** | Changelog generation from conventional commits |
| **gum** | Glamorous CLI tool for interactive shell scripts and user prompts |
| **ripgrep** | Fast grep replacement respecting .gitignore patterns |
| **vhs** | Terminal recorder for reproducible GIF/MP4/WebM demos |
| **worktrunk** | Developer workflow automation for parallel work sessions |

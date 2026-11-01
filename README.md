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
- [Repository Structure](#repository-structure)

# Install as Copilot CLI Plugin

This repository is packaged as a GitHub Copilot CLI plugin (`kpatryk-skills`). Install all skills at once:

```bash
# Install directly from GitHub
copilot plugin install kpatryk/skills

# Or add as a marketplace and install from there
copilot plugin marketplace add kpatryk/skills
copilot plugin marketplace browse kpatryk-skills

# Or install from a local clone
copilot plugin install ./path/to/skills

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
This repository hosts AI skills for developer tools and agentic systems. Each skill is defined in a `SKILL.md` file with YAML frontmatter specifying trigger patterns and comprehensive documentation covering CLI commands, key patterns, configuration, gotchas, and best practices.

## What is a skill?
Each skill is a specialized knowledge domain for AI assistants. The `SKILL.md` frontmatter defines trigger patterns (when the skill should be invoked), and the body provides comprehensive, canonical documentation covering:
- CLI commands and quick references
- Key patterns and idioms
- Configuration and integration points
- Common gotchas and best practices

## Skills Included

| Skill | Purpose |
|-------|---------|
| **macos-diagnostics** | Evidence-first troubleshooting for macOS system issues (battery, heat/fans, panics, Wi-Fi/Bluetooth, sleep/wake, slowness, disk) and dev tools on Mac (`brew`, `mise`, `bun`, `npm`/`pnpm`/`yarn`, `uv`, `pip`/`pipx`/`poetry`) |
| **prek-migrate** | Migrate a repo from pre-commit to prek (YAML→`prek.toml` conversion, `repo: builtin` switch, `cooldown-days` hardening, mise/CI/docs cleanup) |

# Repository Structure

```text
.
├── skills/
│   ├── macos-diagnostics/
│   │   ├── SKILL.md
│   │   ├── evals/evals.json
│   │   ├── references/templates.md
│   │   └── scripts/diag.py
│   └── prek-migrate/
│       ├── SKILL.md
│       └── evals/evals.json
├── hooks/
│   └── validate-plugin.sh   # validates plugin.json against the agent-plugins schema
├── .github/
│   ├── workflows/scan-skills.yml       # runs skill-scanner on skills/ changes
│   ├── skill-scanner-policy.yaml       # policy for the scanner
│   └── plugin/marketplace.json         # marketplace manifest (mirrors plugin.json)
├── plugin.json              # Copilot CLI plugin manifest (name: kpatryk-skills)
├── mise.toml                # mise tools (prek, python, uv) and tasks (install, hooks, clean)
├── .pre-commit-config.yaml  # local hooks: plugin validation, conventional commits, hygiene
├── CODE_OF_CONDUCT.md
└── LICENSE
```

[![Scan Skills](https://github.com/kpatryk/skills/actions/workflows/scan-skills.yml/badge.svg)](https://github.com/kpatryk/skills/actions/workflows/scan-skills.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue?logo=python&logoColor=white&style=flat-square)](https://www.python.org/)
[![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-yellow.svg?style=flat-square)](https://conventionalcommits.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)
[![prek](https://raw.githubusercontent.com/j178/prek/main/docs/assets/badge.svg)](https://github.com/j178/prek)
[![mise](https://img.shields.io/badge/mise-enabled-FF6F00?logo=gnubash&logoColor=white&style=flat-square)](https://mise.jdx.dev)
[![uv](https://img.shields.io/badge/uv-enabled-DE5FE9?logo=python&logoColor=white&style=flat-square)](https://docs.astral.sh/uv)

- [Install as Claude Code Plugin](#install-as-claude-code-plugin)
- [Install as Copilot CLI Plugin](#install-as-copilot-cli-plugin)
- [Install with the skills CLI](#install-with-the-skills-cli)
- [Skills](#skills)
  - [What is a skill?](#what-is-a-skill)
  - [Skills Included](#skills-included)

# Install as Claude Code Plugin

This repository is also a Claude Code plugin marketplace (`kpatryk-skills`). Install the plugin in one step on Claude Code 2.1.275 or later:

```bash
/plugin install kpatryk-skills --marketplace kpatryk/skills
```

Or add the marketplace first and install from it:

```bash
/plugin marketplace add kpatryk/skills
/plugin install kpatryk-skills@kpatryk-skills
```

# Install as Copilot CLI Plugin

This repository is packaged as a GitHub Copilot CLI plugin (`kpatryk-skills`). Install all skills at once:

```bash
# Install directly from GitHub (root plugin.json)
copilot plugin install kpatryk/skills

# Or add the marketplace and install the plugin from it
copilot plugin marketplace add kpatryk/skills
copilot plugin install kpatryk-skills@kpatryk-skills

# Or install from a local clone
copilot plugin install ./path/to/skills

# Verify the plugin is loaded
copilot plugin list
copilot skill list   # plugin skills show under "Plugin skills:"
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

# Install with the skills CLI

The [`skills`](https://skills.sh) CLI scans `skills/` directly and reads `.claude-plugin/plugin.json` to group the results under **Kpatryk Skills**:

```bash
# List the skills the repo provides
skills add -l kpatryk/skills

# Install every skill globally for every detected agent
skills add -g kpatryk/skills --all

# Or pick the skill and target agent explicitly
skills add -g kpatryk/skills --skill macos-diagnostics -a claude-code -y
```

`-g` writes to each selected agent's user-level directory (`~/.claude/skills`, `~/.copilot/skills`, `~/.agents/skills`, …). Drop `-g` to install into the current project instead.

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

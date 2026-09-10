# Repository Guide

This repository contains AI skills for developer tools and agentic systems.

## Quick Start

```bash
mise install
mise run install
mise hooks
```

Run individual checks with:

```bash
pre-commit run conventional-pre-commit --all-files
pre-commit run shellcheck --all-files
pre-commit run check-yaml --all-files
```

Use `mise clean` to remove build artifacts.

## Structure

- `skills/<tool-name>/SKILL.md` — canonical skill definition
- `.pre-commit-config.yaml` — quality and security checks
- `mise.toml` — task automation

## Skill Conventions

Each `SKILL.md` must:

- Start with YAML frontmatter containing `name`, `description`, and `license: MIT`.
- Use clear `#` headings.
- Put CLI examples in `bash` code blocks.
- Cover the skill's CLI, configuration, common patterns, and gotchas.

Shell scripts need a shebang, commits must follow [Conventional Commits](https://www.conventionalcommits.org/), and binary files are not allowed.

## Adding or Reviewing Skills

Keep skills under `skills/<tool-name>/`. Before committing a new or changed skill,
run `mise hooks`. When reviewing, verify frontmatter, documentation coverage,
and pre-commit repository URLs and revisions.

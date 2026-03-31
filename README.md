[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white&style=flat-square)](https://github.com/pre-commit/pre-commit)
[![mise](https://img.shields.io/badge/mise-enabled-FF6F00?logo=gnubash&logoColor=white&style=flat-square)](https://mise.jdx.dev)
[![uv](https://img.shields.io/badge/uv-enabled-DE5FE9?logo=python&logoColor=white&style=flat-square)](https://docs.astral.sh/uv)

- [Skills](#skills)
  - [What is a skill?](#what-is-a-skill)
  - [Skills Included](#skills-included)
    - [Python Development](#python-development)
    - [JavaScript/TypeScript Development](#javascripttypescript-development)
    - [Code Quality \& Security](#code-quality--security)
    - [Developer Workflow \& Tooling](#developer-workflow--tooling)

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

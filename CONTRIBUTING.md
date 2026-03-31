# Contributing

Thanks for contributing to this skills repository.

## Prerequisites

- Install tooling with `mise` and `uv`.
- Ensure `gh` is authenticated if you run GitHub operations.

## Setup

```bash
mise install
mise run install
```

This installs Python/uv requirements and sets up pre-commit hooks.

## Repository layout

- `skills/<tool-name>/SKILL.md` — one skill per directory
- `.github/workflows/` — CI workflows
- `scripts/` — shared scripts used by CI/local checks

## Authoring a skill

1. Create `skills/<tool-name>/SKILL.md`
2. Add valid YAML frontmatter:
   - `name`
   - `description`
3. Use clear markdown sections and runnable command examples.

## Local validation

Run all checks before pushing:

```bash
mise pre-commit
```

To run the skill scanner locally:

```bash
uv tool install cisco-ai-skill-scanner
POLICY=.github/skill-scanner-policy.yaml ./scripts/scan-skills.sh
```

## Commit and PR guidelines

- Follow Conventional Commits (enforced by pre-commit).
- Keep changes focused and small.
- Add/update docs when behavior or CI policy changes.
- For CI/security changes, include rationale in the PR description.

## Security considerations

- Never commit secrets or credentials.
- Prefer pinned versions for external tooling in CI.
- If a scanner alert is a false positive, document why in policy/docs instead of silently ignoring it.

# TruffleHog: CI/CD & Pre-Commit Integration

Reference: https://github.com/trufflesecurity/trufflehog/blob/main/PreCommit.md  
Docs: https://github.com/trufflesecurity/trufflehog

---

## Pre-Commit Hooks

TruffleHog auto-detects several pre-commit environments via env variables and framework signals.

### Method 1: Git's core.hooksPath (global, all repos)

```bash
# 1. Create a global hooks directory
mkdir -p ~/.git-hooks

# 2. Create the hook
cat > ~/.git-hooks/pre-commit << 'EOF'
#!/bin/sh
export TRUFFLEHOG_PRE_COMMIT=1
trufflehog git file://.
EOF
chmod +x ~/.git-hooks/pre-commit

# 3. Apply globally
git config --global core.hooksPath ~/.git-hooks
```

The `TRUFFLEHOG_PRE_COMMIT=1` env variable tells TruffleHog to apply optimal
pre-commit settings automatically (scans only staged/uncommitted changes,
returns exit 183 if secrets found).

### Method 2: pre-commit framework (.pre-commit-config.yaml)

Add to your repo's `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: trufflehog
        name: TruffleHog
        description: Detect secrets in your data.
        entry: bash -c 'trufflehog git file://.'
        language: system
        stages: ["pre-commit", "pre-push"]
```

Then install:

```bash
pip install pre-commit   # or: brew install pre-commit
pre-commit install
```

If auto-detection doesn't work, use explicit flags:

```yaml
entry: bash -c 'trufflehog git file://. --since-commit HEAD --results=verified,unknown --fail --trust-local-git-config'
```

### Method 3: Husky (Node.js projects)

```bash
npm install husky --save-dev
npx husky init

# Write the hook
echo "trufflehog git file://." > .husky/pre-commit
```

Or with Docker:

```bash
echo 'docker run --rm -v "$(pwd):/workdir" -i trufflesecurity/trufflehog:latest git file:///workdir' > .husky/pre-commit
```

### Pre-commit tips

- Run `git add` then `git commit` separately — `git commit -am` can miss unstaged changes
- Bypass hooks when needed: `git commit --no-verify -m "message"`
- Audit mode (no enforcement): remove `--fail` and pipe stderr to `/dev/null`

---

## GitHub Actions

### Standard workflow (recommended)

```yaml
name: Secret Scanning

on:
  push:
    branches: [main]
  pull_request:

jobs:
  trufflehog:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0   # IMPORTANT: full history for commit scanning

      - name: TruffleHog Secret Scan
        uses: trufflesecurity/trufflehog@main
        with:
          extra_args: --results=verified,unknown
```

The action automatically scans only the commits in the PR/push delta — no
`--since-commit` flags needed.

### Shallow clone optimization (faster, when no other CI tooling needs full history)

```yaml
      - shell: bash
        run: |
          if [ "${{ github.event_name }}" == "push" ]; then
            echo "depth=$(($(jq length <<< '${{ toJson(github.event.commits) }}') + 2))" >> $GITHUB_ENV
            echo "branch=${{ github.ref_name }}" >> $GITHUB_ENV
          fi
          if [ "${{ github.event_name }}" == "pull_request" ]; then
            echo "depth=$((${{ github.event.pull_request.commits }}+2))" >> $GITHUB_ENV
            echo "branch=${{ github.event.pull_request.head.ref }}" >> $GITHUB_ENV
          fi

      - uses: actions/checkout@v4
        with:
          ref: ${{ env.branch }}
          fetch-depth: ${{ env.depth }}

      - uses: trufflesecurity/trufflehog@main
        with:
          extra_args: --results=verified,unknown
```

### Scan entire branch (not just delta)

```yaml
      - name: TruffleHog Full Branch Scan
        uses: trufflesecurity/trufflehog@main
        with:
          base: ""
          head: ${{ github.ref_name }}
          extra_args: --results=verified,unknown
```

### Manual `git` subcommand in CI (more control)

```yaml
      - name: Install TruffleHog
        run: |
          curl -sSfL https://raw.githubusercontent.com/trufflesecurity/trufflehog/main/scripts/install.sh \
            | sh -s -- -b /usr/local/bin

      - name: Scan PR commits
        run: |
          trufflehog git file://. \
            --since-commit ${{ github.event.pull_request.base.sha }} \
            --branch HEAD \
            --results=verified,unknown \
            --fail \
            --json | jq .
```

---

## GitLab CI

```yaml
stages:
  - security

secret-scanning:
  stage: security
  image: alpine:latest
  variables:
    SCAN_PATH: "."
  before_script:
    - apk add --no-cache git curl jq
    - curl -sSfL https://raw.githubusercontent.com/trufflesecurity/trufflehog/main/scripts/install.sh \
        | sh -s -- -b /usr/local/bin
  script:
    - trufflehog filesystem "$SCAN_PATH" --results=verified,unknown --fail --json | jq
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
```

For git history scanning in GitLab:

```yaml
  script:
    - git fetch origin $CI_MERGE_REQUEST_TARGET_BRANCH_NAME
    - trufflehog git file://. \
        --since-commit origin/$CI_MERGE_REQUEST_TARGET_BRANCH_NAME \
        --branch $CI_COMMIT_BRANCH \
        --results=verified,unknown \
        --fail \
        --trust-local-git-config
```

---

## Docker-based scanning in CI

```bash
# In any CI environment with Docker
docker run --rm \
  -v "$PWD:/pwd" \
  trufflesecurity/trufflehog:latest \
  git file:///pwd \
  --since-commit HEAD~10 \
  --results=verified,unknown \
  --fail
```

---

## Output & Alerting Patterns

### JSON output for alerting/SIEM

```bash
trufflehog git https://github.com/org/repo --json --results=verified \
  | jq 'select(.Verified == true) | {detector: .DetectorName, file: .SourceMetadata.Data.Git.file, commit: .SourceMetadata.Data.Git.commit}'
```

### Count findings by detector type

```bash
trufflehog git file://. --json --no-update 2>/dev/null \
  | jq -r '.DetectorName' | sort | uniq -c | sort -rn
```

### GitHub Actions annotation format

```bash
trufflehog git file://. --github-actions --results=verified,unknown
```

This outputs inline PR annotations in GitHub's expected format.

---

## Key Flags Reference for CI

```
--fail                  Exit 183 when results found (use in CI to break builds)
--no-update             Skip version check (speeds up CI runs)
--json                  Machine-readable output
--github-actions        GitHub PR annotation format
--since-commit <ref>    Only scan commits after this ref
--branch <name>         Scan this branch (defaults to HEAD)
--max-depth <n>         Cap commit history depth
--trust-local-git-config  Required for local file:// scans in some CI setups
--results=verified,unknown  Best CI default (live secrets + verification errors)
--concurrency <n>       Tune worker count for CI runner capacity
```

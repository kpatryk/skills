---
name: trufflehog
license: MIT
description: >
  Comprehensive guide for using TruffleHog (open-source) to detect, classify,
  and verify leaked secrets and credentials. Use this skill whenever the user
  wants to scan for secrets, credentials, API keys, tokens, or passwords in
  git repos, GitHub/GitLab orgs, Docker images, S3/GCS buckets, filesystems,
  CI systems, or any other data source. Also invoke this skill when the user
  asks about setting up pre-commit hooks for secret detection, integrating
  secret scanning into CI/CD pipelines (GitHub Actions, GitLab CI, etc.),
  reducing false positives from secret scanners, writing custom regex
  detectors, understanding TruffleHog's verification model, or auditing
  repositories for credential leaks. Trigger on any mention of: trufflehog,
  secret scanning, credential detection, leaked keys, API key detection,
  pre-commit secret hooks, or scanning git history for secrets.
---

# TruffleHog (Open-Source)

TruffleHog is the leading open-source tool for **discovering**, **classifying**,
**verifying**, and **analyzing** leaked credentials. It scans across 800+ secret
types, actively tests findings against live APIs to eliminate false positives, and
integrates cleanly into pre-commit hooks and CI/CD pipelines.

**Docs:** https://github.com/trufflesecurity/trufflehog  
**Reference:** See `references/subcommands.md` for detailed per-source options  
**CI/CD patterns:** See `references/cicd.md` for GitHub Actions, GitLab, pre-commit

---

## Installation

```bash
# macOS
brew install trufflehog

# Linux / macOS (install script)
curl -sSfL https://raw.githubusercontent.com/trufflesecurity/trufflehog/main/scripts/install.sh \
  | sh -s -- -b /usr/local/bin

# Docker
docker run --rm -it trufflesecurity/trufflehog:latest <subcommand> [flags]

# Verify install
trufflehog --version
```

---

## Core Concepts

### Result Types
TruffleHog produces four result categories, controlled via `--results=`:

| Type | Meaning |
|---|---|
| `verified` | Credential confirmed **live** by API call — act immediately |
| `unverified` | Pattern matched but could not confirm validity (may be real) |
| `unknown` | Verification attempted but failed (network/API error) |
| `filtered_unverified` | Unverified results that would be filtered out |

Default: `--results=verified,unverified,unknown`  
**CI best practice:** `--results=verified,unknown` (catches live secrets + network failures)  
**High signal only:** `--results=verified`

### Exit Codes
- `0` — No errors, no results
- `1` — Error encountered
- `183` — Results found (only returned when `--fail` is used)

Use `--fail` in CI to break builds when secrets are found.

---

## Essential Global Flags

These flags work with **every** subcommand:

```
--results=<types>           Which result types to output (see above)
--json / -j                 JSON output (one object per line, great for jq)
--no-verification           Skip API verification (faster, more results)
--fail                      Exit 183 if any results found (use in CI)
--filter-unverified         Deduplicate: output only first unverified per chunk/detector
--filter-entropy=3.0        Filter unverified by Shannon entropy (start at 3.0)
--include-detectors=<list>  Only run these detectors (comma-sep names or IDs)
--exclude-detectors=<list>  Skip these detectors (IDs take precedence over include)
--concurrency=<n>           Worker count (default 12)
--config=<path>             Path to YAML config (custom detectors, multi-scan)
--since-commit=<ref>        Scan only commits after this ref
--branch=<name>             Scan specific branch
--max-depth=<n>             Max commit depth to scan
--archive-max-size=<bytes>  Max archive size (e.g., 4MB)
--archive-max-depth=<n>     Max archive nesting depth
--log-level=<0-5>           Verbosity (0=info, 5=trace; -1 to disable)
--no-update                 Skip update check (useful in CI)
--github-actions            Output in GitHub Actions annotation format
```

---

## Subcommands Quick Reference

### Git repository (local or remote)

```bash
# Remote repo
trufflehog git https://github.com/org/repo

# Local repo (clones to temp dir first for safety)
trufflehog git file:///path/to/repo

# Only verified secrets, last 100 commits on main
trufflehog git https://github.com/org/repo \
  --branch main --max-depth 100 --results=verified

# CI: scan only the new commits in a PR branch
trufflehog git file://. \
  --since-commit main --branch feature-1 \
  --results=verified,unknown --fail

# Trust local git config (only for repos you own/trust)
trufflehog git file://. --trust-local-git-config
```

### GitHub (orgs, repos, PRs, issues)

```bash
# Entire GitHub org (requires token to avoid rate limits)
trufflehog github --org=myorg --token=$GITHUB_TOKEN --results=verified

# Single repo including PR/issue comments
trufflehog github --repo=https://github.com/org/repo \
  --issue-comments --pr-comments

# All repos for a user
trufflehog github --token=$GITHUB_TOKEN --repo=https://github.com/user/repo
```

### GitLab

```bash
trufflehog gitlab --token=$GITLAB_TOKEN --endpoint=https://gitlab.mycompany.com
```

### Filesystem (files and directories)

```bash
# Scan specific files or directories
trufflehog filesystem /path/to/dir /path/to/file.env

# Scan current directory
trufflehog filesystem .
```

### S3

```bash
# Using local credentials / instance role
trufflehog s3 --bucket=my-bucket --results=verified,unknown

# With IAM role assumption
trufflehog s3 --bucket=my-bucket --role-arn=arn:aws:iam::123:role/scanner

# Multiple roles (scans all accessible buckets for each role)
trufflehog s3 --role-arn=<arn1> --role-arn=<arn2>
```

### Docker images

```bash
# Remote registry
trufflehog docker --image myrepo/myimage:tag --results=verified

# Local daemon
trufflehog docker --image docker://myimage:tag

# From tarball
trufflehog docker --image file://image.tar
```

### Google Cloud Storage

```bash
trufflehog gcs --project-id=my-project --cloud-environment --results=verified
```

### Other sources

```bash
# Stdin
aws s3 cp s3://bucket/data.gz - | gunzip -c | trufflehog stdin

# Postman
trufflehog postman --token=$POSTMAN_API_TOKEN --workspace-id=<id>

# Jenkins
trufflehog jenkins --url https://jenkins.example.com --username admin --password pass

# Elasticsearch (username/password)
trufflehog elasticsearch --nodes 192.168.1.1 --username user --password pass

# CircleCI
trufflehog circleci --token=$CIRCLECI_TOKEN

# HuggingFace org
trufflehog huggingface --org myorg

# Scan deleted/hidden GitHub commits (experimental)
trufflehog github-experimental --repo https://github.com/org/repo.git --object-discovery
```

---

## Ignoring False Positives

**Inline suppression** (preferred) — add a comment on the same line as the secret:

```python
API_KEY = "example_key_for_testing"  # trufflehog:ignore
```

```yaml
password: "test123"  # trufflehog:ignore
```

**Output filtering** — use `--results=verified` to show only confirmed live secrets.

**Entropy filtering** — reduce noisy unverified hits:

```bash
trufflehog git file://. --filter-unverified --filter-entropy=3.0
```

---

## Custom Regex Detectors

Define custom detectors in a YAML config and pass with `--config`. Each detector needs at least one keyword (literal string anchor) and one regex.

```yaml
# custom-detectors.yaml
detectors:
  - name: MyInternalToken
    keywords:
      - "myco_token"
    regex:
      myco_token: 'myco_token_[a-zA-Z0-9]{32}'
    verify:
      - endpoint: https://auth.myco.internal/verify
        unsafe: true   # allows HTTP
        headers:
          - "Authorization: Bearer {myco_token}"
```

```bash
trufflehog git file://. --config=custom-detectors.yaml
```

Verification: if the webhook returns HTTP 200, the secret is marked `verified`.

See `references/subcommands.md` for filtering options (entropy, regex filters, word lists).

---

## Analyzing a Found Credential

```bash
# After finding a secret, analyze its permissions
trufflehog analyze
```

For supported credential types (AWS, GCP, etc.), this reports the identity,
accessible resources, and IAM permissions — critical for understanding blast radius.

---

## Multi-Source Scanning

Scan multiple sources in one run using a YAML config with `multi-scan`:

```yaml
# scan-config.yaml
sources:
  - connection:
      '@type': type.googleapis.com/sources.GitHub
      repositories:
        - https://github.com/org/repo1.git
        - https://github.com/org/repo2.git
    name: github-scan
    type: SOURCE_TYPE_GITHUB
    verify: true
```

```bash
trufflehog multi-scan --config=scan-config.yaml
```

---

## Best Practices

1. **Always use `--results=verified,unknown` in CI** — `unknown` catches network failures that might mask live secrets.

2. **Use `--fail` in CI** — ensures the pipeline stops on findings; exit code 183 is non-blocking-friendly (not 1, so you can test for it specifically).

3. **Prefer `--json` for automation** — pipe to `jq` for filtering, deduplication, alerting.

4. **Rate limits on GitHub scans** — always pass `--token=$GITHUB_TOKEN` to avoid hitting unauthenticated rate limits.

5. **Local git repos** — TruffleHog clones them to a temp dir by default (protects against malicious configs). Use `--trust-local-git-config` only for repos you fully control.

6. **Don't over-rely on `--no-verification`** — you'll get many more results but lose the verified/unverified distinction that makes findings actionable.

7. **Scan history, not just HEAD** — most leaked secrets live in git history, not the current codebase. TruffleHog scans all commits by default.

8. **Pre-commit hooks** — set up early; they catch leaks before they ever hit the remote.

9. **`fetch-depth: 0`** in GitHub Actions — shallow clones miss commit history; use full depth or calculate the right fetch depth.

For pre-commit setup and CI/CD patterns, see **`references/cicd.md`**.

---

## Common Pitfalls

- **Shallow clones in CI** miss historical commits — always use `fetch-depth: 0` or calculate depth explicitly.
- **`git commit -am`** can bypass pre-commit hooks for unstaged changes — use separate `git add` + `git commit`.
- **Skipping `--token`** on GitHub scans hits rate limits quickly on large orgs.
- **`--since-commit` without `--branch`** may not behave as expected in detached HEAD states.
- **Binary files** — TruffleHog scans them by default; use `--force-skip-binaries` to skip if scan is slow.
- **Archives** — deeply nested archives slow scans; tune with `--archive-max-depth` and `--archive-max-size`.

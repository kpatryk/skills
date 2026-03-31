# TruffleHog Subcommand Reference

Detailed options for each TruffleHog source subcommand.  
Docs: https://github.com/trufflesecurity/trufflehog

---

## git

Scans git commit history (local or remote).

```bash
trufflehog git [flags] <uri>
```

**URI formats:**
- `https://github.com/org/repo` — HTTPS remote
- `git@github.com:org/repo.git` — SSH remote
- `file:///absolute/path/to/repo` — local repo
- `file://.` — current directory (common in CI)
- `ssh://github.com/org/repo` — SSH alt format

**Key flags:**

```
--branch=<name>           Branch to scan (default: all branches)
--since-commit=<ref>      Start scanning from this commit (exclusive)
--max-depth=<n>           Max number of commits to scan
--bare                    Scan a bare repository
--include-paths=<file>    File containing path patterns to include
--exclude-paths=<file>    File containing path patterns to exclude
--issue-comments          (N/A for git subcommand)
--trust-local-git-config  Skip cloning; scan directly (trusted repos only)
--clone-path=<path>       Where to clone local repos (default: temp dir)
```

**Note on local scanning:** By default, `file://` repos are cloned to a temp
directory before scanning (prevents CVE-2025-41390-style attacks from malicious
git configs). Use `--trust-local-git-config` to skip this for repos you own.

---

## github

Scans GitHub repositories (one repo, all repos in an org, or a user's repos).

```bash
trufflehog github [flags]
```

**Key flags:**

```
--repo=<url>              Specific repo URL (can pass multiple times)
--org=<name>              Scan all repos in this GitHub org
--user=<name>             Scan all repos for this user
--token=<token>           GitHub PAT (highly recommended to avoid rate limits)
--endpoint=<url>          GitHub Enterprise URL (default: https://github.com)
--include-forks           Include forked repos
--issue-comments          Scan issue bodies and comments
--pr-comments             Scan PR bodies and comments
--include-members         Also scan personal repos of org members
--only-members            Only scan personal repos of org members
--member-dedup-count=<n>  Number of repos to use for member deduplication (default 10)
```

**Token scopes needed:**
- Public repos: no token needed (but rate-limited)
- Private repos: `repo` scope
- Org scanning: `read:org` scope

**Example — scan org for verified secrets, output JSON:**

```bash
trufflehog github \
  --org=mycompany \
  --token=$GITHUB_TOKEN \
  --results=verified \
  --json \
  --include-forks \
  --issue-comments
```

---

## gitlab

Scans GitLab repos (instance or group).

```bash
trufflehog gitlab --token=<token> [flags]
```

**Key flags:**

```
--token=<token>           GitLab personal/group access token (required)
--endpoint=<url>          GitLab instance URL (default: https://gitlab.com)
--repo=<url>              Specific repo to scan (repeatable)
--group=<name>            Scan all repos in this group (repeatable)
--include-members         Include member personal repos
```

---

## filesystem

Scans files and directories (not git history).

```bash
trufflehog filesystem [flags] [path...]
```

**Key flags:**

```
--include-paths=<file>    File of include patterns (one per line)
--exclude-paths=<file>    File of exclude patterns (one per line)
```

**Examples:**

```bash
# Scan multiple paths
trufflehog filesystem /etc /home/user/.ssh ./config

# Scan with path exclusions
echo "node_modules" > .trufflehog_exclude
trufflehog filesystem . --exclude-paths=.trufflehog_exclude
```

---

## s3

Scans Amazon S3 buckets. Uses standard AWS credential chain (env vars, `~/.aws`, instance role).

```bash
trufflehog s3 [flags]
```

**Key flags:**

```
--bucket=<name>           Bucket to scan (repeatable for multiple)
--role-arn=<arn>          IAM role to assume for scanning (repeatable)
--prefix=<prefix>         Limit scan to objects with this prefix (repeatable)
--max-object-size=<bytes> Skip objects larger than this
```

**Examples:**

```bash
# Scan with current credentials
trufflehog s3 --bucket=prod-backups --results=verified,unknown

# Cross-account: assume roles in target accounts
trufflehog s3 \
  --role-arn=arn:aws:iam::111111111:role/TruffleHogScanner \
  --role-arn=arn:aws:iam::222222222:role/TruffleHogScanner
```

**IAM policy for the scanner role:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {"Effect": "Allow", "Action": ["s3:GetObject", "s3:ListBucket"], "Resource": "*"},
    {"Effect": "Allow", "Action": "sts:AssumeRole", "Resource": "*"}
  ]
}
```

---

## gcs (Google Cloud Storage)

```bash
trufflehog gcs [flags]
```

**Key flags:**

```
--project-id=<id>         GCP project ID (required)
--cloud-environment       Use application default credentials (ADC)
--service-account=<key>   Path to service account JSON
--bucket=<name>           Scan only this bucket (repeatable)
--include-buckets=<file>  File of bucket names to include
--exclude-buckets=<file>  File of bucket names to exclude
--max-object-size=<bytes> Skip objects larger than this
```

---

## docker

Scans Docker images (layers, config, env vars).

```bash
trufflehog docker [flags]
```

**Key flags:**

```
--image=<spec>            Image to scan (repeatable). Specs:
                            myimage:tag          — local daemon
                            docker://myimage:tag — explicit local daemon
                            file://image.tar     — tarball
                            (no prefix)          — remote registry
```

**Example — scan multiple images:**

```bash
trufflehog docker \
  --image myapp:latest \
  --image myworker:v2 \
  --results=verified
```

---

## elasticsearch

```bash
trufflehog elasticsearch [flags]
```

**Key flags:**

```
--nodes=<host>            Elasticsearch node(s) (repeatable)
--username=<user>         Username
--password=<pass>         Password
--service-token=<token>   Service token (alternative to user/pass)
--cloud-id=<id>           Elastic Cloud cluster ID
--api-key=<key>           Elastic Cloud API key
--index=<name>            Scan only this index (repeatable)
```

---

## postman

```bash
trufflehog postman [flags]
```

**Key flags:**

```
--token=<token>           Postman API token (required)
--workspace-id=<id>       Workspace to scan (repeatable)
--collection-id=<id>      Collection to scan (repeatable)
--environment=<id>        Environment to scan (repeatable)
--include-collections     Include collection items
--include-environments    Include environment variables
```

---

## jenkins

```bash
trufflehog jenkins [flags]
```

**Key flags:**

```
--url=<url>               Jenkins instance URL (required)
--username=<user>         Jenkins username
--password=<pass>         Jenkins password or API token
--insecure-skip-verify-tls  Skip TLS verification
```

---

## circleci / travisci

```bash
trufflehog circleci --token=$CIRCLECI_TOKEN
trufflehog travisci --token=$TRAVISCI_TOKEN
```

---

## huggingface

```bash
trufflehog huggingface [flags]
```

**Key flags:**

```
--org=<name>              Scan org's models, datasets, and spaces
--user=<name>             Scan user's resources
--model=<id>              Scan a specific model (repeatable)
--dataset=<id>            Scan a specific dataset (repeatable)
--space=<id>              Scan a specific space (repeatable)
--token=<token>           HuggingFace token (for private resources)
--skip-models             Skip models when scanning org/user
--skip-datasets           Skip datasets
--skip-spaces             Skip spaces
--ignore-models=<id>      Exclude specific model (repeatable)
--ignore-datasets=<id>    Exclude specific dataset (repeatable)
--ignore-spaces=<id>      Exclude specific space (repeatable)
--include-discussions     Scan discussion comments
--include-prs             Scan PR comments
```

---

## stdin

Read from standard input (pipe any data into TruffleHog):

```bash
trufflehog stdin [flags]
```

**Examples:**

```bash
# Decompress and scan on the fly
aws s3 cp s3://bucket/logs.gz - | gunzip -c | trufflehog stdin

# Scan any text content
cat /var/log/app.log | trufflehog stdin --results=verified,unknown
```

---

## multi-scan

Scan multiple sources defined in a YAML config file:

```bash
trufflehog multi-scan --config=<path>
```

**Config format:**

```yaml
sources:
  - connection:
      '@type': type.googleapis.com/sources.GitHub
      repositories:
        - https://github.com/org/repo1.git
      token:
        value: "ghp_xxxx"
      unauthenticated: {}
    name: github-production
    type: SOURCE_TYPE_GITHUB
    verify: true
  - connection:
      '@type': type.googleapis.com/sources.S3
      buckets:
        - my-data-bucket
    name: s3-data
    type: SOURCE_TYPE_S3
    verify: true
```

---

## Custom Regex Detector Config

Full YAML config format for custom detectors:

```yaml
detectors:
  - name: InternalAPIKey
    keywords:
      - "internal_api_key"     # literal anchor string
    regex:
      internal_key: 'internal_api_key_[A-Za-z0-9]{40}'
    verify:
      - endpoint: https://api.internal.example.com/verify
        unsafe: false    # true to allow HTTP
        headers:
          - "Authorization: Bearer {internal_key}"
    # Optional filters:
    min_length: 40
    max_length: 60
    filter_entropy: 3.5   # Shannon entropy threshold
    filter_regex:
      - '^internal_api_key_test'   # exclude test keys

  - name: MyJWTToken
    keywords:
      - "eyJ"
    regex:
      jwt: 'eyJ[A-Za-z0-9\-_=]+\.[A-Za-z0-9\-_=]+\.?[A-Za-z0-9\-_.+/=]*'
    # No verify block = unverified only
```

**Notes:**
- `keywords` are literal strings that must appear near the regex match (fast pre-filter)
- Multiple `regex` entries = all must match in the same chunk
- `verify.endpoint` receives a JSON POST with `{match: "...", groups: {...}}`; return 200 = verified
- `filter_regex` patterns matched against the captured group (or full match if no group)

---

## Detector Names / IDs

To list all available detector names (for `--include-detectors` / `--exclude-detectors`):

```bash
trufflehog git --help-long 2>&1 | grep -A2 'include-detectors'
```

Common detectors: `AWS`, `GitHub`, `Stripe`, `Slack`, `GCP`, `Azure`, `Postgres`,
`MySQL`, `Twilio`, `SendGrid`, `Okta`, `Shopify`, `HuggingFace`, `OpenAI`, `Anthropic`,
`PrivateKey`, `JWT`, and 800+ more.

**Include only AWS and GCP:**

```bash
trufflehog git file://. --include-detectors=AWS,GCP
```

**Exclude Stripe and generic tokens:**

```bash
trufflehog git file://. --exclude-detectors=Stripe,GenericAPIKey
```

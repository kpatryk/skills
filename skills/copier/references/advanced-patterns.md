# Copier Advanced Reference

This document provides detailed reference material for advanced Copier patterns, edge cases, and troubleshooting.

## copier.yml Schema Reference

### Top-level Question Definition

```yaml
question_key:           # Variable name available in templates
  type: str             # Question type (see below)
  help: "Help text"     # Displayed to user
  default: value        # Default answer
  placeholder: "hint"   # Input field hint
  secret: false         # Hide input/output if true
  when: "{{ condition }}" # Show only if Jinja2 condition is true
  choices:              # Restrict to these options
    - value1
    - value2
  validator: "{% if condition %}Error message{% endif %}"  # Custom validation
```

### Question Types

| Type | Input Format | Example |
|------|---|---|
| `str` | String | `"my_project"` |
| `int` | Integer | `42` |
| `float` | Decimal | `3.14` |
| `bool` | Yes/No prompt | `true` / `false` |
| `json` | JSON string | `{"key": "value"}` |
| `yaml` | YAML string | `key: value` |
| `path` | File path | `"/home/user/project"` |
| `choice` | Single selection | One of `choices` |
| `multichoice` | Multi-select | List from `choices` |

### Advanced Choices Patterns

**Simple list:**
```yaml
database:
  type: choice
  choices:
    - PostgreSQL
    - MySQL
    - SQLite
```

**Dict format (choice label → value):**
```yaml
license:
  type: choice
  choices:
    "MIT": mit
    "Apache 2.0": apache2
    "GPL 3.0": gpl3
```

**With validators (disable choice conditionally):**
```yaml
cloud_provider:
  type: choice
  choices:
    AWS:
      value: aws
    Azure:
      value: azure
      validator: "{% if region != 'US' %}Azure unavailable outside US{% endif %}"
```

**Dynamic choices (Jinja2 rendering):**
```yaml
language:
  type: choice
  choices:
    - Python
    - JavaScript
    - Go

package_manager:
  type: choice
  choices: |
    {%- if language == "Python" %}
    - pip
    - poetry
    - pipenv
    {%- elif language == "JavaScript" %}
    - npm
    - yarn
    - pnpm
    {%- elif language == "Go" %}
    - go get
    {%- endif %}
```

## Copier Settings (_*) Reference

All copier settings must start with `_`.

### Essential Settings

```yaml
_min_copier_version: "9.0.0"
  # Minimum Copier version required. Format: PEP 440

_subdirectory: "template"
  # Relative path to template content (useful for mono-repos)
  # If set, only files in this directory are rendered

_answers_file: ".copier-answers.yml"
  # Where to store generated answers (relative to dst_path)

_exclude:
  - "*.pyc"
  - "__pycache__"
  - ".git"
  # Patterns to exclude from rendering (glob format)

_skip_if_exists:
  - "config.local.yml"
  - ".env"
  # Files to preserve if they already exist
```

### Post-Generation

```yaml
_tasks:
  - "git init"
  - "git add -A"
  - "git commit -m 'Initial commit'"
  - "pre-commit install"
  # Shell commands executed after project is generated
  # Requires --trust flag to execute

_message_before_copy: |
  ⚠️  This template requires Python 3.10+
  Make sure to have Git installed.

_message_after_copy: |
  ✅ Project created successfully!
  Next steps:
    1. cd {{project_name}}
    2. pip install -e .
    3. make test
```

### Template Rendering

```yaml
_jinja_extensions:
  - jinja2.ext.do
  - jinja2.ext.loopcontrols
  - jinja2.ext.debug

_envops:
  keep_trailing_newline: true
  trim_blocks: true
  lstrip_blocks: true

_templates_suffix: ".jinja"
  # File suffix that triggers Jinja2 rendering (default: .jinja)
```

### Migrations

```yaml
_migrations:
  "0.1.0->0.2.0": |
    # Python code executed during update from 0.1.0 to 0.2.0
    # `answers` dict is available for modification
    answers["module_name"] = answers.get("module_name", "").lower()

  "0.2.0->0.3.0": |
    # Multi-step migrations
    if "old_key" in answers:
      answers["new_key"] = answers.pop("old_key").upper()
    answers["version"] = "3"
```

### Conflict Resolution

```yaml
_conflict: "inline"       # inline (default) or rej
_context_lines: 3         # Lines of context in diffs (for merge conflict display)
```

## Jinja2 Templating Patterns

### In File Content

```jinja
{# Conditional blocks #}
{% if include_license %}
# License
MIT License - {{current_year}}
{% endif %}

{# Loops #}
{% for dep in dependencies %}
{{ dep }}
{% endfor %}

{# Filters #}
{{ project_name | upper }}
{{ author | title }}
{{ config | to_json }}
{{ answers | to_nice_yaml }}

{# Math #}
{% set total = 10 * 5 %}
Total: {{ total }}

{# Nested conditionals #}
{% if use_docker %}
  {% if db_type == "postgres" %}
  services:
    db:
      image: postgres:latest
  {% endif %}
{% endif %}
```

### In File/Directory Names

```
# Directory with templated name
{{project_name}}/

# File with templated name
{{project_name}}/{{module_name}}.py.jinja

# Conditional file names not supported directly, but:
# Use _skip_if_exists and conditions in _tasks instead
config-{{environment}}.yaml.jinja
```

### Special Variables

```jinja
{# Current user's answers (excludes secrets) #}
{{ _copier_answers }}

{# Configuration object #}
{{ _copier_conf.answers_file }}      {# Path to answers file #}
{{ _copier_conf.dst_path }}          {# Destination directory #}
{{ _copier_conf.src_path }}          {# Template source path #}
{{ _copier_conf.data }}              {# Extra data passed via --data #}
{{ _copier_conf.defaults }}          {# true if using --defaults #}

{# Convert to YAML/JSON #}
{{ _copier_answers | to_nice_yaml }}
{{ answers_dict | to_json }}
```

## Common Template Structures

### Minimal Template

```
my_template/
├── .git/                    (required)
├── copier.yml
├── {{project_name}}/
│   └── __init__.py.jinja
└── README.md.jinja
```

### Full-featured Template

```
my_template/
├── .git/
├── .github/
│   └── workflows/           (not templated, but version-controlled)
├── copier.yml
├── template/                (use with _subdirectory: "template")
│   ├── {{project_name}}/
│   │   ├── src/
│   │   │   └── {{module_name}}/
│   │   │       ├── __init__.py.jinja
│   │   │       └── main.py.jinja
│   │   ├── tests/
│   │   ├── pyproject.toml.jinja
│   │   └── README.md.jinja
│   └── .env.example.jinja
├── scripts/                 (not templated)
│   └── setup.sh
└── {{_copier_conf.answers_file}}.jinja
```

### Multi-variant Template

```
my_template/
├── copier.yml
│   # Questions include: project_type (web, cli, lib)
│   # _subdirectory: "templates/{{project_type}}"
├── templates/
│   ├── web/                 (rendered if project_type == "web")
│   │   ├── {{project_name}}/
│   │   │   ├── app.py.jinja
│   │   │   └── requirements.txt.jinja
│   │   └── docker-compose.yml.jinja
│   ├── cli/
│   │   ├── {{project_name}}/
│   │   │   └── cli.py.jinja
│   │   └── setup.py.jinja
│   └── lib/
│       └── {{project_name}}/
│           └── __init__.py.jinja
```

## Update Workflow Details

### Step 1: Verify prerequisites
```bash
cd /path/to/project
git status              # Must be clean
cat .copier-answers.yml # Must exist
```

### Step 2: Run update
```bash
copier update --vcs-ref HEAD  # Update to HEAD, not latest tag

# Or with modified answers:
copier update --defaults --data new_question="new_value"
```

### Step 3: Resolve conflicts
```bash
# Find conflict markers or .rej files
git diff | grep -E "^<<<<<<<|^=======|^>>>>>>>"  # inline conflicts
find . -name "*.rej"                             # .rej files

# Fix conflicts and remove markers
# Remove .rej files after fixing
```

### Step 4: Commit
```bash
git add .
git commit -m "Update from template version X to Y"
```

## Task Security & Best Practices

### Tasks require --trust flag

```bash
# This won't run tasks:
copier copy gh:user/template ./project

# This runs tasks (security prompt):
copier copy --trust gh:user/template ./project
```

### Safe task patterns

```yaml
_tasks:
  # Safe: dependency installation
  - "pip install -e .[dev]"

  # Safe: git initialization
  - "git init && git add . && git commit -m 'init'"

  # Avoid: arbitrary downloads
  - "curl https://untrusted.site/setup.sh | bash"  # ❌ Dangerous

  # Avoid: modifying user files outside project
  - "sudo systemctl restart service"                # ❌ Dangerous
```

## Troubleshooting

### Issue: Template isn't rendering Jinja2

**Solution:** Ensure file ends with `.jinja`:
```bash
# Wrong
config.yaml

# Correct
config.yaml.jinja
```

### Issue: Update applies old answers instead of new

**Possible cause:** `.copier-answers.yml` was edited manually

**Solution:**
```bash
# Don't edit manually, use:
copier recopy  # or copier update with fresh answers
```

### Issue: Directory names not templated

**Limitation:** Jinja2 rendering only applies to file content and top-level template directory names

**Workaround:**
```yaml
# Use _tasks to rename after generation
_tasks:
  - "mv {{project_name}}/old_dir {{project_name}}/new_name"
```

### Issue: Conditional files not supported

**Limitation:** File inclusion can't be purely conditional

**Workaround:**
```yaml
# Option 1: Use _skip_if_exists + placeholder files
_skip_if_exists:
  - "optional_feature.py"

# Option 2: Use _tasks to remove files
_tasks:
  - "{% if not include_feature %}rm {{project_name}}/optional_feature.py{% endif %}"
```

## Jinja2 Built-in Filters (via jinja2-ansible-filters)

```jinja
{{ text | upper }}
{{ text | lower }}
{{ text | title }}
{{ text | replace("old", "new") }}
{{ text | regex_replace("pattern", "replacement") }}
{{ list | join(", ") }}
{{ dict | to_nice_yaml }}
{{ dict | to_json }}
{{ number | round(2) }}
{{ list | first }}
{{ list | last }}
{{ list | length }}
```

## Git Workflow for Templates

### Releasing a new template version

```bash
git tag 1.0.0
git push origin 1.0.0
```

### For unreleased development

```bash
# Point to HEAD for testing:
copier copy --vcs-ref HEAD gh:user/template ./project

# Or use dirty working directory:
copier copy --vcs-ref HEAD /path/to/local/template ./project
```

### Version numbering (PEP 440)

```
1.0.0           # Release
1.0.1           # Patch
1.1.0           # Minor
2.0.0           # Major
2.0.0rc1        # Release candidate
2.0.0.dev0      # Development
```

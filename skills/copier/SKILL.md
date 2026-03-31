---
name: copier
license: MIT
description: |
  Create and manage project templates with Copier, a Python-based scaffolding tool. Use this skill whenever the user:
  - Wants to generate projects from templates (copier copy)
  - Needs to keep projects updated with template changes (copier update)
  - Is creating or maintaining a template itself (copier.yml, Jinja2 templates, tasks, migrations)
  - Has questions about template workflows, version management, or conditional prompts
  - Wants to re-apply a template to a project (copier recopy)
  - Needs help with .copier-answers.yml or template configuration
  Use Copier when working with project scaffolding, template versioning, or batch project generation. This skill covers creating templates with conditional questions, post-copy tasks, Jinja2 templating, and intelligent project updates.
---

# Copier: Project Template Scaffolding

Copier is a powerful Python library and CLI tool for rendering project templates and keeping generated projects in sync with template updates. It works with local paths and Git URLs, uses Jinja2 for templating, and handles complex workflows like version-aware updates and task execution.

## Core Concepts

**Templates** are Git repositories containing a `copier.yml` config file, Jinja2-templated files/directories, and optional tasks or migrations.

**Projects** are generated from templates and linked to them via `.copier-answers.yml`, enabling intelligent updates.

**Questionnaires** collect answers from users to customize each project. Answers become template variables.

## Quick Start

### Create a template:
```bash
# Initialize a git repo for your template
mkdir my_template && cd my_template && git init

# Create copier.yml with questions
cat > copier.yml << 'EOF'
project_name:
  type: str
  help: What is your project name?
module_name:
  type: str
  help: What is your Python module name?
EOF

# Create templated files (note the .jinja suffix)
mkdir -p "{{project_name}}"
cat > "{{project_name}}/{{module_name}}.py.jinja" << 'EOF'
print("Hello from {{module_name}}!")
EOF

# Commit everything
git add -A
git commit -m "Initial template"
git tag 0.1.0
```

### Generate a project from the template:
```bash
# From command line
copier copy path/to/template /path/to/destination

# From Python
from copier import run_copy
run_copy("path/to/template", "path/to/destination")

# From Git URL (shortcuts available: gh:, gl:)
copier copy gh:user/template /path/to/destination
```

### Update a project with template changes:
```bash
cd /path/to/project
copier update
```

## copier.yml Configuration

### Question Types
Define user prompts at the root level of `copier.yml`. Simple format or advanced:

```yaml
simple_version:
  "My project"

advanced_version:
  type: str              # bool, int, float, json, yaml, choice, multichoice, path
  help: "What is your name?"
  default: "John"
  placeholder: "Enter your name"
  secret: false          # Hide input if true
  choices:
    - Option 1
    - Option 2
  validator: "{% if len(name) < 3 %}Must be 3+ characters{% endif %}"
  when: "{{ include_optional }}"  # Show only if condition is true
```

### Special Settings
Copier settings start with underscore. Key ones:

```yaml
_min_copier_version: "9.0.0"
_subdirectory: "template"        # Render files from this subdirectory only
_exclude:                        # Patterns to skip
  - "*.pyc"
  - "__pycache__"
_skip_if_exists:                 # Files to keep if they exist
  - "README.md"
_tasks:                          # Post-copy shell commands (requires --trust flag)
  - "pip install -e ."
  - "git init"
_migrations:                     # Version-specific migration scripts
  "0.1.0->0.2.0": |
    import json
    # Migration code here
_message_before_copy: |
  ⚠️ This template requires Python 3.10+
_message_after_copy: |
  ✅ Project created! Run: pip install -e .
_answers_file: ".copier-answers.yml"  # Where to store answers
_envops:                         # Jinja2 environment options
  keep_trailing_newline: true
_jinja_extensions:
  - jinja2.ext.do
  - jinja2.ext.loopcontrols
```

### Conditional Questions & Dynamic Choices
```yaml
use_database:
  type: bool
  help: Use a database?
  default: false

db_type:
  type: str
  help: Which database?
  when: "{{ use_database }}"
  choices: |
    {%- if project_type == "web" %}
    - PostgreSQL
    - MySQL
    {%- else %}
    - SQLite
    {%- endif %}
```

## Templating

Copier uses Jinja2 for dynamic content. Templates are rendered if they end with `.jinja` (configurable).

### In file content:
```jinja
# {{project_name}}/README.md.jinja
# {{project_name.title()}}
By: {{author}}

{% if include_license %}
This project is licensed under MIT.
{% endif %}
```

### In file/directory names:
```
{{project_name}}/
  {{module_name}}.py.jinja
  config-{{environment}}.yaml.jinja
```

### Available Variables
- `_copier_answers`: User answers (JSON-serializable, excludes secrets)
- `_copier_conf`: Configuration object with `.answers_file`, `.data`, `.dst_path`, etc.
- All user-defined question answers (e.g., `{{ project_name }}`)
- Jinja2 filters from `jinja2-ansible-filters` (e.g., `to_nice_yaml`, `to_json`)

### Example:
```jinja
# Store answers for future updates
{{ _copier_answers|to_nice_yaml }}
```

## .copier-answers.yml

This file is auto-generated in the destination after copying. Keep it committed to enable intelligent updates:

```yaml
_commit: 0.1.0          # Template commit/tag used
_src_path: gh:user/template  # Template source
project_name: my_project
module_name: core
```

**Important:** Never edit this manually—Copier uses it to track template history and apply diffs correctly.

## Updating Projects

The `copier update` workflow:

1. Read `.copier-answers.yml` to find the previous template version
2. Compare template Git tags using PEP 440 versioning
3. Prompt user for new/changed answers (defaults to previous values)
4. Apply diffs from the template, intelligently merging changes

### Update options:
```bash
copier update --vcs-ref HEAD           # Update to HEAD instead of latest tag
copier update --defaults               # Use previous answers, skip prompts
copier update --data key=value         # Override specific answer
copier update --conflict inline        # Inline conflict markers (default)
copier update --conflict rej           # Separate .rej files for conflicts
```

If conflicts arise, review them manually before committing.

## CLI Commands

```bash
# Copy (generate from template)
copier copy [OPTIONS] SRC DST
  --data/-d KEY=VALUE              # Provide answers programmatically
  --defaults                       # Use all defaults, no prompts
  --vcs-ref REF                    # Git tag/branch to use (default: latest tag)
  --overwrite                      # Overwrite existing files
  --skip-if-exists                 # Skip files that exist
  --exclude PATTERN                # Skip matching paths
  --trust                          # Run tasks without prompting
  --pretend                        # Show what would happen, don't apply
  --quiet                          # Suppress output
  --help-all                       # Show all options

# Update (sync with template changes)
copier update [OPTIONS] [--vcs-ref REF] [DESTINATION]
  --defaults                       # Keep previous answers
  --conflict inline|rej            # Conflict resolution style
  --context-lines N                # Lines of context in diffs

# Recopy (re-apply template)
copier recopy [OPTIONS] [DESTINATION]
  # Re-applies template with existing answers, ignoring history
```

## Tasks & Migrations

### Tasks (post-copy commands)
Define in `copier.yml`:
```yaml
_tasks:
  - "git init"
  - "git add ."
  - "git commit -m 'Initial commit'"
```

Run with `--trust` flag (security feature—prevents untrusted code execution):
```bash
copier copy --trust gh:user/template ./project
```

### Migrations (version-specific transformations)
```yaml
_migrations:
  "0.1.0->0.2.0": |
    # Python code to transform answers before rendering new version
    answers["module_name"] = answers.get("module_name", "").lower()
    import json
    answers["config"] = json.dumps({"version": "2"})
```

## Common Patterns

### Template directory structure:
```
my_template/
├── copier.yml                   # Configuration & questions
├── .git/                        # Must be a Git repo
├── {{project_name}}/
│   ├── src/
│   │   └── {{module_name}}.py.jinja
│   └── tests/
├── .github/workflows/
├── README.md.jinja
└── {{_copier_conf.answers_file}}.jinja
```

### Multi-variant templates:
```yaml
_subdirectory: "templates/{{project_type}}"  # Render different template per type
```

### Protecting user changes during updates:
```yaml
_skip_if_exists:
  - "config.local.yaml"  # User's local config won't be overwritten
```

## Best Practices

- **Version templates with Git tags** using [PEP 440](https://peps.python.org/pep-0440/) (e.g., `1.0.0`, `2.0.0-rc1`)
- **Use `_subdirectory`** to keep template files separate: `_subdirectory: "template"` puts template files in a subdirectory
- **Commit `.copier-answers.yml`** in generated projects so future updates work
- **Use `_skip_if_exists`** for files users customize (config, keys, etc.)
- **Enable `_tasks` only when safe**; users must pass `--trust` to run them
- **Use `when:` fields** for conditional questions, not comment-based logic
- **Use validators** for input validation: `"{% if len(x) < 3 %}Too short{% endif %}"`
- **Test updates carefully**: conflicts can occur if template and project diverge significantly
- **Use conflict hooks**: add pre-commit hooks to catch merge conflicts before committing

## Common Pitfalls

- ❌ **Forgetting `--trust`**: Tasks won't run without it
- ❌ **Editing `.copier-answers.yml` manually**: Breaks the update diff algorithm
- ❌ **Not tagging template releases**: Updates will use dirty HEAD instead of stable versions
- ❌ **Template not a Git repo**: Copier can't version or update projects without Git history
- ❌ **Jinja2 syntax in non-.jinja files**: Only `.jinja` files are rendered
- ❌ **Complex update conflicts**: Minimize by avoiding large manual changes to generated code
- ❌ **Forgetting to commit `.copier-answers.yml`**: Project can't be updated later

## Python API

```python
from copier import run_copy, run_update, run_recopy

# Copy
run_copy(
    "path/to/template",
    "path/to/destination",
    data={"project_name": "my_app"},
    defaults=False,
    overwrite=False,
    trust=False,
    vcs_ref="v1.0.0"
)

# Update
run_update(
    "path/to/destination",
    defaults=False,
    overwrite=False,
    vcs_ref=None  # None = latest tag
)

# Recopy
run_recopy("path/to/destination", defaults=True)
```

## Documentation

For detailed docs, see: https://copier.readthedocs.io/en/stable/

Key sections:
- [Creating templates](https://copier.readthedocs.io/en/stable/creating/)
- [Generating projects](https://copier.readthedocs.io/en/stable/generating/)
- [Updating projects](https://copier.readthedocs.io/en/stable/updating/)
- [Configuration reference](https://copier.readthedocs.io/en/stable/configuring/)

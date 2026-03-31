# Copier Agent Skill

A comprehensive skill for creating, managing, and updating project templates using **Copier**, a Python-based project scaffolding tool.

## What This Skill Covers

This skill provides expert guidance on:

### Template Creation
- Structuring templates with `copier.yml` configuration
- Jinja2 templating for dynamic file content and names
- Question types and validation patterns
- Conditional questions and dynamic choices
- Post-copy tasks and migrations

### Project Generation
- Using `copier copy` to create projects from templates
- Providing answers programmatically with `--data`
- Handling versioned templates with Git tags
- Using template variants with `_subdirectory`

### Project Updates
- Using `copier update` to sync with template changes
- Managing `.copier-answers.yml` for reproducible updates
- Resolving merge conflicts during updates
- Preserving user customizations with `_skip_if_exists`

### Advanced Features
- Post-copy shell tasks (requiring `--trust` flag)
- Version-specific migrations
- Custom Jinja2 extensions
- Security best practices
- Troubleshooting common issues

## Skill Files

```
copier-skill/
├── SKILL.md                          # Main skill documentation (351 lines)
├── evals/
│   └── evals.json                    # 5 comprehensive test cases
└── references/
    └── advanced-patterns.md          # Deep-dive reference material
```

### SKILL.md Contents
- Core concepts and quick start
- CLI commands with all major flags
- Complete `copier.yml` configuration schema
- Jinja2 templating patterns and examples
- `.copier-answers.yml` file structure
- Update workflow and conflict resolution
- Tasks and migrations
- Best practices and common pitfalls
- Python API examples
- Links to official documentation

### references/advanced-patterns.md
- Detailed schema reference
- Advanced question patterns (conditional, dynamic, validated)
- Settings reference (`_*` keys)
- Complex Jinja2 patterns
- Multi-variant template structures
- Update workflow details
- Task security guidelines
- Troubleshooting guide
- Git workflow for template releases

## Test Coverage

5 comprehensive test cases covering:

1. **FastAPI Template Creation** - Setting up a template with conditional features
2. **Project Update Workflow** - Updating a project while preserving customizations
3. **Advanced Configuration** - Tasks, variants, and conditional questions
4. **Missing Answers File Recovery** - Understanding consequences and recovery options
5. **Conditional & Validated Questions** - Complex question configurations

## When to Use This Skill

Invoke this skill when the user:
- Is creating a reusable project template
- Needs to generate multiple projects from a template
- Wants to keep projects in sync with template updates
- Has questions about `copier.yml` configuration
- Is working with Jinja2 templating in projects
- Needs help with version management or migrations
- Is troubleshooting template or update issues
- Wants to understand `.copier-answers.yml` and its role

## Key Features

✅ **Comprehensive Coverage** - From creating first template to managing complex updates
✅ **Practical Examples** - Real-world patterns and configurations
✅ **Security Focused** - Explains `--trust` requirement and safe task patterns
✅ **Progressive Disclosure** - Main SKILL.md for quick reference, advanced-patterns.md for deep dives
✅ **Best Practices** - Common pitfalls highlighted and explained
✅ **Multi-variant Templates** - Support for different project types from one template
✅ **Conflict Resolution** - Guidance on handling merge conflicts during updates
✅ **Version Management** - Using Git tags and PEP 440 versioning

## Documentation Links

- **Official Docs**: https://copier.readthedocs.io/en/stable/
- **Creating Templates**: https://copier.readthedocs.io/en/stable/creating/
- **Generating Projects**: https://copier.readthedocs.io/en/stable/generating/
- **Updating Projects**: https://copier.readthedocs.io/en/stable/updating/
- **Configuration**: https://copier.readthedocs.io/en/stable/configuring/

## Installation

Install Copier:
```bash
pip install copier
# or
pipx install copier
# or
brew install copier
```

## Quick Example

### Create a template:
```bash
mkdir my_template && cd my_template
git init

cat > copier.yml << 'EOF'
project_name:
  type: str
  help: Project name?
EOF

mkdir "{{project_name}}"
echo 'print("Hello {{project_name}}")' > "{{project_name}}/main.py.jinja"

git add -A && git commit -m "init" && git tag 0.1.0
```

### Generate a project:
```bash
copier copy /path/to/my_template ./my_project
```

### Update the project:
```bash
cd my_project
copier update
```

## Skill Metadata

- **Name**: copier
- **Type**: Reference/Template Guidance
- **Domain**: Project Scaffolding, Template Management, Build Automation
- **Trigger Contexts**: Template creation, project generation, template updates, Jinja2 templating
- **Complexity**: Advanced (supports beginner to expert workflows)
- **Status**: Complete and ready for use

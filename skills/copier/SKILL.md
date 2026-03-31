---
name: copier
description: >
  Expert guide for working with the Copier template ecosystem (copy, update, recopy,
  check-update, authoring copier.yaml/copier.yml, Jinja templating, questions, tasks,
  migrations, answers files). Use this skill whenever the user mentions copier,
  copier.yaml, copier.yml, copier template, scaffolding a project from a template,
  updating a generated project, .copier-answers.yml, recopy, Jinja suffix, _tasks,
  _migrations, _exclude, _subdirectory, or asks to create, debug, test, or update
  a copier template or generated project — even if they don't say the word "copier"
  explicitly but describe template-driven project generation or lifecycle updates.
---

# Copier — template authoring and project lifecycle

Copier renders project templates (Jinja + YAML questionnaire) and manages the
lifecycle of generated projects. Two audiences: **template authors** (create/maintain
templates) and **consumers** (copy/update projects).

## 1. Core operations — use the right one

| Command | Purpose | When to use |
|---|---|---|
| `copier copy <src> <dst>` | Generate new project | First render; also overlays onto preexisting dir |
| `copier update` (run inside project) | Smart update to newer template | Template evolved; preserves local edits via 3-way merge |
| `copier recopy` | Dumb re-render, keep answers, discard history | Broken update, deleted-file recovery, or update algorithm can't run |
| `copier check-update` | Report if template has newer version | Manual (`plain`) or CI (`--output-format json` / `--quiet` exit 2 = update available) |

Common flags (copy):

```bash
copier copy --trust <src> <dst>            # required if template has _tasks/_migrations/_jinja_extensions
copier copy --trust --defaults <src> <dst> # non-interactive, all defaults
copier copy -d 'key=value' -d 'list=[a, b]' <src> <dst>  # override answers
copier copy --data-file answers.yml <src> <dst>          # bulk answers (--data wins on conflict)
copier copy --vcs-ref HEAD <src> <dst>     # dev: include dirty/unreleased changes
copier copy --vcs-ref v2.0.0 <src> <dst>   # pin version
copier copy --skip-tasks <src> <dst>       # skip _tasks (NOT migrations)
copier copy --pretend <src> <dst>          # dry run
copier copy --overwrite <src> <dst>        # overwrite without asking
copier copy -f <src> <dst>                 # = --defaults --overwrite
```

Update flags (run in project dir, clean `git status` first):

```bash
copier update --trust                      # standard
copier update --trust --defaults           # reuse all prior answers
copier update --trust --defaults -d 'q=new'  # change one answer only
copier update --vcs-ref=:current:          # re-answer questions, keep template version
copier update --conflict rej|inline        # conflict style (default inline)
copier update --skip-answered              # keep recorded answers, don't re-ask
```

## 2. Template anatomy

```text
my-template/                    # usually a Git repo with PEP 440 tags (v1.0.0)
├── copier.yaml (or copier.yml) # questions + _settings (underscore-prefixed)
├── template/                   # actual payload when _subdirectory: template
│   ├── {{ _copier_conf.answers_file }}.jinja
│   ├── README.md.jinja         # *.jinja → rendered, suffix stripped
│   └── .gitignore              # no suffix → copied verbatim
└── includes/ (optional)        # macros/partials — must be _excluded
```

Key settings in `copier.yaml`:

```yaml
_min_copier_version: "9.0.0"   # abort if installed copier is older
_subdirectory: template        # isolate payload from template meta files
_templates_suffix: .jinja      # which files Jinja renders ("" = render everything)
_answers_file: .copier-answers.yml
_preserve: [.copier-answers.yml]
_exclude: ["~*", "*.py[co]", __pycache__, "*.rej"]
_tasks: ["git init", "mise install"]
_message_after_copy: |
  Your project "{{ project_name }}" was created. Run `mise run check`.
_message_after_update: |
  Your project "{{ project_name }}" was updated. Resolve conflicts, then check.
```

`_exclude` vs `_skip_if_exists` vs `_tasks`-only-once:

- `_exclude`: never copy (gitignore syntax via `pathspec`; `!` negates).
  Templatable. Patterns match **destination paths** (after `.jinja` stripping),
  so `*.bar` already covers `foo.bar.jinja` → `foo.bar`; do NOT add `*.bar.jinja`.
  Use `_copier_operation == 'update'` guard for copy-once files.
- `_skip_if_exists`: copy once; never overwrite if present; recreate on
  `update` if missing (good for generated secrets).
- `_exclude` with update-guard: never re-render on update even if missing.

## 3. Questions — best practices

Order matters: questions are asked top-to-bottom; a default/validator/`when`
can only reference **earlier** answers.

```yaml
project_name:
  type: str
  help: Human-readable project name
  default: my base project

project_slug:
  type: str
  help: URL/filesystem-safe slug
  default: "{{ project_name|lower|replace(' ', '-')|replace('_', '-') }}"
  validator: "{% if not (project_slug | regex_search('^[a-z][a-z0-9-]+$')) %}Use lowercase, digits, dashes; start with a letter.{% endif %}"

use_ci:
  type: bool
  help: Add CI workflow?
  default: true

ci_provider:
  type: str
  choices:
    GitHub CI: github      # key shown to user, VALUE stored in template
    GitLab CI: gitlab
  default: github          # default must be the VALUE, not the key
  when: "{{ use_ci }}"     # skip unless use_ci is true

deploy_key:
  type: str
  secret: true             # hidden prompt, excluded from answers file
  default: "{{ _external_data.secrets.deploy_key | default('changeme', true) }}"
  placeholder: "paste deploy key"  # visual hint only, not a value
```

Rules:

- `type`: `str|int|float|bool|json|yaml|path` (`yaml` default). Keep choice
  values to one type; prefer `str` and convert in template code.
- Always give `help` and a sane `default` (omit default only to force input).
  `--defaults` fails on default-less questions unless `-d` supplies them.
- `validator`: Jinja that renders **empty = valid**, non-empty = error message.
- `when`: `false` (boolean) or templated string. Skipped questions are not
  stored, but their default is in render context. Use `when: false` for computed
  values; render `{{ UNSET }}` as default to leave the var undefined.
- `choices`: default must match value type. For multiselect bracket values quote
  explicitly: `default: '["[", "]"]'`, CLI: `-d 'brackets=["[", "]"]'`.
- `secret: true` **requires** a real default of the question's type; the value
  never lands in the answers file. `default: null` does NOT satisfy this —
  verified on Copier 9: `copy --defaults` crashes with
  `InvalidTypeError: Invalid answer "None" ... of type "str"`. Use a static
  fallback or `_external_data` (see §5).
- Conditional/dynamic choices: either `validator` per choice (visible but
  disabled with message) or templated `choices: |` block (hidden). When mixing
  both, wrap validator in `{% raw %}...{% endraw %}`.
- Templating is allowed **only inside string values**, only with
  already-answered variables. Interactive answers are never re-rendered.
- Computed, non-asked value: `default: "{{ earlier_var + 1 }}"` + `when: false`.
  To freeze it across updates (e.g. `copyright_year`), also dump it explicitly
  in the answers template (see §5).
- Prefer well-known user defaults names so `settings.yml` reuse works:
  `user_name`, `user_email`, `github_user`, `gitlab_user`.

## 4. Jinja rendering rules

- Rendered: files ending in `_templates_suffix` (default `.jinja`) — suffix is
  stripped on output. Everything else copied verbatim. If both `README.md` and
  `README.md.jinja` exist, the non-suffixed one is **ignored**.
- Directory names are templated but must **NOT** end with the suffix.
- File/dir names, `_exclude`/`_skip_if_exists` patterns, `_messages_*`,
  `_tasks`, `_migrations`, question `default/help/choices/validator/when` can
  all contain Jinja.
- Conditional file: `{% if use_precommit %}.pre-commit-config.yaml{% endif %}.jinja`
  — suffix stays **outside** the `{% if %}` or the file is not recognized.
  Use single quotes in path conditions (double quotes are illegal on Windows).
- Multi-pattern conditional exclude: one list item can render a whole
  newline-separated gitignore block.
- `{% yield item from list %}{{ item }}{% endyield %}` in a path loops to
  generate many files/dirs; loop vars are in scope inside generated files.
- Reuse snippets via `{% include 'partial.jinja' %}` or
  `{% from 'macros.jinja' import thing %}` (paths relative to template root).
  Put partials in `includes/` and `_exclude` it, or use `_subdirectory` so they
  are never copied. In path names use `pathjoin('includes','x.jinja')` (POSIX
  separator required).
- Builtins: all Jinja2 + `jinja2-ansible-filters` (`to_nice_yaml`,
  `to_nice_json`, `regex_search`, `ans_random|hash('sha512')` for secrets, ...).
- `_envops` default keeps trailing newlines. Set
  `_envops: {undefined: jinja2.StrictUndefined}` to fail fast on typos.
- Useful context: `_copier_answers` (safe, serializable, has `_commit`,
  `_src_path`), `_copier_conf` (has `.data`, `.dst_path`, `.src_path`,
  `.sep`, `.os`, `.answers_file` — WARNING `.data` may contain secrets),
  `_folder_name`, `_copier_python`, `_copier_phase` (prompt/tasks/migrate/render),
  `_copier_operation` (copy/update — tasks/exclude only), `_external_data`,
  `UNSET`.
- `_external_data`: `{namespace: relative/path.yml}` lazily parsed as YAML.
  Use for multi-template composition (read parent answers) or loading ignored
  secrets. Paths outside project root require `--trust`.

## 5. Answers file — the update contract

Template must ship `{{ _copier_conf.answers_file }}.jinja` (default name
`.copier-answers.yml`) with exactly:

```jinja
# Changes here will be overwritten by Copier
{{ _copier_answers|to_nice_yaml -}}
```

- Commit it in generated projects. Without it there is no smart update.
- **NEVER edit it by hand** — it makes Copier believe a different answer set
  produced the project and corrupts future diffs. Change answers via
  `copier update --defaults -d 'q=new'`, never via editor.
- Secrets (`secret: true`) are excluded automatically — that is why they need
  `_external_data` round-tripping if they must persist.
- Multi-template projects: each template gets its own file
  (`-a .copier-answers.main.yml`, `-a .copier-answers.ci.yml`, ...) and is
  updated independently.

## 6. Tasks and migrations (unsafe — need `--trust`)

```yaml
_tasks:
  - "git init"
  - "git rev-parse --verify HEAD >/dev/null 2>&1 || git commit --allow-empty -m 'Init commit'"
  - ["mise", "install"]            # array form: no shell, no escaping bugs
  - command: ["{{ _copier_python }}", task.py]
    when: "{{ _copier_operation == 'copy' }}"
  - command: rm {{ name }}/README.md
    when: "{{ _copier_conf.os in ['linux', 'macos'] }}"

_migrations:
  - version: v2.0.0               # run only when old < v2.0.0 <= new (PEP 440)
    command: rm -rf ./old-folder
    when: "{{ _stage == 'before' }}"
```

- `_tasks` run after **every** copy and update. `_migrations` run only on
  update (optionally version-gated, `before`/`after` stage via `_stage`).
  `--skip-tasks` skips tasks but **not** migrations.
- Each item runs in its own subprocess with `$STAGE`, `$VERSION_FROM`,
  `$VERSION_TO`, `$VERSION_CURRENT` (+ PEP 440-normalized variants) in env.
  Answers file is reloaded after `before` migrations, so they can rewrite answers.
- Keep tasks idempotent, fast, and offline-safe where possible; prefer array
  form; gate OS-specific commands on `_copier_conf.os`.
- Any use of tasks/migrations/`_jinja_extensions` makes `copier` abort with
  exit 4 unless consumer passes `--trust`/`--UNSAFE` (or marks the source in
  `trust:` in `settings.yml`). Verified: without `--trust` Copier aborts
  **before rendering anything** — it does NOT render files and silently skip
  tasks. To render without running tasks: `--trust --skip-tasks`.

## 7. Versioning, update safety, conflict recovery

- Tag template releases with stable PEP 440 versions (`v1.0.0`). Default copy
  and `update` resolve to the **latest tag**, not the branch tip. Never move a
  released tag; use branches or explicit `--vcs-ref` for moving refs.
- `--vcs-ref HEAD` = current checkout **including dirty files** (needed for
  local template dev). Without it, dirty files are silently ignored because a
  tag is checked out instead (FAQ gotcha). `--vcs-ref=:current:` = re-ask
  without changing version.
- Before `update`: clean `git status`. Add merge-conflict guard hooks:
  `check-merge-conflict --assume-in-merge` for `inline`, forbid `*.rej` for
  `rej` style.
- How update works: regen old-tag template → diff vs current project → apply
  pre-migrations → render new-tag template → replay diff → post-migrations.
  Template-deleted-but-project-deleted paths stay deleted; `skip_if_exists`
  paths are always restored. If the old template can't be regenerated (missing
  external resource, incompatible Jinja extension, ancient Copier), fall back
  to `copier recopy` and resolve with git diff (loses smart merge for that run).
- Abort a bad update: `git reset; git checkout .; git clean -d -i`
  (`checkout <branch>` / `merge --abort` do NOT work).

## 8. Caveats and known-issue checklist (verify before shipping)

1. `_exclude` in YAML **replaces** defaults (you lose `copier.yaml`, `.git`, …).
   CLI `-x` **extends**. With `_subdirectory` set to a real dir, default
   `_exclude` becomes `[]`. `_exclude` matches **destination** paths.
2. `copier copy ./src ./dst` on a dirty template checks out latest **tag** —
   dirty files missing. Use `-r HEAD` while developing.
3. Shallow template clones cause huge git CPU use — use full clones.
4. Never put credentials in the source URL (`https://user:pass@…`) — they are
   recorded in `_src_path` in the answers file. Use SSH keys / credential helpers.
5. `secret` questions need a default; `choices` defaults must be values with
   matching `type`; multiselect bracket literals need inner quotes.
6. `when: false` values aren't stored — explicitly merge them into the answers
   dump if they must be frozen (`{{ dict(_copier_answers, foo=foo)|to_nice_yaml }}`).
7. Referencing a later question, or templating a key (not value), or unquoted
   `default: {{ 'x' }}` are all invalid — keep YAML valid, template values only.
8. `force` = skip prompts + overwrite; `defaults` = use defaults but still fail
   on default-less questions; `overwrite` = overwrite files only.
   `cleanup_on_error` deletes dst only if Copier created it.
9. `preserve_symlinks: false` (default) replaces links with target content.
10. Copier ≤5 used `.tmpl` suffix and `[[ ]]` delimiters. For cross-version
    templates pin `_min_copier_version` and, if needed, set `_envops` to the
    legacy delimiters. Copier 7+ ignores the legacy fallback.
11. `_jinja_extensions` code runs at render — audit it, and tell users which
    extra pip package to install in Copier's own env
    (`pipx inject copier <pkg>` / `uv tool install --with <pkg> copier`).
12. One template = one repo. Don't host multiple versioned templates in one
    repo to share tags — subdirectory-per-variant keyed off an answer
    (`_subdirectory: "{{ engine }}"`) is the supported exception.
13. `copier update` needs Git on **both** template and project sides for smart
    merge; `recopy` is the fallback when that contract is broken.

## 9. Local verification loop (run before commit/release)

```bash
copier copy --trust --defaults --skip-tasks . /tmp/copier-test   # fast render check
rm -rf /tmp/copier-test && copier copy --trust --defaults -r HEAD . /tmp/copier-test
cd /tmp/copier-test && git init && git add . && git commit -qm init
copier check-update          # expect "up-to-date"
# simulate template change → tag → copier update --trust --defaults
```

Also run the project's own hygiene (`mise run check` / `pre-commit run --all-files`)
in the generated copy, not just in the template repo.

## 10. References

- Docs: https://copier.readthedocs.io/en/stable/ (creating, configuring,
  generating, updating, settings, FAQ)
- Public templates: `https://github.com/topics/copier-template`
- Local example in this workspace: `copier.yaml` + `template/` (subdirectory
  pattern, `_preserve`, tasks, slug validator, answers-file template)

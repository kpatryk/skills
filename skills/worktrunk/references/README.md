<!-- markdownlint-disable MD033 -->

<h1><img src="docs/static/logo.png" alt="Worktrunk logo" width="50" align="absmiddle">&nbsp;&nbsp;Worktrunk</h1>

[![Docs](https://img.shields.io/badge/docs-worktrunk.dev-blue?style=for-the-badge&logo=gitbook)](https://worktrunk.dev)
[![Crates.io](https://img.shields.io/crates/v/worktrunk?style=for-the-badge&logo=rust)](https://crates.io/crates/worktrunk)
[![License: MIT OR Apache-2.0](https://img.shields.io/badge/license-MIT%20OR%20Apache--2.0-blue?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![CI](https://img.shields.io/github/actions/workflow/status/max-sixty/worktrunk/ci.yaml?event=push&branch=main&style=for-the-badge&logo=github)](https://github.com/max-sixty/worktrunk/actions?query=branch%3Amain+workflow%3Aci)
[![Codecov](https://img.shields.io/codecov/c/github/max-sixty/worktrunk?style=for-the-badge&logo=codecov)](https://codecov.io/gh/max-sixty/worktrunk)
[![Stars](https://img.shields.io/github/stars/max-sixty/worktrunk?style=for-the-badge&logo=github)](https://github.com/max-sixty/worktrunk/stargazers)

> **March 2026**: Worktrunk was [released](https://x.com/max_sixty/status/2006077845391724739?s=20) at the start of the year, and has quickly become the most popular git worktree manager. It's built with love (there's no slop!). Please let me know any frictions at all; I'm intensely focused on continuing to make Worktrunk excellent, and the biggest help is folks posting problems they perceive.

Worktrunk is a CLI for git worktree management, designed for running AI agents in parallel.

Worktrunk's three core commands make worktrees as easy as branches. Plus, Worktrunk has a bunch of quality-of-life features to simplify working with many parallel changes, including hooks to automate local workflows.

Scaling agents becomes trivial. A quick demo:

![Worktrunk Demo](https://cdn.jsdelivr.net/gh/max-sixty/worktrunk-assets@main/assets/docs/light/wt-core.gif)

> ### 📚 Full documentation at [worktrunk.dev](https://worktrunk.dev) 📚

<!-- ⚠️ AUTO-GENERATED from docs/content/worktrunk.md#context-git-worktrees..worktrunk-makes-git-worktrees-as-easy-as-branches — edit source to update -->

## Context: git worktrees

AI agents like Claude Code and Codex can handle longer tasks without
supervision, such that it's possible to manage 5-10+ in parallel. Git's native
worktree feature give each agent its own working directory, so they don't step
on each other's changes.

But the git worktree UX is clunky. Even a task as small as starting a new
worktree requires typing the branch name three times: `git worktree add -b feat
../repo.feat`, then `cd ../repo.feat`.

## Worktrunk makes git worktrees as easy as branches

Worktrees are addressed by branch name; paths are computed from a configurable template.

> Start with the core commands

**Core commands:**

<table class="cmd-compare">
  <thead>
    <tr>
      <th>Task</th>
      <th>Worktrunk</th>
      <th>Plain git</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Switch worktrees</td>
      <td><pre>wt switch feat</pre></td>
      <td><pre>cd ../repo.feat</pre></td>
    </tr>
    <tr>
      <td>Create + start Claude</td>
      <td><pre>wt switch -c -x claude feat</pre></td>
      <td><pre>git worktree add -b feat ../repo.feat && \
cd ../repo.feat && \
claude</pre></td>
    </tr>
    <tr>
      <td>Clean up</td>
      <td><pre>wt remove</pre></td>
      <td><pre>cd ../repo && \
git worktree remove ../repo.feat && \
git branch -d feat</pre></td>
    </tr>
    <tr>
      <td>List with status</td>
      <td><pre>wt list</pre></td>
      <td><pre>git worktree list</pre> (paths only)</td>
    </tr>
  </tbody>
</table>

> Expand into the more advanced commands as needed

**Workflow automation:**

- **[Hooks](https://worktrunk.dev/hook/)** — run commands on create, pre-merge, post-merge, etc
- **[LLM commit messages](https://worktrunk.dev/llm-commits/)** — generate commit messages from diffs
- **[Merge workflow](https://worktrunk.dev/merge/)** — squash, rebase, merge, clean up in one command
- **[Interactive picker](https://worktrunk.dev/switch/#interactive-picker)** — browse worktrees with live diff and log previews
- **[Copy build caches](https://worktrunk.dev/step/)** — skip cold starts by sharing `target/`, `node_modules/`, etc between worktrees
- **[`wt list --full`](https://worktrunk.dev/list/#full-mode)** — [CI status](https://worktrunk.dev/list/#ci-status) and [AI-generated summaries](https://worktrunk.dev/list/#llm-summaries) per branch
- **[PR checkout](https://worktrunk.dev/switch/#pull-requests-and-merge-requests)** — `wt switch pr:123` to jump straight to a PR's branch
- **[Dev server per worktree](https://worktrunk.dev/hook/#dev-servers)** — `hash_port` template filter gives each worktree a unique port
- ...and **[lots more](#next-steps)**

A demo with some advanced features:

![Worktrunk omnibus demo: multiple Claude agents in Zellij tabs with hooks, LLM commits, and merge workflow](https://raw.githubusercontent.com/max-sixty/worktrunk-assets/main/assets/docs/light/wt-zellij-omnibus.gif)

<!-- END AUTO-GENERATED -->

<!-- ⚠️ AUTO-GENERATED from docs/content/worktrunk.md#install..further-reading — edit source to update -->

## Install

**Homebrew (macOS & Linux):**

```bash
brew install worktrunk && wt config shell install
```

Shell integration allows commands to change directories.

**Cargo:**

```bash
cargo install worktrunk && wt config shell install
```

<details>
<summary><strong>Windows</strong></summary>

On Windows, `wt` defaults to Windows Terminal's command. Winget additionally installs Worktrunk as `git-wt` to avoid the conflict:

```bash
winget install max-sixty.worktrunk
git-wt config shell install
```

Alternatively, disable Windows Terminal's alias (Settings → Privacy & security → For developers → App Execution Aliases → disable "Windows Terminal") to use `wt` directly.

</details>

**Arch Linux:**

```bash
paru worktrunk-bin && wt config shell install
```

## Quick start

Create a worktree for a new feature:

```console
$ wt switch --create feature-auth
✓ Created branch feature-auth from main and worktree @ repo.feature-auth

```

This creates a new branch and worktree, then switches to it. Do your work, then check all worktrees with [`wt list`](https://worktrunk.dev/list/):

```console
$ wt list
  Branch        Status        HEAD±    main↕  Remote⇅  Commit    Age   Message
@ feature-auth  +   –      +53                         0e631add  1d    Initial commit
^ main              ^⇡                         ⇡1      0e631add  1d    Initial commit

○ Showing 2 worktrees, 1 with changes, 1 column hidden

```

The `@` marks the current worktree. `+` means staged changes, `⇡` means unpushed commits.

When done, either:

**PR workflow** — commit, push, open a PR, merge via GitHub/GitLab, then clean up:

```bash
wt step commit                    # commit staged changes
gh pr create                      # or glab mr create
wt remove                         # after PR is merged
```

**Local merge** — squash, rebase onto main, fast-forward merge, clean up:

```console
$ wt merge main
◎ Generating commit message and committing changes... (2 files, +53, no squashing needed)
  Add authentication module
✓ Committed changes @ a1b2c3d
◎ Merging 1 commit to main @ a1b2c3d (no rebase needed)
  * a1b2c3d Add authentication module
   auth.rs | 51 +++++++++++++++++++++++++++++++++++++++++++++++++++
   lib.rs  |  2 ++
   2 files changed, 53 insertions(+)
✓ Merged to main (1 commit, 2 files, +53)
◎ Removing feature-auth worktree & branch in background (same commit as main, _)
○ Switched to worktree for main @ repo

```

For parallel agents, create multiple worktrees and launch an agent in each:

```bash
wt switch -x claude -c feature-a -- 'Add user authentication'
wt switch -x claude -c feature-b -- 'Fix the pagination bug'
wt switch -x claude -c feature-c -- 'Write tests for the API'
```

The `-x` flag runs a command after switching; arguments after `--` are passed to it. Configure [post-start hooks](https://worktrunk.dev/hook/) to automate setup (install deps, start dev servers).

## Next steps

- Learn the core commands: [`wt switch`](https://worktrunk.dev/switch/), [`wt list`](https://worktrunk.dev/list/), [`wt merge`](https://worktrunk.dev/merge/), [`wt remove`](https://worktrunk.dev/remove/)
- Set up [project hooks](https://worktrunk.dev/hook/) for automated setup
- Explore [LLM commit messages](https://worktrunk.dev/llm-commits/), [interactive
  picker](https://worktrunk.dev/switch/#interactive-picker), [Claude Code integration](https://worktrunk.dev/claude-code/), [CI
  status & PR links](https://worktrunk.dev/list/#ci-status)
- Browse [tips & patterns](https://worktrunk.dev/tips-patterns/) for recipes: aliases, dev servers, databases, agent handoffs, and more
- Run `wt --help` or `wt <command> --help` for quick CLI reference

## Further reading

- [Claude Code: Best practices for agentic coding](https://www.anthropic.com/engineering/claude-code-best-practices) — Anthropic's official guide, including the worktree pattern
- [Shipping faster with Claude Code and Git Worktrees](https://incident.io/blog/shipping-faster-with-claude-code-and-git-worktrees) — incident.io's workflow for parallel agents
- [Git worktree pattern discussion](https://github.com/anthropics/claude-code/issues/1052) — Community discussion in the Claude Code repo
- [@DevOpsToolbox's video on Worktrunk](https://youtu.be/WBQiqr6LevQ?t=345)
- [git-worktree documentation](https://git-scm.com/docs/git-worktree) — Official git reference

<!-- END AUTO-GENERATED -->

## Contributing

- ⭐ Star the repo
- Tell a friend about Worktrunk
- [Open an issue](https://github.com/max-sixty/worktrunk/issues/new)

> ### 📚 Full documentation at [worktrunk.dev](https://worktrunk.dev) 📚

### Star history

<a href="https://star-history.com/#max-sixty/worktrunk&Date">
  <img src="https://api.star-history.com/svg?repos=max-sixty/worktrunk&type=Date" width="500" alt="Star History Chart">
</a>

# Git vs `gh`: Git Commands and GitHub CLI Study Guide

> **Primary sources**
> - https://cli.github.com/manual/
> - https://docs.github.com/en/github-cli
> - https://docs.github.com/en/github-cli/github-cli/quickstart
> - https://docs.github.com/en/pull-requests/get-started/pull-request-quickstart
> - https://github.blog/news-insights/product-news/supercharge-your-command-line-experience-github-cli-is-now-in-beta/

## Overview

`git` and `gh` are related, but they solve different problems.

- **`git`** is the distributed version control system. It manages commits, branches, tags, merges, local history, and synchronization with Git remotes.
- **`gh`** is the **GitHub CLI**. It talks to GitHub and lets you work with GitHub-specific features such as pull requests, issues, Actions, releases, repositories, projects, Codespaces, rulesets, secrets, and the GitHub API.

A good mental model is:

```text
git = manage source-code history
gh  = manage GitHub
```

You often use them together.

```text
Local files
   |
   v
git add / commit / branch
   |
   v
git push
   |
   v
GitHub repository
   |
   +--> gh pr
   +--> gh issue
   +--> gh run / gh workflow
   +--> gh release
   +--> gh repo
   +--> gh api
```

---

## The Core Difference

| Task | `git` | `gh` |
|---|---|---|
| Track file changes | Yes | No |
| Create commits | Yes | No |
| Create/switch branches | Yes | Limited workflow helpers |
| Merge branches locally | Yes | No |
| Push/pull/fetch | Yes | Usually delegates repository transfer to Git |
| Clone repositories | Yes | Yes (`gh repo clone`) |
| Create GitHub repository | No | Yes |
| Create pull request | No | Yes |
| Review/merge pull request | No | Yes |
| Create/list issues | No | Yes |
| Check GitHub Actions | No | Yes |
| Trigger workflows | No | Yes |
| Manage releases | No | Yes |
| Manage GitHub Projects | No | Yes |
| Call GitHub REST/GraphQL API | No | Yes (`gh api`) |
| Authenticate to GitHub | Git credential mechanisms | `gh auth login` |

The distinction is important for GitHub Foundations:

> **Git is not GitHub.** Git is the version control technology. GitHub is a hosted collaboration platform built around Git repositories.

---

## Typical `git` Usage

### Configure identity

```cli
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

### Create or clone a repository

```cli
git init
```

or:

```cli
git clone https://github.com/OWNER/REPO.git
```

### Inspect changes

```cli
git status
git diff
git log
```

### Stage and commit

```cli
git add .
git commit -m "Add feature"
```

### Work with branches

```cli
git branch
git switch -c feature-branch
git switch main
```

Older syntax:

```cli
git checkout -b feature-branch
```

### Synchronize

```cli
git fetch
git pull
git push
```

These operations belong to Git itself.

---

# What `gh` Is Used For

GitHub CLI is installed separately from Git and uses the `gh` command.

GitHub describes it as a command-line interface that brings GitHub functionality such as pull requests, issues, Actions, repositories, and other GitHub features into the terminal.

## Authenticate

```cli
gh auth login
```

Useful verification:

```cli
gh auth status
```

GitHub CLI can also use environment variables such as:

```text
GH_TOKEN
GITHUB_TOKEN
GH_HOST
GH_REPO
```

---

# Most Important `gh` Command Families

## 1. `gh repo` — Repository Management

Use `gh repo` for GitHub repository operations.

### Clone

```cli
gh repo clone OWNER/REPO
```

This overlaps with:

```cli
git clone https://github.com/OWNER/REPO.git
```

Difference:

- `git clone` is generic Git.
- `gh repo clone` understands GitHub repository names directly and uses your GitHub CLI authentication/configuration.

### Create a repository

```cli
gh repo create
```

Example:

```cli
gh repo create my-project --public
```

You cannot create a GitHub.com repository with normal `git` commands alone.

### View repository details

```cli
gh repo view
```

Open it in a browser:

```cli
gh repo view --web
```

### Fork

```cli
gh repo fork OWNER/REPO
```

### List your repositories

```cli
gh repo list
```

### Other repository operations

```cli
gh repo rename
gh repo archive
gh repo delete
gh repo sync
```

---

## 2. `gh pr` — Pull Requests

This is one of the biggest reasons to use `gh`.

Git has branches and merges, but **pull requests are a GitHub feature**, not a Git feature.

### Create a pull request

```cli
gh pr create
```

A convenient form:

```cli
gh pr create --fill
```

Draft:

```cli
gh pr create --draft
```

### List PRs

```cli
gh pr list
```

### View PR

```cli
gh pr view 123
```

Open in browser:

```cli
gh pr view 123 --web
```

### Check out a PR locally

```cli
gh pr checkout 123
```

This is useful when reviewing another person's pull request.

### Review PR

```cli
gh pr review 123
```

Approve:

```cli
gh pr review 123 --approve
```

Request changes:

```cli
gh pr review 123 --request-changes
```

### Merge PR

```cli
gh pr merge 123
```

### Check CI status

```cli
gh pr checks 123
```

### Overall PR status

```cli
gh pr status
```

![GitHub CLI `gh pr status` example](https://i0.wp.com/user-images.githubusercontent.com/10404068/74261502-34ae1380-4cb0-11ea-8baf-cf8248f1b222.png?ssl=1)

**What this image shows:** GitHub CLI displaying pull-request status in the terminal.

**What matters:** `gh` can query GitHub for PR review/check state that ordinary `git` commands do not know about.

**What to verify:** Confirm the PR branch, review state, and GitHub Actions/check status before merging.

---

## 3. `gh issue` — Issues

Issues are GitHub objects, not Git objects.

### List issues

```cli
gh issue list
```

Assigned to you:

```cli
gh issue list --assignee "@me"
```

### View issue

```cli
gh issue view 42
```

### Create issue

```cli
gh issue create
```

Noninteractive example:

```cli
gh issue create \
  --title "Interface validation fails" \
  --body "Describe the problem here."
```

### Close issue

```cli
gh issue close 42
```

---

## 4. `gh workflow` and `gh run` — GitHub Actions

GitHub Actions is a GitHub platform feature.

### List workflows

```cli
gh workflow list
```

### View workflow

```cli
gh workflow view
```

### Run a workflow manually

```cli
gh workflow run WORKFLOW_NAME
```

Example:

```cli
gh workflow run deploy.yml
```

### View recent runs

```cli
gh run list
```

### Inspect a run

```cli
gh run view RUN_ID
```

### Watch a running workflow

```cli
gh run watch RUN_ID
```

### View failed logs

```cli
gh run view RUN_ID --log-failed
```

This is extremely useful for CI/CD troubleshooting.

---

## 5. `gh release` — GitHub Releases

Git tags are a Git concept; GitHub Releases are a GitHub concept layered on top of tags.

### List releases

```cli
gh release list
```

### Create a release

```cli
gh release create v1.0.0
```

Example:

```cli
gh release create v1.0.0 \
  --title "Version 1.0.0" \
  --notes "Initial production release."
```

### Download release assets

```cli
gh release download v1.0.0
```

---

## 6. `gh project` — GitHub Projects

Use this for GitHub Projects.

Examples:

```cli
gh project list
gh project view 1 --owner OWNER
gh project create --owner OWNER --title "Network Automation"
gh project item-list 1 --owner OWNER
```

GitHub Projects are not represented by Git commands.

---

## 7. `gh search` — Search GitHub

Search issues:

```cli
gh search issues "BGP automation"
```

Search pull requests:

```cli
gh search prs "network automation"
```

Search repositories:

```cli
gh search repos ansible-network
```

Search code:

```cli
gh search code "neighbor fall-over bfd"
```

---

## 8. `gh api` — Direct GitHub API Access

One of the most powerful `gh` commands is:

```cli
gh api
```

It makes authenticated requests to GitHub's REST or GraphQL APIs.

Example:

```cli
gh api repos/OWNER/REPO
```

Get branches:

```cli
gh api repos/OWNER/REPO/branches
```

You can use it in shell scripts when no dedicated `gh` subcommand provides exactly what you need.

Conceptually:

```text
gh repo / gh pr / gh issue
        |
        | high-level commands
        v
   GitHub APIs

gh api
        |
        | direct API access
        v
   GitHub REST / GraphQL
```

---

## 9. `gh secret` and `gh variable`

Useful for GitHub Actions configuration.

### Secrets

```cli
gh secret list
gh secret set API_TOKEN
```

Repository secret:

```cli
gh secret set API_TOKEN --body "VALUE"
```

### Variables

```cli
gh variable list
gh variable set ENVIRONMENT --body "production"
```

Remember the conceptual difference:

- **Secrets** are intended for sensitive values.
- **Variables** are for non-sensitive configuration.

---

## 10. `gh ruleset`

GitHub CLI supports repository rulesets.

Examples include:

```cli
gh ruleset list
gh ruleset view
```

Rulesets can enforce repository governance, such as branch/tag protections.

---

## 11. `gh codespace`

For GitHub Codespaces:

```cli
gh codespace list
gh codespace create
gh codespace ssh
gh codespace code
```

This is another GitHub service that has no direct equivalent in Git.

---

# Side-by-Side Workflow

Suppose you want to fix a bug and submit a pull request.

## Step 1 — Clone

Either:

```cli
git clone https://github.com/example/network-automation.git
```

or:

```cli
gh repo clone example/network-automation
```

## Step 2 — Create branch

```cli
git switch -c fix-bgp-validation
```

## Step 3 — Edit files

```text
Make changes...
```

## Step 4 — Stage

```cli
git add .
```

## Step 5 — Commit

```cli
git commit -m "Fix BGP validation"
```

## Step 6 — Push branch

```cli
git push -u origin fix-bgp-validation
```

## Step 7 — Create PR

```cli
gh pr create --fill
```

## Step 8 — Check CI

```cli
gh pr checks
```

## Step 9 — Review PR information

```cli
gh pr view
```

## Step 10 — Merge

```cli
gh pr merge
```

This shows the clean separation:

```text
git
 |
 +-- edit history
 +-- commit
 +-- branch
 +-- push
 |
 v
GitHub
 |
 +-- pull request
 +-- review
 +-- checks
 +-- merge
        ^
        |
       gh
```

---

# `git` vs `gh` for GitHub Foundations

These distinctions are especially worth remembering.

| Question concept | Correct idea |
|---|---|
| Version control system | Git |
| Hosting/collaboration platform | GitHub |
| Stage changes | `git add` |
| Create snapshot | `git commit` |
| Send commits to remote | `git push` |
| Download remote changes | `git pull` / `git fetch` |
| Create pull request | `gh pr create` |
| List issues | `gh issue list` |
| Check Actions runs | `gh run list` |
| Trigger workflow | `gh workflow run` |
| Create GitHub repo | `gh repo create` |
| Call GitHub API | `gh api` |
| Log in to GitHub CLI | `gh auth login` |

---

# Commands That Look Similar but Are Not the Same

## Clone

```cli
git clone URL
```

versus:

```cli
gh repo clone OWNER/REPO
```

Both ultimately get a Git repository onto your machine.

`gh repo clone` is GitHub-aware and convenient when working specifically with GitHub.

---

## Branch Creation

Usually use Git:

```cli
git switch -c feature
```

Do not think of `gh` as a replacement for normal local Git branch work.

---

## Merge

Local branch merge:

```cli
git merge feature
```

GitHub pull-request merge:

```cli
gh pr merge 123
```

These are related but not identical actions.

---

## Status

Git working-tree status:

```cli
git status
```

Shows:

- modified files
- staged files
- untracked files
- current branch

GitHub PR status:

```cli
gh pr status
```

Shows GitHub pull-request information.

These two commands answer completely different questions.

---

# Important `gh` Help Commands

Show top-level commands:

```cli
gh
```

General help:

```cli
gh help
```

Command help:

```cli
gh pr --help
```

Subcommand help:

```cli
gh pr create --help
```

This is valuable in an exam or lab because the CLI itself can remind you of syntax.

---

# Authentication Relationship Between `gh` and `git`

After:

```cli
gh auth login
```

GitHub CLI can configure authentication that also makes HTTPS Git operations easier.

This means commands such as:

```cli
git push
git pull
```

may use credentials that were configured during GitHub CLI authentication.

However, the tools are still separate:

```text
gh auth login
     |
     +--> authenticate GitHub CLI
     |
     +--> optionally help configure Git credentials
```

---

# Common Mistakes

## Mistake 1: Thinking Git and GitHub are the same thing

They are not.

```text
Git     = version control
GitHub  = collaboration/hosting platform
gh      = CLI for GitHub
```

## Mistake 2: Trying to create a pull request with `git`

There is no standard:

```cli
git pull-request create
```

Use GitHub CLI:

```cli
gh pr create
```

## Mistake 3: Thinking `gh` replaces Git

You still normally use:

```cli
git add
git commit
git branch
git switch
git fetch
git push
```

`gh` complements Git rather than replacing it.

## Mistake 4: Confusing `git status` with `gh status`

```cli
git status
```

checks the local working tree.

```cli
gh status
```

shows GitHub-related activity and status.

## Mistake 5: Confusing `git pull` with a pull request

A **Git pull**:

```cli
git pull
```

downloads and integrates remote Git history.

A **pull request** is a GitHub collaboration object.

The similar wording causes frequent confusion.

---

# Exam Memory Aid

Remember this sentence:

> **Git manages commits. `gh` manages GitHub.**

Or:

```text
git = repository history
gh  = GitHub platform objects
```

A few command pairs worth memorizing:

```text
git status      -> local files
gh pr status    -> pull requests

git clone       -> clone any Git repo
gh repo clone   -> clone a GitHub repo

git merge       -> local Git branch merge
gh pr merge     -> merge GitHub PR

git log         -> commit history
gh run list     -> Actions history

git config      -> Git configuration
gh config       -> GitHub CLI configuration
```

---

# Quick Reference

```cli
# Authentication
gh auth login
gh auth status

# Repositories
gh repo create
gh repo clone OWNER/REPO
gh repo list
gh repo view
gh repo fork OWNER/REPO

# Pull requests
gh pr create
gh pr list
gh pr view
gh pr checkout 123
gh pr checks
gh pr review
gh pr merge
gh pr status

# Issues
gh issue create
gh issue list
gh issue view 123
gh issue close 123

# Actions
gh workflow list
gh workflow view
gh workflow run WORKFLOW
gh run list
gh run view RUN_ID
gh run watch RUN_ID

# Releases
gh release list
gh release create TAG
gh release download TAG

# Projects
gh project list
gh project view

# Search
gh search repos QUERY
gh search issues QUERY
gh search prs QUERY
gh search code QUERY

# API
gh api ENDPOINT

# Secrets and variables
gh secret list
gh secret set NAME
gh variable list
gh variable set NAME

# Help
gh
gh help
gh pr --help
gh pr create --help
```

---

# Key Takeaways

1. `git` is the version control system.
2. `gh` is GitHub's command-line interface.
3. Use `git` for commits, branches, merges, history, fetch, pull, and push.
4. Use `gh` for GitHub pull requests, issues, repositories, Actions, releases, Projects, Codespaces, rulesets, secrets, and API calls.
5. `gh` does not replace Git; the two are designed to work together.
6. For GitHub Foundations, be especially careful about the distinction between `git pull` and a GitHub pull request.

## Sources

- https://cli.github.com/manual/
- https://cli.github.com/manual/gh
- https://cli.github.com/manual/gh_pr
- https://cli.github.com/manual/gh_repo
- https://cli.github.com/manual/gh_api
- https://docs.github.com/en/github-cli
- https://docs.github.com/en/github-cli/github-cli/quickstart
- https://docs.github.com/en/pull-requests/get-started/pull-request-quickstart
- https://github.blog/news-insights/product-news/supercharge-your-command-line-experience-github-cli-is-now-in-beta/

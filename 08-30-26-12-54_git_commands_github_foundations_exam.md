# Git Commands for the GitHub Foundations Exam

> **Purpose:** Exam-focused Git command study guide for GitHub Foundations.
>
> **Supporting sources:**
> - https://docs.github.com/en/get-started/git-basics/git-cheatsheet
> - https://docs.github.com/en/get-started/using-git/getting-changes-from-a-remote-repository
> - https://docs.github.com/en/get-started/git-basics/about-remote-repositories
> - https://docs.github.com/en/get-started/using-github/hello-world
> - https://git-scm.com/docs
> - https://git-scm.com/docs/git-fetch
> - https://git-scm.com/docs/git-pull
> - https://git-scm.com/docs/git-switch

## Overview

For GitHub Foundations, focus on the commands that support the normal GitHub workflow:

```text
clone/init -> branch -> edit -> add -> commit -> push -> pull request -> merge -> pull
```

The most important mental model is:

```text
Working directory --git add--> Staging area --git commit--> Local repository --git push--> GitHub
```

And for incoming changes:

```text
GitHub --git fetch--> remote-tracking refs --git merge/rebase--> local branch
```

`git pull` combines fetching with integration.

## Git versus GitHub

**Git** is the distributed version control system. **GitHub** is a collaboration and repository-hosting platform built around Git.

A Git commit is created locally:

```cli
git commit -m "Update README"
```

A pull request is a **GitHub feature**, not a core Git command. There is no standard `git pull-request` command. GitHub CLI uses `gh pr create`.

---

# 1. Version and help

```cli
git --version
git help
git help clone
git help commit
git clone --help
```

`git help <COMMAND>` opens documentation for a command.

---

# 2. Configuration

## View configuration

```cli
git config --list
git config --list --show-origin
```

## Configure identity

```cli
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

Your Git `user.name` does not have to equal your GitHub username.

## Configuration scopes

```cli
git config --system <KEY> <VALUE>
git config --global <KEY> <VALUE>
git config --local <KEY> <VALUE>
```

- `--system`: system-wide.
- `--global`: current user's repositories.
- `--local`: current repository; commonly stored in `.git/config`.

## Read individual values

```cli
git config user.name
git config user.email
```

## Default initial branch

```cli
git config --global init.defaultBranch main
```

---

# 3. Create or copy repositories

## `git init`

```cli
git init
```

Creates a new Git repository in the current directory.

```cli
git init my-project
```

creates a new repository in `my-project`.

## `git clone`

```cli
git clone https://github.com/OWNER/REPOSITORY.git
```

SSH:

```cli
git clone git@github.com:OWNER/REPOSITORY.git
```

Custom destination directory:

```cli
git clone https://github.com/OWNER/REPOSITORY.git local-name
```

A normal clone:

- creates a local repository;
- downloads commits and files;
- creates a remote called `origin`;
- creates remote-tracking references such as `origin/main`;
- checks out the default branch;
- normally sets that local branch to track its remote counterpart.

### Exam distinction

| Command | Meaning |
|---|---|
| `git init` | Create a new local repository |
| `git clone` | Copy an existing repository and history |

---

# 4. Repository state and history

## `git status`

```cli
git status
git status --short
```

Shows current branch, staged changes, unstaged changes, untracked files, conflicts, and often ahead/behind status.

## `git log`

```cli
git log
git log --oneline
git log --oneline --graph --decorate --all
git log -- README.md
```

## `git show`

```cli
git show
git show <COMMIT_SHA>
git show <TAG_NAME>
```

Shows a commit/tag and associated changes.

## `git diff`

Unstaged changes:

```cli
git diff
```

Staged changes:

```cli
git diff --staged
```

Equivalent common form:

```cli
git diff --cached
```

Compare commits or branches:

```cli
git diff <COMMIT1> <COMMIT2>
git diff main feature
```

**Exam trap:** `git diff` normally shows unstaged differences; use `git diff --staged` for changes already in the index.

---

# 5. Staging changes

The staging area is also called the **index**.

```cli
git add README.md
git add file1.txt file2.txt
git add .
git add -A
git add -p
```

`git add` stages content for the next commit. It does **not** create a commit.

---

# 6. Commits

```cli
git commit
git commit -m "Update README"
```

Automatically stage modifications/deletions to tracked files and commit:

```cli
git commit -am "Fix documentation"
```

**Important:** `-a` does not automatically include brand-new untracked files.

Amend the last commit:

```cli
git commit --amend
git commit --amend -m "Correct message"
```

Amending rewrites the most recent commit and changes its commit ID.

---

# 7. `HEAD`

`HEAD` represents the current checkout. Normally it points symbolically to the current branch.

```text
HEAD -> main -> commit C
```

Useful relative references:

```text
HEAD
HEAD~1
HEAD~2
```

`HEAD~1` means the first parent of the current commit.

---

# 8. Branches

List local branches:

```cli
git branch
```

List remote-tracking branches:

```cli
git branch -r
```

List both:

```cli
git branch -a
```

Create a branch without switching:

```cli
git branch feature-login
```

Switch branches:

```cli
git switch feature-login
```

Older syntax:

```cli
git checkout feature-login
```

Create and switch:

```cli
git switch -c feature-login
```

Older equivalent:

```cli
git checkout -b feature-login
```

Rename current branch:

```cli
git branch -m new-name
```

Rename another branch:

```cli
git branch -m old-name new-name
```

Delete a merged local branch:

```cli
git branch -d feature-login
```

Force local deletion:

```cli
git branch -D feature-login
```

Show tracking relationships:

```cli
git branch -vv
```

### High-value exam distinction

```cli
git branch feature
```

creates only.

```cli
git switch -c feature
```

creates **and** switches.

---

# 9. Merging

To merge `feature` into `main`:

```cli
git switch main
git merge feature
```

The branch you are currently on is the destination.

## Abort a conflicted merge

```cli
git merge --abort
```

## Continue after resolving conflicts

```cli
git add <RESOLVED_FILE>
git merge --continue
```

or complete the merge with a commit when appropriate.

Typical conflict markers look like:

```text
<<<<<<< HEAD
current branch version
=======
incoming version
>>>>>>> feature
```

---

# 10. Remotes

A remote is a named reference to another repository location.

List remotes:

```cli
git remote
git remote -v
```

Add a remote:

```cli
git remote add origin https://github.com/OWNER/REPOSITORY.git
```

Common fork setup:

```cli
git remote add upstream https://github.com/ORIGINAL_OWNER/REPOSITORY.git
```

Conventionally:

```text
origin   = your main remote / often your fork
upstream = original project
```

`origin` and `upstream` are conventions, not reserved magical names.

Inspect a remote:

```cli
git remote show origin
```

Change URL:

```cli
git remote set-url origin <NEW_URL>
```

Rename:

```cli
git remote rename origin old-origin
```

Remove:

```cli
git remote remove origin
```

---

# 11. Fetch

```cli
git fetch
git fetch origin
git fetch --all
git fetch --prune
```

`git fetch` downloads objects/refs and updates remote-tracking references such as `origin/main` **without directly integrating those changes into the checked-out local branch**.

Conceptually:

```text
Before fetch:
main        C
origin/main C
GitHub      C---D---E

After fetch:
main        C
origin/main E
```

Your local `main` is still at `C`.

---

# 12. Pull

```cli
git pull
git pull origin main
```

A useful exam model is:

```text
git pull = fetch + integrate
```

Pull with rebase:

```cli
git pull --rebase
```

Fast-forward only:

```cli
git pull --ff-only
```

### Fetch versus pull

| Command | Downloads | Updates remote-tracking refs | Integrates into current branch |
|---|---:|---:|---:|
| `git fetch` | Yes | Yes | No |
| `git pull` | Yes | Yes | Yes |

**Memory:** Fetch = download/inspect. Pull = download + integrate.

---

# 13. Push

```cli
git push
git push origin main
```

Push a new branch and set its upstream:

```cli
git push -u origin feature-login
```

Long form:

```cli
git push --set-upstream origin feature-login
```

Delete remote branch:

```cli
git push origin --delete feature-login
```

Push one tag:

```cli
git push origin v1.0.0
```

Push all tags:

```cli
git push origin --tags
```

### Local versus remote branch deletion

```cli
git branch -d feature
```

deletes the local branch.

```cli
git push origin --delete feature
```

deletes the remote branch.

---

# 14. Upstream/tracking branches

Set tracking while pushing:

```cli
git push -u origin main
```

Inspect:

```cli
git branch -vv
```

Set separately:

```cli
git branch --set-upstream-to=origin/main main
```

A local `main` and `origin/main` are different refs. `origin/main` represents your last fetched knowledge of the remote branch.

---

# 15. Standard GitHub feature-branch workflow

```cli
git clone https://github.com/OWNER/REPOSITORY.git
cd REPOSITORY

git switch -c feature-login

# edit files

git status
git diff
git add .
git diff --staged
git commit -m "Add login feature"
git push -u origin feature-login
```

Then on GitHub:

1. Open a pull request.
2. Review changes.
3. Run/check required status checks.
4. Obtain approvals if required.
5. Merge using an allowed method.
6. Optionally delete the feature branch.

Then locally:

```cli
git switch main
git pull
git branch -d feature-login
```

---

# 16. Fork workflow

A **fork** is a GitHub-side copy of another repository. Core Git does not have `git fork`.

Common setup:

```cli
git clone https://github.com/YOUR_ACCOUNT/PROJECT.git
cd PROJECT
git remote add upstream https://github.com/ORIGINAL_OWNER/PROJECT.git
git remote -v
```

Synchronize:

```cli
git fetch upstream
git switch main
git merge upstream/main
git push origin main
```

A project may prefer rebase instead:

```cli
git rebase upstream/main
```

---

# 17. Restore and unstage

Discard unstaged changes to a file:

```cli
git restore README.md
```

Unstage a file while keeping its working-tree edit:

```cli
git restore --staged README.md
```

Older common equivalent:

```cli
git reset HEAD README.md
```

Restore from another commit:

```cli
git restore --source=<COMMIT> README.md
```

### Exam distinction

- `git restore <FILE>`: working-tree content.
- `git restore --staged <FILE>`: staging area/index.

---

# 18. Reset

## Soft

```cli
git reset --soft HEAD~1
```

Moves the branch back but keeps changes staged.

## Mixed (default)

```cli
git reset HEAD~1
```

or:

```cli
git reset --mixed HEAD~1
```

Moves the branch and unstages changes, but leaves them in the working tree.

## Hard

```cli
git reset --hard HEAD~1
```

Moves the branch and resets index and working tree. **Potentially destructive.**

| Mode | Move branch | Reset index | Reset working tree |
|---|---:|---:|---:|
| `--soft` | Yes | No | No |
| `--mixed` | Yes | Yes | No |
| `--hard` | Yes | Yes | Yes |

---

# 19. Revert

```cli
git revert <COMMIT_SHA>
```

Creates a new commit that reverses an earlier commit.

### Revert versus reset

| Command | Behavior | Rewrites visible history? | Shared-history suitability |
|---|---|---:|---:|
| `git revert` | Adds inverse commit | No | Usually safer |
| `git reset` | Moves branch reference | Can | Use carefully |

For a bad commit that has already been shared, `revert` is typically safer because it preserves history.

---

# 20. Remove and move files

Remove a tracked file and stage deletion:

```cli
git rm old-file.txt
```

Stop tracking but keep local file:

```cli
git rm --cached secret-config.txt
```

Rename/move:

```cli
git mv old-name.txt new-name.txt
```

**Exam trap:** adding a path to `.gitignore` does not automatically untrack a file that Git already tracks.

---

# 21. `.gitignore`

Example:

```gitignore
*.log
.env
node_modules/
build/
```

Check why a path is ignored:

```cli
git check-ignore -v <PATH>
```

`.gitignore` is a file, not a command.

---

# 22. Stash

```cli
git stash
git stash push -m "Work in progress"
git stash list
git stash apply
git stash pop
git stash drop
git stash clear
```

| Command | Reapply changes | Keep stash entry |
|---|---:|---:|
| `git stash apply` | Yes | Yes |
| `git stash pop` | Yes | Normally no after successful application |

---

# 23. Tags

List:

```cli
git tag
```

Lightweight:

```cli
git tag v1.0.0
```

Annotated:

```cli
git tag -a v1.0.0 -m "Release v1.0.0"
```

Specific commit:

```cli
git tag v1.0.0 <COMMIT_SHA>
```

Push:

```cli
git push origin v1.0.0
git push origin --tags
```

Delete local:

```cli
git tag -d v1.0.0
```

Delete remote:

```cli
git push origin --delete v1.0.0
```

Tags identify specific points in history, commonly releases. A tag is not a branch.

---

# 24. Rebase

```cli
git switch feature
git rebase main
```

Rebase replays commits onto a new base, creating new commit IDs for replayed commits.

Continue after conflict resolution:

```cli
git add <RESOLVED_FILE>
git rebase --continue
```

Abort:

```cli
git rebase --abort
```

Interactive:

```cli
git rebase -i HEAD~3
```

Interactive rebase can reorder, squash, reword, edit, or drop commits.

**Exam concept:** rebase rewrites the commits it replays, so avoid casually rebasing shared public history.

---

# 25. Cherry-pick

Apply one selected commit onto the current branch:

```cli
git cherry-pick <COMMIT_SHA>
```

Abort:

```cli
git cherry-pick --abort
```

Continue:

```cli
git cherry-pick --continue
```

Cherry-pick is useful when you want a specific commit rather than merging an entire branch.

---

# 26. Investigation commands

```cli
git blame README.md
git grep "authentication"
git rev-parse HEAD
git rev-parse --show-toplevel
```

- `git blame`: shows the commit/author associated with lines of a file.
- `git grep`: searches tracked content.
- `git rev-parse HEAD`: resolves `HEAD` to an object ID.
- `git rev-parse --show-toplevel`: shows repository root.

---

# 27. Clean untracked files

Preview:

```cli
git clean -n
```

Delete untracked files:

```cli
git clean -f
```

Include untracked directories:

```cli
git clean -fd
```

Use carefully.

---

# 28. Prune stale remote-tracking branches

```cli
git fetch --prune
```

or:

```cli
git remote prune origin
```

Useful when a branch was deleted on GitHub but an old `origin/branch` ref remains locally.

---

# 29. Detached HEAD

```cli
git switch --detach <COMMIT_SHA>
```

Older syntax:

```cli
git checkout <COMMIT_SHA>
```

In detached HEAD, `HEAD` points directly to a commit instead of a local branch.

Preserve new work by creating a branch:

```cli
git switch -c saved-work
```

---

# 30. Force push

```cli
git push --force
git push --force-with-lease
```

`--force-with-lease` adds safety checks compared with unconditional `--force`.

GitHub branch protection/rules may prohibit force pushes even though Git supports the command.

---

# 31. GitHub authentication concepts

Common remote formats:

HTTPS:

```text
https://github.com/OWNER/REPOSITORY.git
```

SSH:

```text
git@github.com:OWNER/REPOSITORY.git
```

Inspect configured URLs:

```cli
git remote -v
```

GitHub does not use normal account passwords for HTTPS Git authentication. Supported approaches include personal access tokens, credential helpers such as Git Credential Manager, SSH keys, and GitHub CLI authentication.

---

# 32. GitHub CLI commands worth recognizing

These are **not core Git commands**:

```cli
gh auth login
gh repo clone OWNER/REPOSITORY
gh repo fork
gh pr create
gh pr list
gh pr view
gh pr checkout <PR_NUMBER>
gh pr merge
gh issue list
```

High-value distinction:

```cli
git push
```

publishes Git refs/commits.

```cli
gh pr create
```

creates a GitHub pull request.

---

# 33. Plausible commands that do not exist in core Git

Watch for distractors such as:

```text
git pull-request
git fork
git issue
git discussion
git actions
git protect-branch
```

Forks, pull requests, Issues, Discussions, Actions, rulesets, and branch protection are GitHub platform concepts rather than core Git command families.

---

# 34. GitHub pull-request merge methods

GitHub repositories may allow:

- **Merge commit** — preserves commits and adds a merge commit when required.
- **Squash and merge** — combines the pull request changes into one commit on the target branch.
- **Rebase and merge** — replays pull request commits onto the target branch without a merge commit.

Repository administrators can control which merge methods are enabled.

---

# 35. Common command sequences

## New local repository to GitHub

```cli
mkdir project
cd project
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/OWNER/REPOSITORY.git
git push -u origin main
```

The remote must exist and your authentication/permissions must allow the push.

## Clone and develop a feature

```cli
git clone https://github.com/OWNER/REPOSITORY.git
cd REPOSITORY
git switch -c feature
# edit
git add .
git commit -m "Add feature"
git push -u origin feature
```

## Update local main

```cli
git switch main
git pull
```

More controlled version:

```cli
git fetch origin
git log --oneline main..origin/main
git merge origin/main
```

## Bring main into a feature using merge

```cli
git fetch origin
git switch feature
git merge origin/main
```

## Bring main into feature using rebase

```cli
git fetch origin
git switch feature
git rebase origin/main
```

The rebase version rewrites the feature commits.

---

# 36. High-value comparisons

## Clone vs pull

| `git clone` | `git pull` |
|---|---|
| Initial local copy | Update existing local repository |
| Creates local repository | Works inside existing repository |
| Usually creates `origin` | Uses configured remote/upstream |

## Add vs commit vs push

| Command | Scope | Purpose |
|---|---|---|
| `git add` | Local | Stage changes |
| `git commit` | Local | Save staged snapshot into local history |
| `git push` | Remote interaction | Publish commits/refs to remote |

## Branch vs switch

| Command | Purpose |
|---|---|
| `git branch feature` | Create branch only |
| `git switch feature` | Switch to existing branch |
| `git switch -c feature` | Create and switch |

## Merge vs rebase

| Merge | Rebase |
|---|---|
| Combines histories | Replays commits onto another base |
| May create merge commit | Replayed commits receive new IDs |
| Preserves topology | Often creates linear-looking history |

## Reset vs revert

| Reset | Revert |
|---|---|
| Moves branch/reference | Adds inverse commit |
| Can rewrite visible branch history | Preserves existing commits |
| Commonly local/history editing | Usually safer for shared history |

---

# 37. High-value exam scenarios

### Check whether GitHub has new changes without merging them

```cli
git fetch
```

Then inspect:

```cli
git status
git log --oneline HEAD..origin/main
```

### Update current branch from its upstream

```cli
git pull
```

### Discard an unstaged file edit

```cli
git restore <FILE>
```

### Unstage a file without deleting its edit

```cli
git restore --staged <FILE>
```

### Undo a shared commit while preserving history

```cli
git revert <COMMIT>
```

### Create and enter a feature branch

```cli
git switch -c feature
```

### Publish a branch and establish tracking

```cli
git push -u origin feature
```

### Delete merged local branch

```cli
git branch -d feature
```

### Delete remote branch

```cli
git push origin --delete feature
```

### Remove stale remote-tracking branches

```cli
git fetch --prune
```

---

# 38. One-page cheat sheet

```cli
# Help / config
git --version
git help <COMMAND>
git config --list
git config --global user.name "Your Name"
git config --global user.email "you@example.com"

# Create / copy
git init
git clone <URL>

# State / history
git status
git status --short
git log
git log --oneline
git log --oneline --graph --decorate --all
git show <COMMIT>

# Differences
git diff
git diff --staged
git diff <COMMIT1> <COMMIT2>

# Stage / commit
git add <FILE>
git add .
git add -A
git commit -m "message"
git commit -am "message"
git commit --amend

# Branch
git branch
git branch -r
git branch -a
git branch <NAME>
git switch <NAME>
git switch -c <NAME>
git checkout <NAME>
git checkout -b <NAME>
git branch -m <NEW_NAME>
git branch -d <NAME>
git branch -D <NAME>
git branch -vv

# Merge
git merge <BRANCH>
git merge --abort
git merge --continue

# Remotes
git remote
git remote -v
git remote add <NAME> <URL>
git remote show <NAME>
git remote set-url <NAME> <URL>
git remote rename <OLD> <NEW>
git remote remove <NAME>

# Fetch / pull
git fetch
git fetch <REMOTE>
git fetch --all
git fetch --prune
git pull
git pull <REMOTE> <BRANCH>
git pull --rebase
git pull --ff-only

# Push
git push
git push <REMOTE> <BRANCH>
git push -u <REMOTE> <BRANCH>
git push <REMOTE> --delete <BRANCH>
git push <REMOTE> --tags

# Restore / undo
git restore <FILE>
git restore --staged <FILE>
git reset --soft HEAD~1
git reset HEAD~1
git reset --hard HEAD~1
git revert <COMMIT>

# Files
git rm <FILE>
git rm --cached <FILE>
git mv <OLD> <NEW>

# Stash
git stash
git stash push -m "message"
git stash list
git stash apply
git stash pop
git stash drop
git stash clear

# Tags
git tag
git tag <TAG>
git tag -a <TAG> -m "message"
git push origin <TAG>
git push origin --tags
git tag -d <TAG>

# Rebase / cherry-pick
git rebase <BRANCH>
git rebase --abort
git rebase --continue
git rebase -i HEAD~3
git cherry-pick <COMMIT>
git cherry-pick --abort
git cherry-pick --continue

# Investigation
git blame <FILE>
git grep "<TEXT>"
git rev-parse HEAD

# Cleanup
git clean -n
git clean -f
git clean -fd
git remote prune origin
```

---

# 39. Commands to memorize first

If you are short on study time, prioritize:

```cli
git init
git clone <URL>
git status
git diff
git add .
git commit -m "message"
git log --oneline

git branch
git switch <BRANCH>
git switch -c <BRANCH>
git merge <BRANCH>

git remote -v
git remote add origin <URL>

git fetch
git pull
git push
git push -u origin <BRANCH>

git restore <FILE>
git restore --staged <FILE>
git revert <COMMIT>

git branch -d <BRANCH>
git push origin --delete <BRANCH>

git stash
git stash pop

git tag
git push origin --tags
```

---

# 40. Exam traps to memorize

1. Git is not GitHub.
2. `git clone` is normally used for the initial local copy.
3. `git fetch` downloads remote changes without directly integrating them into the checked-out local branch.
4. `git pull` fetches and integrates.
5. `git add` stages; it does not commit.
6. `git commit` is local; `git push` publishes to a remote.
7. `origin` is a conventional remote name, not a GitHub keyword.
8. Local `main` and remote-tracking `origin/main` are different refs.
9. `git branch feature` creates but does not switch.
10. `git switch -c feature` creates and switches.
11. `git branch -d` deletes locally.
12. `git push origin --delete feature` deletes remotely.
13. `.gitignore` does not automatically untrack already tracked files.
14. `git restore --staged` unstages while preserving the working-tree edit.
15. `git revert` creates a new commit that reverses another commit.
16. `git reset --hard` can destroy uncommitted work.
17. Rebase rewrites replayed commits.
18. A fork is a GitHub concept; there is no normal `git fork` command.
19. A pull request is a GitHub concept; there is no normal `git pull-request` command.
20. GitHub repository rules/branch protection can reject a push that core Git syntax would otherwise permit.
21. Tags are not branches.
22. `git stash apply` keeps the stash entry; `git stash pop` normally removes it after successful application.
23. `git commit -am` does not add new untracked files.
24. HTTPS and SSH are common GitHub remote URL methods.
25. GitHub HTTPS Git authentication does not use your ordinary account password.

---

# 41. Visual: branching workflow

![Git branching and tagging workflow](https://help.qlik.com/talend/en-US/software-dev-lifecycle-best-practices-guide/7.3/Content/Resources/images/archi-git.png)

**What this image shows:** A representative branching workflow with mainline, development, feature, release, merge, and tag concepts.

**What matters:** Branches permit parallel lines of development; merge operations combine history; tags mark specific points such as releases.

**What to verify:** Do not assume every repository uses this exact Git Flow-style topology. For Foundations, understand the underlying branch/commit/merge/tag concepts and GitHub Flow.

Source page: https://help.qlik.com/talend/r/en-US/7.3/software-dev-lifecycle-best-practices-guide/scm-concepts

---

# 42. Final memory model

```text
EDIT
 |
 v
git status
 |
 v
git diff
 |
 v
git add
 |
 v
git diff --staged
 |
 v
git commit
 |
 v
git push
 |
 v
GitHub pull request
 |
 v
review + checks
 |
 v
merge
 |
 v
git switch main
 |
 v
git pull
```

Synchronization rule:

```text
FETCH = download remote information without integrating into current branch
PULL  = fetch + integrate
PUSH  = publish local refs/commits to a remote
```

Undo rule:

```text
restore = restore working-tree/index content
reset   = move/reset local references/state
revert  = add a new commit that reverses an earlier commit
```

## Key takeaways

- Learn the workflow **clone -> branch -> edit -> add -> commit -> push -> pull request -> merge -> pull**.
- The most important command distinction is **fetch vs pull**, followed by **add vs commit vs push**.
- Understand **local branches versus remote-tracking branches**.
- Know that **forks and pull requests are GitHub features**, not native Git commands.
- Prefer `revert` for history-preserving undo of a shared commit.
- Treat `reset --hard`, rebase, and force-push operations with care.
- GitHub repository rules can restrict operations that Git itself supports.

## Sources

- GitHub Docs — Git cheat sheet: https://docs.github.com/en/get-started/git-basics/git-cheatsheet
- GitHub Docs — Getting changes from a remote repository: https://docs.github.com/en/get-started/using-git/getting-changes-from-a-remote-repository
- GitHub Docs — About remote repositories: https://docs.github.com/en/get-started/git-basics/about-remote-repositories
- GitHub Docs — Hello World: https://docs.github.com/en/get-started/using-github/hello-world
- GitHub Docs — Using Git: https://docs.github.com/en/get-started/using-git
- Git reference: https://git-scm.com/docs
- Git user manual: https://git-scm.com/docs/user-manual
- `git fetch`: https://git-scm.com/docs/git-fetch
- `git pull`: https://git-scm.com/docs/git-pull
- `git switch`: https://git-scm.com/docs/git-switch
- Branching workflow image source: https://help.qlik.com/talend/r/en-US/7.3/software-dev-lifecycle-best-practices-guide/scm-concepts

# InnerSource Development Terminology Study Guide

> **Primary sources**
> - https://innersourcecommons.org/learn/learning-path/introduction/01/
> - https://innersourcecommons.org/learn/learning-path/introduction/05/
> - https://patterns.innersourcecommons.org/
> - https://github.com/resources/articles/innersource
> - https://github.com/InnerSourceCommons/InnerSourcePatterns

## Overview

**InnerSource** is the application of open-source development practices and principles to software that remains **private to an organization**. The code is not necessarily public, but teams inside the company are encouraged to discover, use, improve, and contribute to software owned by other teams.

A useful shorthand is:

> **Open source collaboration model + private company boundary = InnerSource**

InnerSource is not simply "putting all code in GitHub" and it is not outsourcing work to another internal team. It is a collaboration model built around discoverability, transparency, documented contribution processes, review, mentorship, and voluntary cross-team contributions.

## Why the term matters

Traditional enterprise software development often creates **team silos**:

- Team A owns application A.
- Team B needs a feature from application A.
- Team B opens a ticket and waits for Team A.
- Team A may have other priorities.

With InnerSource, Team B may be allowed to implement the feature itself and submit the change back to Team A for review. Team A remains the owner and maintainer of the project, but the organization gains a scalable way to share engineering effort.

## InnerSource compared with other development models

| Model | Who can see the source? | Who can contribute? | Typical ownership |
|---|---|---|---|
| Traditional closed source | Usually only the owning team or restricted groups | Primarily the owning team | One team or business unit |
| InnerSource | Broadly visible inside the organization, subject to permissions | Other internal teams can contribute | Host/core team retains stewardship |
| Open source | Publicly visible | Potentially anyone | Community/project maintainers |

## Core InnerSource terminology

### Host Team

The **host team** is the team that owns or stewards an InnerSource project.

The host team typically:

- Maintains the repository.
- Defines architecture and coding standards.
- Reviews pull requests.
- Publishes contribution guidelines.
- Maintains CI/CD pipelines.
- Handles releases.
- Mentors contributors.
- Decides whether a contribution fits the project.

The host team does **not** lose ownership merely because other teams can contribute.

### Guest Team

A **guest team** is another internal team that uses the host team's project and may want to contribute changes.

Example:

- Network Automation team owns a Python library for pushing Cisco configurations.
- Security Engineering needs Palo Alto support.
- Security Engineering becomes a guest team and contributes the feature instead of waiting for the Network Automation team to build it.

### Contributor

A **contributor** is an individual who submits improvements to an InnerSource project.

Contributions may include:

- Source code
- Tests
- Documentation
- Bug fixes
- Automation
- CI/CD improvements
- Feature proposals

InnerSource Commons emphasizes that collaboration should eventually reach the **code contribution level**, not stop at tickets and requirements.

### Trusted Committer

A **trusted committer** is a contributor who has demonstrated enough knowledge, quality, and sustained participation to receive additional trust and responsibility.

Depending on the organization's model, a trusted committer may:

- Review pull requests.
- Mentor new contributors.
- Help triage issues.
- Participate in design decisions.
- Merge approved changes.

This is similar to maintainer or committer roles in large open-source projects.

### Maintainer

A **maintainer** is responsible for the ongoing health of a project.

Typical responsibilities include:

- Reviewing contributions.
- Keeping dependencies current.
- Managing releases.
- Enforcing standards.
- Maintaining backward compatibility where required.
- Responding to defects.

A maintainer may be part of the host team, core team, or trusted-committer group.

### Core Team

The **core team** is the group responsible for the fundamental health and direction of an InnerSource project.

It commonly owns:

- Architecture
- Versioning
- CI/CD
- Automated testing
- Release management
- Contribution review
- Long-term roadmap

The project can accept contributions broadly while the core team protects overall coherence.

![InnerSource core team model](https://raw.githubusercontent.com/InnerSourceCommons/InnerSourcePatterns/main/assets/img/core-team.png)

**What this image shows:** The InnerSource Commons core-team model illustrates how a dedicated core team provides the project foundation while contributors from other teams add features.

**What matters:** Broad contribution does not eliminate ownership. The core team continues to provide engineering foundations such as modularization, versioning, CI/CD, and automated testing.

**What to verify:** Confirm the project has an identifiable core/host team and that contributors know who reviews changes and maintains the shared foundation.

### Contribution

A **contribution** is a proposed change made by someone outside the project's normal owning team.

In a GitHub workflow, this commonly looks like:

```text
Contributor -> branch/fork -> commit -> pull request -> review -> CI checks -> merge
```

### Pull Request (PR)

A **pull request** is the review boundary through which a contributor proposes a change.

![Branch, commit, pull, and review contribution flow](https://raw.githubusercontent.com/InnerSourceCommons/InnerSourcePatterns/main/assets/img/branchCommitPullReview.png)

**What this image shows:** A contribution-oriented source-control workflow built around branching, committing, proposing a pull request, and review.

**What matters:** The pull request is the controlled interface between a guest contributor and the host team.

**What to verify:** Ensure branch/repository rules require the appropriate review and automated checks before merge.

In an InnerSource project, PRs are especially important because they provide:

- A visible audit trail.
- Peer review.
- Automated testing.
- Security checks.
- Design discussion.
- Approval gates.
- A searchable record of why a change was made.

### Code Review

**Code review** is the process of evaluating a proposed change before it is merged.

Review may check:

- Correctness
- Security
- Style
- Architecture
- Test coverage
- Backward compatibility
- Documentation
- Operational impact

InnerSource relies heavily on review because contribution access is broader than in a traditional siloed team.

### Repository

The **repository** is the shared source-control location containing code, history, documentation, issues, workflows, and contribution instructions.

An InnerSource-ready repository should generally be easy for internal developers to discover and understand.

### README.md

The **README** explains what a project is, why it exists, how to use it, and how to get started.

For InnerSource, a good README reduces the amount of direct assistance the host team must provide.

### CONTRIBUTING.md

`CONTRIBUTING.md` explains **how someone should contribute**.

Typical contents include:

- Development environment setup.
- Branching requirements.
- Coding standards.
- Testing expectations.
- Pull-request process.
- Required approvals.
- Commit-message standards.
- Contact/escalation paths.

This is one of the most important InnerSource documents.

### CODEOWNERS

On GitHub, `CODEOWNERS` maps files or directories to people or teams responsible for review.

Example:

```text
/network/        @network-automation
/security/       @security-engineering
/.github/        @platform-engineering
```

When combined with branch protection or repository rules, CODEOWNERS can require the appropriate maintainers to review changes before merge.

### Issue Tracker

An **issue tracker** records work such as bugs, features, design discussions, tasks, and technical debt.

In InnerSource, the issue tracker should be transparent enough that potential contributors can understand:

- What work is needed.
- What is already being worked on.
- Why decisions were made.
- Where help is wanted.

### RFC (Request for Comments)

An **RFC** is a written design proposal circulated for discussion before implementation.

An InnerSource RFC process is useful when a proposed change affects multiple teams or requires architectural agreement.

Typical flow:

```text
Problem -> RFC -> discussion -> decision -> implementation -> pull request
```

### InnerSource Portal

An **InnerSource portal** is an internal catalog or website used to help developers discover reusable internal projects.

It may index:

- Repository name
- Owner
- Description
- Programming language
- Documentation
- Contribution readiness
- Support channel
- Activity level
- Open issues

The goal is to prevent teams from rebuilding functionality that already exists elsewhere in the organization.

### Discoverability

**Discoverability** means developers can find existing projects before creating new ones.

Poor discoverability leads to:

- Duplicate tools.
- Duplicate libraries.
- Different teams solving the same problem independently.
- Increased maintenance cost.

### Transparency

**Transparency** means project plans, progress, decisions, issues, and contribution processes are visible to potential internal contributors.

Transparency does not mean abandoning access control. Sensitive repositories can still be restricted.

### Self-Service

**Self-service** means a new contributor can understand and use the project without repeatedly asking the host team for basic information.

A self-service repository usually provides:

- README
- CONTRIBUTING guide
- Build instructions
- Test instructions
- Examples
- Architecture documentation
- Issue templates
- Pull-request template

### Open Collaboration

**Open collaboration** means teams cooperate through visible, reusable processes rather than relying entirely on private messages, meetings, or handoffs.

Inside an enterprise, "open" normally means open **within an authorized internal boundary**, not public on the Internet.

## The four InnerSource principles

InnerSource Commons identifies four foundational principles.

### 1. Openness

Projects should be sufficiently discoverable and documented so that internal developers can understand how to use and contribute to them.

### 2. Transparency

Potential contributors should be able to understand project direction, outstanding work, progress, and important decisions.

### 3. Prioritized Mentorship

Host-team members should actively help contributors become effective rather than treating external contributors as interruptions.

### 4. Voluntary Code Contribution

Both sides opt in:

- The guest team chooses to contribute.
- The host team chooses whether to accept the contribution.

The host team is not obligated to merge every pull request.

## Typical InnerSource workflow

```mermaid
flowchart LR
    A[Guest team needs a feature] --> B[Search internal repositories]
    B --> C[Find an InnerSource project]
    C --> D[Read README and CONTRIBUTING]
    D --> E[Open or claim an issue]
    E --> F[Create branch and implement change]
    F --> G[Run local tests]
    G --> H[Open pull request]
    H --> I[CI security and test checks]
    I --> J[Host team code review]
    J -->|Changes requested| F
    J -->|Approved| K[Merge]
    K --> L[Release or deployment]
```

### What this diagram shows

It shows how a team that does not own a project can still solve its own requirement while preserving review and governance by the host team.

### What matters

The important distinction is that the guest team can **contribute directly** instead of merely filing a ticket and waiting.

### What to verify

Before calling a project InnerSource-ready, verify that a contributor can discover it, understand how to build/test it, submit a change, receive review, and see the contribution through to merge.

## GitHub terminology mapped to InnerSource

| GitHub concept | InnerSource purpose |
|---|---|
| Organization / Enterprise | Defines the internal collaboration boundary |
| Repository | Shared project location |
| Internal/private visibility | Controls who inside the enterprise can see the code |
| Issues | Tracks work and discussions |
| Branches | Isolates proposed work |
| Pull requests | Formal contribution and review mechanism |
| CODEOWNERS | Routes changes to responsible maintainers |
| Repository rules / branch protection | Enforces required reviews and checks |
| GitHub Actions | Automates testing, linting, security, releases, and deployment |
| Discussions | Enables broader design/community conversations |
| Dependabot | Helps maintain dependencies and security posture |

## Example: network automation InnerSource model

Suppose a company has a central repository:

```text
network-automation/
├── cisco/
├── fortinet/
├── paloalto/
├── templates/
├── tests/
├── .github/workflows/
├── README.md
├── CONTRIBUTING.md
└── CODEOWNERS
```

The Network Automation team is the **host team**.

A firewall engineer discovers that Palo Alto support is missing.

Rather than opening a request and waiting several months, the firewall engineer:

1. Reads `CONTRIBUTING.md`.
2. Opens an issue proposing Palo Alto support.
3. Creates a branch.
4. Adds the new module.
5. Adds tests.
6. Opens a pull request.
7. GitHub Actions validates the change.
8. Network Automation maintainers review it.
9. The contribution is merged.

That is a practical example of InnerSource.

## What InnerSource is not

InnerSource is **not** simply:

- Giving everyone write access to every repository.
- Making all company repositories public.
- Eliminating code review.
- Removing ownership.
- Asking another department to do your team's work.
- Copying code between repositories without collaboration.
- Creating a shared Git repository with no documentation or governance.

A repository can be visible company-wide and still **not** be a meaningful InnerSource project if nobody outside the owning team can realistically contribute.

## Governance and security

InnerSource does not require weak controls. A mature implementation typically uses controls such as:

- Least-privilege repository permissions.
- Protected branches or repository rules.
- Required pull-request review.
- CODEOWNERS review.
- Automated tests.
- Secret scanning.
- Dependency scanning.
- Static analysis.
- Signed commits or provenance requirements where appropriate.
- Controlled deployment environments.

The principle is **open collaboration within the appropriate security boundary**, not unrestricted access.

## Common mistakes

### Mistake: "Everyone can read it, so it is InnerSource"

Visibility alone is insufficient. Contributors need a documented and supported path to make changes.

### Mistake: No contribution guide

Without `CONTRIBUTING.md`, guest contributors must repeatedly ask the host team how to work with the project.

### Mistake: Host team ignores external PRs

If outside contributions sit unreviewed, developers will stop contributing.

### Mistake: No clear ownership

InnerSource broadens contribution, but stewardship still needs to be explicit.

### Mistake: Treating contributors as free labor

InnerSource works best when the contribution solves a real need for the contributing team and also benefits the shared project.

### Mistake: Too much synchronous communication

If design decisions happen only in private meetings or chat, future contributors cannot understand the history. Issues, PRs, ADRs, or RFCs should preserve important context.

## Verification checklist for an InnerSource-ready repository

- [ ] Repository is discoverable by its intended internal audience.
- [ ] README explains purpose and usage.
- [ ] CONTRIBUTING explains the contribution workflow.
- [ ] Ownership is documented.
- [ ] Issues are visible and usable by guest contributors.
- [ ] Contributors can create a branch/fork and submit a PR.
- [ ] Automated tests run on proposed changes.
- [ ] Required security checks run before merge.
- [ ] Review responsibilities are clear.
- [ ] Maintainers respond to contributions in a reasonable time.
- [ ] Decisions are documented in searchable systems.
- [ ] Release/versioning process is documented.

## Quick memory aid

Think of InnerSource as:

> **"Open-source behavior, enterprise-private code."**

And remember the main actors:

```text
Host Team  -> owns and maintains the project
Guest Team -> needs something from the project
Contributor -> submits the change
Trusted Committer -> experienced contributor with elevated trust
Maintainer/Core Team -> protects project quality and direction
PR -> contribution and review mechanism
```

## Key takeaways

1. **InnerSource is a development model**, not a GitHub feature by itself.
2. The code generally remains private to the organization.
3. Other internal teams are enabled to contribute directly.
4. The host team retains stewardship and review authority.
5. README, CONTRIBUTING, issues, PRs, automated testing, and clear ownership are core practical building blocks.
6. InnerSource Commons emphasizes **openness, transparency, prioritized mentorship, and voluntary code contribution**.
7. GitHub is well suited to InnerSource because repositories, pull requests, CODEOWNERS, rules, issues, and Actions provide the mechanics needed to implement the model.

## Sources

- InnerSource Commons — Introduction: https://innersourcecommons.org/learn/learning-path/introduction/01/
- InnerSource Commons — InnerSource Principles: https://innersourcecommons.org/learn/learning-path/introduction/05/
- InnerSource Commons — InnerSource Patterns: https://patterns.innersourcecommons.org/
- InnerSource Commons — InnerSource Patterns repository: https://github.com/InnerSourceCommons/InnerSourcePatterns
- GitHub — An introduction to innersource: https://github.com/resources/articles/innersource
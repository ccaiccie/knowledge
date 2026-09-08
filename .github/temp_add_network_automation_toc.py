from pathlib import Path

p = Path('08-30-26-17-00_network_automation_using_github.md')
s = p.read_text()

if '## Table of contents' in s:
    raise SystemExit('TOC already present')

anchor = '## Overview\n'
toc = '''## Table of contents

- [Overview](#overview)
- [What GitHub is—and is not—in this design](#what-github-isand-is-notin-this-design)
- [Recommended repository layout](#recommended-repository-layout)
- [Control plane versus data plane](#control-plane-versus-data-plane)
- [Cisco implementation choices](#cisco-implementation-choices)
- [A safe deployment pattern](#a-safe-deployment-pattern)
  - [1. Treat inventory and variables as intent](#1-treat-inventory-and-variables-as-intent)
  - [2. Validate in pull requests](#2-validate-in-pull-requests)
  - [3. Separate plan from apply](#3-separate-plan-from-apply)
  - [4. Gate production deployments](#4-gate-production-deployments)
  - [5. Use a private, disposable runner](#5-use-a-private-disposable-runner)
- [Example: GitHub Actions calling Ansible for Cisco IOS XE](#example-github-actions-calling-ansible-for-cisco-ios-xe)
  - [Illustrative Ansible task pattern](#illustrative-ansible-task-pattern)
- [Change lifecycle and rollback](#change-lifecycle-and-rollback)
  - [Rollback principles](#rollback-principles)
- [Reconciliation and drift management](#reconciliation-and-drift-management)
- [Secrets and identity](#secrets-and-identity)
- [Common mistakes](#common-mistakes)
- [Implementation roadmap](#implementation-roadmap)
- [Key takeaways](#key-takeaways)
- [Sources](#sources)

---

'''

if anchor not in s:
    raise SystemExit('Overview heading not found')
s = s.replace(anchor, toc + anchor, 1)
p.write_text(s)

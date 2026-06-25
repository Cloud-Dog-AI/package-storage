---
template-id: T-PKG-BLD
template-version: 1.0
applies-to: BUILD.md
registry: package
required: must-have
when-applicable: ""
template-last-updated: 2026-06-12
template-owner: platform-standards

project: platform-storage
public: true
doc-last-updated: 2026-06-12
doc-git-commit: no-git
doc-git-branch: main
doc-source-shas: []
doc-age-policy: 90d
doc-conformance-stamp: 2026-06-12T12:00:00Z
---

# platform-storage — BUILD

> **Template version:** T-PKG-BLD v1.0

## 1. Local build

```bash
pip install -e .        # backend dev install
npm run build           # frontend
```

## 2. Publishable build
Internal PyPI / Gitea boundary / npm registry instructions.

## 3. Public boundary check
What gets stripped during public publication.

## 4. Cross-references
- PS-90-package-publishing.md

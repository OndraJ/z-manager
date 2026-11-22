---
name: codebase-audit
description: Deep review of the whole Zuza's Manager codebase (not a diff) – architecture, code quality, maintainability, readability, conventions, tests, tooling and docs, judged for a single-user local app. Use when the developer asks for an audit or analysis of everything built so far. Produces a verified findings report and a fix plan; changes nothing by itself.
---

# Codebase audit

## Scale lens – apply to every finding

The app serves one person on one laptop and will most likely never go to production (`AGENTS.md`). Therefore:

- **Over-engineering is a finding**, just like a bug: abstractions, tooling, configuration or defensive code this scale does not need.
- Do not recommend production concerns (scaling, HTTPS, multi-user, caching, monitoring, hardening) unless they are cheap and useful now.
- What matters most: the code stays easy to understand and change in future AI-assisted sessions – clarity, consistency, a small surface, tests that catch regressions.
- Recorded decisions in `docs/decisions.md` stand, unless a finding shows they cost more than they bring.

## Steps

1. **Inventory** – `git ls-files`, size per area; read `AGENTS.md`, `PRD.md`, `docs/decisions.md`. Skip `static/vendor/` and `design/`.
2. **Independent reads** – unless the codebase is only a few files, spawn reviewer subagents per dimension (below) in parallel. Give them the paths, the scale lens and the output format – not your own opinions, so their read is not anchored on yours. They must not edit anything.
3. **Verify** – check every returned finding against the code yourself. Drop what you cannot confirm; merge duplicates.
4. **Report** to the developer (Czech): overall verdict, findings grouped by severity, a "keep as is" list (things that look odd but are deliberate – cite the decision), and a fix plan grouped into one-feature commits. Change nothing until the developer picks what to fix.

## Dimensions

- **Architecture** – app boundaries and dependencies between apps, where logic lives, settings, coupling, dead code, consistency of patterns across apps.
- **Code quality and readability** – naming, function size, duplication, comments (why, not what), error handling, type hints consistency, Python and Django idioms.
- **Conventions** – PEP 8 beyond what ruff checks, Django conventions (app layout, URL and template naming), consistency with `AGENTS.md`.
- **Tests** – meaningful assertions, behaviour gaps, brittle tests (e.g. asserting exact HTML formatting), duplication, readability.
- **Frontend** – template structure and duplication, accessibility basics, CSS organisation, inline JS.
- **Tooling** – Makefile, Docker/Compose, hooks, scripts: correctness and proportionality to the project.
- **Docs** – `AGENTS.md`, `PRD.md`, `README.md`, `docs/`, skills: consistent with each other and with the code, nothing stale.

## Finding format

| Field | Content |
| --- | --- |
| id | e.g. A3 (dimension letter + number) |
| severity | **high** – a bug or a real maintainability risk; **medium** – worth fixing; **low** – nit |
| where | `path:line` |
| evidence | what the code does, quoted or described precisely |
| recommendation | the concrete change |
| effort | S / M / L |
| worth it at this scale | yes / no, with one sentence why |

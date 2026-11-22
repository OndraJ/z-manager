---
name: quality-review
description: Project-specific review of the current diff in Zuza's Manager before it is proposed for commit – correctness, security, maintainability, tests, UX and docs. Use after implementing a change and before the prepare-commit skill.
---

# Quality review

1. `make check` – fix every failure in the code; never weaken a check, threshold or rule.
2. Check the diff against `AGENTS.md` (Language, Architecture, Conventions, Testing) and the `django-patterns` skill.
3. Go through the review-only checklist below.
4. **Larger changes only** – run the built-in `code-review` skill, then `simplify`, and fix confirmed findings. Larger means any of: roughly 150+ changed lines of code, a new app/model/service/management command, or touching login, permissions, backups/restore or data deletion. For smaller changes skip them and say so.
5. Report what was found and fixed, and what is left open.

## Review-only checklist

These are not covered by `make check` or `AGENTS.md` rules:

- [ ] Every new behaviour has tests for the error paths and permissions too, asserting outcomes (DB state, messages, redirects), not implementation.
- [ ] Failures Zuza can hit (network, missing config, invalid input) show a clear Czech message telling her what to do.
- [ ] No queries in loops – `select_related` / `prefetch_related` where a template walks relations.
- [ ] Existing helpers, partials and factories reused instead of near-duplicates.
- [ ] Names say what things are; no dead or commented-out code; no TODO without a PRD entry.
- [ ] No secrets, real personal data or real e-mail addresses in code, tests or logs.
- [ ] Czech UI texts read naturally and match the wording of existing screens.

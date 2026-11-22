---
name: feature
description: End-to-end workflow for building a new feature, milestone or any non-trivial change in Zuza's Manager – from PRD to a proposed commit. Use whenever the developer asks to build, add or change functionality (e.g. „pojďme na rozpis směn“, „přidej …“, „udělej …“).
---

# Feature workflow

The rules live in `AGENTS.md` (Working with the developer, Language, Conventions, Definition of done). This skill only puts the work in order. Do not skip a step silently – if one does not apply, say why.

1. **Understand** – read the relevant part of `PRD.md` and `docs/decisions.md`; find the closest existing code to imitate (`django-patterns` skill). If the task holds several features, agree on their order.
2. **Clarify** – list what the PRD leaves open (data, UI, validation, edge cases, out of scope) and ask in rounds in the format of the `grilling` skill (numbered questions, each with a recommended answer). Stop when the PRD gaps are closed – a full design interview only if the developer asks for one. Write the agreed scope into `PRD.md` before coding.
3. **Plan** – for multi-file changes a short plan: models/migrations, services, views/URLs, templates, tests, docs. Get approval.
4. **Build** – code and tests together, following `django-patterns`. After model changes run `uv run python manage.py makemigrations`.
5. **Verify** – `ui-check` skill for anything visible; then `quality-review` skill.
6. **Hand over** – walk through the Definition of done in `AGENTS.md` (docs included), then the `prepare-commit` skill.

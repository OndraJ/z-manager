# Zuza's Manager – agent guide

Internal Django web app for Zuza, who runs a hotel restaurant. It runs in Docker on her Windows laptop at `http://localhost:8000`. One developer (Ondra) builds it with AI agents across many sessions – these rules exist so he never has to repeat himself.

## Sources of truth

- **`PRD.md` – what** to build: milestones and agreed scope. Never build beyond it; if it is unclear or contradicts itself, ask. Keep it current when scope is agreed in chat.
- **`docs/decisions.md` – why** things are the way they are. Do not reopen a recorded decision without new information. Add an entry for every new non-obvious decision.
- **The code – how.** Follow the existing patterns (see Architecture) instead of inventing new ones.
- If the developer states a new rule or preference in chat, **add it to this file** in the same session.

## Working with the developer

- Chat in Czech (he writes Czech). Everything in the repository follows the language rule below.
- Clarify before building: ask in short numbered rounds, each question with a recommended answer. Ask only open questions – no recaps of what is already answered.
- Non-trivial work: questions → short plan → implementation. Small fixes: just do them.
- **One feature per commit.** If a task contains several features, deliver them one by one.
- Be honest about what was verified and what was not (e.g. real SMTP sending cannot be tested here).

## Language – strict rule

Czech is allowed **only** in texts Zuza sees inside the app: templates, Django messages, form labels, model `verbose_name`, the backup e-mail. **Everything else is English** – Python identifiers and comments, JS/Apps Script, Makefile, configs, docs, PRD, commit messages, and names that scripts create outside the app (Drive folders, Gmail labels, file names). Docs may quote a UI label in „…“ (e.g. the „Zálohovat“ button). Enforced by `make check-language` (`scripts/check_language.py`).

## Definition of done

A task is done only when all of these hold:

1. `make check` passes: ruff (incl. security and simplification rules), format, language check, no missing migrations, Django deploy checks, tests with ≥ 90 % branch coverage. Never weaken a check to make it pass – fix the code, or ask.
2. New behaviour has unit tests (every view, form, model method, service, management command).
3. UI changes are verified in a browser (isolated `zm-test` stack, screenshots reviewed).
4. `PRD.md`, `docs/decisions.md`, `README.md` and this file are updated where affected.
5. The diff is summarized to the developer and the commit is proposed – **not** made – until he approves.

## Architecture

- `config/` – single env-driven `settings.py`, root URLs, WSGI, `utils.py` (shared helpers such as `get_safe_next_url`).
- One Django app per domain area:
  - `accounts` – login/logout via Django auth views (`templates/registration/login.html`)
  - `dashboard` – home page, `hotel_links` context processor
  - `employees` – staff records: model, filters, inline status change, Czech collation
  - `backups` – e-mail backup (`services.py`), confirmation modal, `restore_backup` command
- Business logic lives in `services.py` / model or queryset methods – views stay thin (see `backups/services.py`, `Employee.objects.ordered()`).
- Templates: `base.html` (skeleton) → `layout.html` (header, sidebar, messages, `content` block) → page templates. Reusable pieces in `templates/partials/`.
- Styling: Bootstrap 5 + Bootstrap Icons vendored in `static/vendor/` (never edit, no CDN – the app must work offline). Brand overrides only in `static/css/app.css`.
- Settings that may change (e.g. `HOTEL_LINKS`, e-mail) come from `config/settings.py` / `.env`, never hard-coded in templates.

## Conventions

- Prefer Django built-ins: class-based views, `ModelForm`, auth views, `messages` / `SuccessMessageMixin`, `LoginRequiredMixin` on every view except login.
- **Employees are always listed via `Employee.objects.ordered()`** (status order, then Czech alphabetical order through the `czech` SQLite collation). Plain `order_by("last_name")` sorts Czech names wrongly.
- Redirects to a POSTed `next` URL go through `config.utils.get_safe_next_url`.
- State-changing actions are POST only (`http_method_names = ["post"]` where a view only changes state).
- Sidebar items appear only when the feature is finished.
- Add a dependency only when it clearly saves work; record why in `docs/decisions.md`.
- Keep it simple – one user, one laptop, an experiment.

## Testing

- Django test runner, tests in `<app>/tests/test_*.py`, shared factories in `<app>/tests/factories.py` (e.g. `make_employee`).
- Arrange / act / assert, one behaviour per test, descriptive names.
- Anything using the SQLite backup API (backups, restore) must use `TransactionTestCase` – the backup API cannot run inside the transaction `TestCase` opens.
- Real e-mail is never sent in tests (Django's locmem backend).

## Commands

Run `make` to list all targets. Most used:

```bash
make check     # full quality gate – must pass before a commit
make format    # auto-fix lint issues and format
make test      # tests only (make coverage = tests + coverage report)
make up/down   # developer's own dev instance in Docker – do not use for verification
make migrate   # apply migrations in the running dev container (containers migrate only at start)
```

New recurring commands get a Makefile target with a `## description` comment.

## Safety

- **The Docker daemon is shared with the developer's own setup** (project `z_manager`, port 8000, his data volume). For verification always use an isolated project and port: `ZM_PORT=8001 docker compose -p zm-test ...`. Never `down -v` anything but `zm-test`.
- **The developer's `.env` contains real Gmail SMTP credentials.** Test stacks read the same `.env`, so always override `EMAIL_HOST: ""` and `EMAIL_HOST_PASSWORD: ""` in the test compose override.
- Never print, log or commit secrets (`.env` values). `.env.example` documents every variable.
- The dev Compose file is `compose.dev.yaml`, deliberately not `compose.override.yaml`, so Docker never auto-loads dev settings on Zuza's laptop.

## Git

- Commit only after the developer has seen the summary and approved it.
- Commit messages: short English imperative summary. **No `Co-Authored-By` trailer or any AI attribution.**
- Never push, create or switch branches, or rewrite history – the developer does that.

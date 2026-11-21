# Zuza's Manager

Internal Django web app for a hotel restaurant manager (Zuza). Runs locally in Docker on her Windows laptop at `http://localhost:8000`.

**What to build is defined in @PRD.md.** Work on one milestone at a time and do not add features, screens or fields the PRD does not ask for. If the PRD is unclear or contradicts itself, ask instead of guessing.

## Stack

- Python 3.14, latest stable Django, dependencies managed with **uv** (`pyproject.toml`, `uv.lock`)
- Django templates + **Bootstrap 5**, vendored in `static/vendor/` (no CDN – the app must work offline). Bootstrap Icons for icons.
- Brand: cherry/višňová colour taken from the logo, applied by overriding Bootstrap CSS variables in one project stylesheet. Font Bricolage Grotesque (vendored woff2) only for the logo and headings.
- SQLite in a persistent Docker volume
- Production runtime: gunicorn, `DEBUG=False`, whitenoise, config from `.env` (never committed; keep `.env.example` up to date)

## Commands

Local commands read `.env` (via python-dotenv). For development create it with `DJANGO_DEBUG=1` – see `.env.example`.

```bash
uv sync                                    # install dependencies
uv run python manage.py runserver          # quick local run without Docker
uv run python manage.py test               # unit tests
uv run ruff check . && uv run ruff format . # lint + format

docker compose up -d --build               # production setup (what runs on Zuza's laptop)
docker compose -f compose.yaml -f compose.dev.yaml up --build   # dev setup with runserver + mounted source
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

The dev Compose file is deliberately **not** named `compose.override.yaml`, so Docker never auto-loads dev settings on Zuza's laptop.

The containers run `migrate` only at start. After adding a migration, run `docker compose -f compose.yaml -f compose.dev.yaml exec web python manage.py migrate` (or restart the container).

The Docker daemon is shared with the developer's own setup (project name `z_manager`). For automated verification use a separate project, e.g. `docker compose -p zm-test …`, and never `down -v` the `z_manager` project – that deletes the developer's data volume.

## Conventions

- **Language:** all code, identifiers, comments, docstrings, commit messages and docs for developers in English. Only user-facing texts (templates, messages, form labels, model `verbose_name`) are in Czech. `LANGUAGE_CODE = "cs"`, `TIME_ZONE = "Europe/Prague"`.
- **Layout:**
  - `config/` – settings (single env-driven file), root URLs, WSGI
  - one Django app per domain area: `accounts` (login/logout via Django auth views), `dashboard` (home page, `hotel_links` context processor), `employees` (staff records)
  - Always list employees with `Employee.objects.ordered()` – status order (active, sick, terminated), then Czech alphabetical order by name via the `czech` SQLite collation (`employees/collation.py`). Plain `order_by("last_name")` sorts Czech names wrongly.
  - Django messages are rendered as Bootstrap alerts by `templates/layout.html` – use `messages`/`SuccessMessageMixin` for feedback after actions.
  - `templates/base.html` (HTML skeleton) → `templates/layout.html` (header + sidebar + `content` block) → page templates; reusable pieces in `templates/partials/` (`_logo`, `_header`, `_sidebar`)
  - `static/css/app.css` – the only project stylesheet (brand variables, layout); `static/img/bell.svg` – logo icon and favicon; third-party assets in `static/vendor/` (never edit)
  - Sidebar items are added only when the feature is finished (PRD).
- **Configuration values** that may change (e.g. `HOTEL_LINKS`) live in `config/settings.py`, not in templates.
- **Auth:** a single account, no registration, no password reset by e-mail, Django admin disabled. All pages except login require login.
- Prefer Django built-ins (auth views, class-based views, forms, messages) over custom code or extra packages. Add a dependency only when it clearly saves work.
- Keep it simple – this is an experiment for one user, not a SaaS.

## Testing

- Write unit tests with Django's test runner (`django.test.TestCase`) for every view, form and model behaviour you add, in `tests/` inside each app.
- Before saying a task is done: tests pass, `ruff check` is clean, and the milestone's "How we verify completion" steps in the PRD are satisfied.

## Git

Do not commit until the user has reviewed the diff and approved it. Never push, create or switch branches – the user does that.

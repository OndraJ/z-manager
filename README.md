# Zuza’s Manager

Internal web app for managing a hotel restaurant – staff, shift planning and more. Product requirements are in [PRD.md](PRD.md), conventions for coding agents in [CLAUDE.md](CLAUDE.md).

Stack: Python 3.14, Django, Bootstrap 5, SQLite, Docker Compose.

## Local development

```bash
cp .env.example .env        # then set DJANGO_DEBUG=1
uv sync
uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py runserver
```

Tests and linting:

```bash
uv run python manage.py test
uv run ruff check . && uv run ruff format .
```

Development in Docker (runserver, source mounted):

```bash
docker compose -f compose.yaml -f compose.dev.yaml up --build
```

## Installation on Zuza’s laptop (Windows)

1. Install Docker Desktop and Git for Windows. In Docker Desktop enable *Start Docker Desktop when you sign in* (Settings → General).
2. Clone the repository and create `.env` from `.env.example`:
   - `DJANGO_SECRET_KEY` – generate with `docker run --rm python:3.14-slim python -c "import secrets; print(secrets.token_urlsafe(50))"` (no Python needed on Windows)
   - `DJANGO_DEBUG=0`
3. Start the app (it restarts automatically with Docker Desktop):
   ```bash
   docker compose up -d --build
   ```
4. Create Zuza’s account:
   ```bash
   docker compose exec web python manage.py createsuperuser
   ```
5. Bookmark `http://localhost:8000` in her browser.

The database lives in the Docker volume `z_manager_data` – never run `docker compose down -v` on her laptop.

### Forgotten password

```bash
docker compose exec web python manage.py changepassword <username>
```

### Deploying a new version

```bash
git pull
docker compose up -d --build
```

Migrations run automatically when the container starts.

## Manual check (milestone 1)

1. After `docker compose up -d --build`, `http://localhost:8000` loads.
2. Opening the dashboard while logged out redirects to the login page.
3. Logging in shows the header (logo, hotel links, „Odhlásit“) and the sidebar. A wrong password keeps you on the login page with an error message.
4. After logging out, the dashboard requires logging in again.
5. After `docker compose up -d --build --force-recreate`, the original credentials still work.

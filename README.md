# Zuza’s Manager

Internal web app for managing a hotel restaurant – staff, shift planning and more. Product requirements are in [PRD.md](PRD.md), conventions for coding agents in [CLAUDE.md](CLAUDE.md).

Stack: Python 3.14, Django, Bootstrap 5, SQLite, Docker Compose.

## Development

Common commands are in the `Makefile` – run `make` to list them.

```bash
cp .env.example .env        # then set DJANGO_DEBUG=1
make up                     # dev app in Docker at http://localhost:8000
make createsuperuser        # first time only
make logs                   # follow logs
make down                   # stop (data is kept)
make check                  # quality gate: lint, language, migrations, deploy checks, tests + coverage
```

Without Docker: `make install` and `make run`.

## Installation on Zuza’s laptop (Windows)

Windows has no `make`, so the commands below are plain `docker compose` calls (the `prod-*` make targets do the same).

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

### Backups

The „Zálohovat“ button at the bottom of the sidebar e-mails a copy of the database (`zuzas-manager-<date>.sqlite3`) to `BACKUP_EMAIL_TO`. The app sends from its own Gmail account `zuzasmanager@gmail.com` – fill in the `EMAIL_*` values in `.env` (see `.env.example`) and restart: `docker compose up -d`.

Without `EMAIL_HOST` (e.g. in development) the e-mail is only printed to the container log.

Backups are also copied to Google Drive by an Apps Script in the app's Gmail account – see [docs/drive-backup.md](docs/drive-backup.md).

### Restoring from a backup

Save the attachment from the backup e-mail, then (on a Mac/Linux machine with make):

```bash
make restore FILE=path/to/zuzas-manager-2026-11-21-2204.sqlite3        # dev
make prod-restore FILE=path/to/zuzas-manager-2026-11-21-2204.sqlite3   # production
```

On Zuza’s Windows laptop (PowerShell, in the project folder):

```powershell
docker compose cp "C:\Users\<user>\Downloads\zuzas-manager-....sqlite3" web:/tmp/restore.sqlite3
docker compose exec -u root web chmod 644 /tmp/restore.sqlite3
docker compose exec web python manage.py restore_backup /tmp/restore.sqlite3
```

The command checks the file, asks for confirmation, keeps a safety copy of the current data in the volume (`/data/before-restore-*.sqlite3`) and applies migrations, so older backups work too.

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

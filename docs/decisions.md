# Decision log

Why the project is the way it is. Newest decisions at the bottom. Format: **decision** – reason; rejected alternatives.

## Platform and runtime (2026-11-21)

1. **Runs locally on Zuza's Windows laptop in Docker Desktop, reachable only at `localhost`.** – An experiment for one user; a server or phone access can come later. Port bound to `127.0.0.1` so the app is not exposed to the hotel network. Rejected: running natively without Docker (the developer prefers identical environments; the laptop has enough RAM).
2. **Production mode on the laptop** (gunicorn, `DEBUG=False`, whitenoise) and a separate `compose.dev.yaml` for development. – Zuza uses it for real. The dev file is not called `compose.override.yaml`, which Docker would auto-load.
3. **Django + templates + Bootstrap 5, vendored (no CDN)** – the app must work offline; the developer chose Bootstrap over plain CSS. Fonts and icons are vendored for the same reason.
4. **SQLite in a named Docker volume** – single user, zero administration; survives container replacement.
5. **`tzdata` dependency** – `Europe/Prague` must resolve outside Docker too (Windows, slim systems).

## Accounts (2026-11-21)

6. **One account, no registration, no e-mail password reset, Django admin disabled.** – Only Zuza uses the app; the developer creates the account and resets the password with management commands.
7. **Session expires 24 hours after the last activity** (sliding). – Chosen by the developer.

## Staff records (2026-11-21)

8. **Employees are never deleted; ending employment is a status change** (`active`, `sick`, `terminated`). – Future shift schedules must keep their history.
9. **Working hours are not modelled yet** – deferred until it is clear what the number means (target vs. limit, period).
10. **Custom `czech` SQLite collation** – SQLite sorts bytes („Černá“ after „Zelený“); Czech order needs „č, ř, š, ž“ and „ch“ as separate letters. Rejected: sorting in Python (breaks queryset composition), ICU (heavy dependency).
11. **Status can be changed inline in the list and in the edit form; filters by status and employment type combine.** – Agreed with the developer.

## Backups (2026-11-21 – 2026-11-22)

12. **Backup = e-mail with the SQLite file, sent from the app's own Gmail account `zuzasmanager@gmail.com`** (SMTP + app password in `.env`). – Gets the data off the laptop and keeps a history in the mailbox with no extra dependencies. Rejected: copying to a Windows folder (fragile bind mounts, stays on the same laptop), Google Drive API (Cloud project, OAuth tokens that expire or get revoked – Zuza could not fix it), download-only button (relies on Zuza moving the file).
13. **Google Apps Script in the app's Gmail account copies backup attachments to Google Drive hourly** (`docs/drive-backup-apps-script.js`). – Drive copies without any credentials or code in the app; if it breaks, e-mail backups still work.
14. **A confirmation modal shows the recipient before sending.** – Requested by the developer.
15. **Restore is done by the developer (`make restore` / `restore_backup`), not in the app.** – One wrong click would overwrite all data. In-app drag & drop restore is an open question in the PRD.

## Working rules (2026-11-21 – 2026-11-22)

16. **English everywhere except texts Zuza sees in the app.** – Repeated three times by the developer; enforced in `AGENTS.md`.
17. **One feature per commit, no AI attribution in commit messages, the developer pushes.**
18. **Verification uses an isolated `zm-test` Docker project with SMTP disabled.** – The Docker daemon and `.env` are shared with the developer's own instance; an early test run deleted the developer's data volume.

## Quality gate (2026-11-22)

19. **HTTPS-only security checks are silenced** (`security.W004/W008/W012/W016`). – The app is served over plain HTTP on `localhost` only; secure cookies or SSL redirects would break login. Revisit if the app moves to a server.
20. **`make check` is the quality gate**: ruff (incl. simplification and security rules), format check, language check (`scripts/check_language.py`), missing-migration check, Django deploy checks and tests with ≥ 90 % branch coverage (`coverage` dev dependency). – Rules that a script can verify are enforced by the script, not by instructions.
21. **Rules a machine can check are enforced by Claude Code hooks** (`.claude/settings.json` → `scripts/claude_hooks.py`). – The developer does not want to repeat rules or check that they were followed. Details:
    - Commands are parsed like a shell (quotes, `;`, `&&`, `|`), so only real `git`/`docker` commands are blocked, not text that mentions them.
    - `git commit` must run alone with nothing unstaged, so `make check` on the working tree tests exactly what is committed.
    - The formatter never auto-removes unused imports or variables (an agent adds an import before the code that uses it).
    - Without `uv` on `PATH` the hooks block loudly instead of switching off silently.
    - Hook logic is a tested Python module rather than inline shell, so `make check` covers it.

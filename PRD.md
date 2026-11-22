# Zuza’s Manager

## Product purpose

Zuza runs a hotel restaurant. Among other things she is responsible for staff, shift planning and the storeroom. Zuza’s Manager is an internal web application designed specifically for her. The goal is to simplify her paperwork. It is an experiment: once she has tried the app in day-to-day operation, she will decide whether she wants to keep using it and what is worth developing further.

The user interface is in Czech. Czech UI labels are quoted in this document as they should appear in the app.

## Milestone 1 – local app with login ✅ done

Zuza opens a local address in the browser on her computer, logs in and lands on the home dashboard. This milestone delivers the project skeleton, a working local setup and the visual foundation for further screens.

| Area | Agreement |
| --- | --- |
| Operation | The app runs on Zuza’s Windows laptop in Docker Desktop via Docker Compose and is reachable only from that computer at `http://localhost:8000`. Installation, deploying new versions and maintenance are done by the developer (in person or via remote desktop). Zuza never runs any commands. |
| Runtime | Production mode: gunicorn, `DEBUG=False`, static files served by whitenoise, `SECRET_KEY` in `.env` outside git, `ALLOWED_HOSTS` limited to localhost. A separate Compose file with `runserver` for development. Dependencies managed with uv. |
| Frontend | Django templates and Bootstrap 5 vendored in the project (no CDN), colours adjusted to the logo. Icons from Bootstrap Icons. The UI is in Czech (`cs`, `Europe/Prague`). |
| Backend | Python and Django handle requests, authentication and data access via the Django ORM. |
| Database | SQLite. The database file is stored in a persistent Docker volume so the account survives replacing the application container. |
| Account | There is a single account and no registration. The developer creates the account with a command inside the container; login is by username. A forgotten password is reset by the developer with `changepassword`. No e-mail password recovery and no Django admin. |
| Session | The login expires 24 hours after the last activity. Logging out ends it immediately. |
| Login page | Logo and login form, no header and no links. |
| Layout after login | A full-width header with the logo in the centre. On the right side of the header, icon links to Hotel Schreiner’s [website](https://hotelschreiner.cz/), [Facebook](https://www.facebook.com/schreinerhotel) and [Instagram](https://www.instagram.com/hotelschreiner/) (opening in a new tab) and a logout button („Odhlásit“). A sidebar on the left, the main dashboard on the right. |
| Sidebar | Contains only the „Pracovní plocha“ (dashboard) item. Further items are added only once the corresponding features are finished. |
| Visual identity | Cherry („višňová“) colour, the name **Zuza’s Manager** with an apostrophe and a logo with a hotel service bell. [Selected logo](design/logo.png). The bell is redrawn as SVG and also serves as the favicon. The name is rendered as text in Bricolage Grotesque, vendored in the project (works offline) and used only for the logo and headings; other text uses the system font. Colours are taken from the logo. Social media icons come from Bootstrap Icons. Link URLs live in configuration. |

### How we verify completion

Steps 2–4 are covered by unit tests. All steps are additionally verified by clicking through manually.

1. After starting the project via Docker Compose, the app loads in the browser at `localhost:8000`.
2. When Zuza opens the dashboard URL without being logged in, the app redirects her to the login page.
3. Zuza logs in with her account and sees the header with the logo and links, and the dashboard with the left sidebar. When she enters a wrong password, she stays on the login page and sees a message that the login failed.
4. After logging out, the dashboard requires logging in again.
5. After replacing the application container with the volume preserved, Zuza logs in with her original credentials.

## Milestone 2 – staff records and backup ✅ done

| Area | Agreement |
| --- | --- |
| Navigation | A new sidebar item „Správa zaměstnanců“ below „Pracovní plocha“. |
| Employee data | First name, last name, date of birth, employment type (HPP – full-time employment contract, or „brigáda“ – casual/part-time work) and status („aktivní“ active, „nemocný“ sick, „ukončený“ terminated; default active). All fields are required; the date of birth cannot be in the future. |
| Editing | Adding and editing happen on a separate page; after saving, Zuza returns to the list with a confirmation message. The status can also be changed directly in the list (saved immediately). Employees cannot be deleted; ending employment is recorded by changing the status. |
| List | Shows name, date of birth, employment type, status and an edit button. Filters by status and by employment type combine. Without a filter: active, sick, terminated, then Czech alphabetical order by last and first name. The staff records are the source of employees for the shift schedule. |
| Backup | A „Zálohovat“ button at the bottom of the sidebar asks for confirmation (showing the recipient) and e-mails a copy of the SQLite database from the app's own Gmail account `zuzasmanager@gmail.com`. Every backup is a separate e-mail, so the mailbox keeps the history; an Apps Script in that account also copies each backup to Google Drive (`docs/drive-backup.md`). |
| Restore | Done by the developer with the `restore_backup` command (README → Restoring from a backup): it validates the file, asks for confirmation and keeps a safety copy of the current data. |

### How we verify completion

Covered by unit tests; additionally clicked through manually.

1. Zuza adds an employee; a missing field or a future date of birth shows an error next to the field.
2. She edits an employee and changes a status directly in the list; the list keeps its filters and confirms the change.
3. Filters by status and employment type combine; names with „Č“, „Ch“ and „Š“ are in Czech alphabetical order.
4. „Zálohovat“ shows the recipient, sends the e-mail with the database attached, and the file appears on Google Drive within an hour.
5. Restoring that file with `restore_backup` brings the data back and leaves a safety copy of the previous state.

## Next milestones

| Order | Area | Scope agreed so far |
| --- | --- | --- |
| 3 | Shift schedule | Zuza builds the schedule in advance for a week, several weeks or a month and assigns employees from the staff records to shifts. All employees are available for selection, in the same order as in the staff records. The detailed design will be done when the milestone starts. |

Any further areas will be decided based on experience with using the app.

## Open questions for further design

**Shift schedule**

- Working hours (contracted hours for HPP, a limit for „brigáda“) and any checking of statutory limits for casual work – deferred from staff records (`docs/decisions.md` #9).

**Backup – ideas, only if Zuza needs them**

- Restoring a backup by Zuza herself in the app (e.g. drag & drop).
- A reminder when the last backup is old.

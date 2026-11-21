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
| Visual identity | Cherry (višňová) colour, the name **Zuza’s Manager** with an apostrophe and a logo with a hotel service bell. [Selected logo](design/logo.png). The bell is redrawn as SVG and also serves as the favicon. The name is rendered as text in Bricolage Grotesque, vendored in the project (works offline) and used only for the logo and headings; other text uses the system font. Colours are taken from the logo. Social media icons come from Bootstrap Icons. Link URLs live in configuration. |

### How we verify completion

Steps 2–4 are covered by unit tests. All steps are additionally verified by clicking through manually.

1. After starting the project via Docker Compose, the app loads in the browser at `localhost:8000`.
2. When Zuza opens the dashboard URL without being logged in, the app redirects her to the login page.
3. Zuza logs in with her account and sees the header with the logo and links, and the dashboard with the left sidebar. When she enters a wrong password, she stays on the login page and sees a message that the login failed.
4. After logging out, the dashboard requires logging in again.
5. After replacing the application container with the volume preserved, Zuza logs in with her original credentials.

## Next milestones

| Order | Area | Scope agreed so far |
| --- | --- | --- |
| 2 | Simple staff records | A new sidebar item „Správa zaměstnanců“ below „Pracovní plocha“. Zuza can add an employee and edit all of their data: first name, last name, date of birth, employment type (HPP – full-time employment contract, or brigáda – casual/part-time work) and status („aktivní“ active, „nemocný“ sick, „ukončený“ terminated; default active). All fields are required; the date of birth cannot be in the future. Adding and editing happen on a separate page; after saving, Zuza returns to the list with a confirmation message. Employees cannot be deleted; ending employment is recorded by changing the status. The status can also be changed directly in the list (saved immediately). The list shows name, date of birth, employment type, status and an edit button, and can be filtered by status and by employment type (filters combine). Without a filter it shows all employees ordered: active, sick, terminated, then alphabetically by last and first name (Czech alphabetical order). The milestone also includes a „Zálohovat“ (back up) button at the bottom of the sidebar that e-mails a copy of the SQLite database to a configured address (the app sends from its own Gmail account, `zuzasmanager@gmail.com`). Every backup is a separate e-mail, so the mailbox keeps the history. Restoring from a backup is done by the developer with a command (`make restore`); it validates the file, asks for confirmation and keeps a safety copy of the current data. The staff records will be the source of employees when building the shift schedule. |
| 3 | Shift schedule | Zuza builds the schedule in advance for a week, several weeks or a month and assigns employees from the staff records to shifts. All employees are available for selection, in the same order as in the staff records. The detailed design will be done after the app foundation is finished. |

Any further areas will be decided based on experience with using the app.

## Open questions for further design

**When implementing staff records**

- Working hours (contracted hours for HPP, a limit for brigáda) and any checking of statutory limits for casual work are to be resolved when the feature is implemented.
- Whether Zuza should be able to restore a backup herself in the app (e.g. drag & drop), and whether to add a reminder when the last backup is old.

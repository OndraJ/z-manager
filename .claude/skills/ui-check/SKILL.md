---
name: ui-check
description: Verify UI changes of Zuza's Manager in a real browser on an isolated Docker stack – start it, create test data, take screenshots, review them, tear it down. Use after any change to templates, CSS, forms or views.
---

# UI check

Use only the `make verify-*` targets – why is in `AGENTS.md` → Safety.

1. `make verify-up` – starts the isolated stack (port 8001) and creates the user `verify` / `verify-password-123`.
2. Create the data the screens need – empty lists show nothing useful:
   ```bash
   make verify-manage ARGS='shell -c "from employees.tests.factories import make_employee; make_employee(last_name=\"Novak\")"'
   ```
   Use realistic Czech names with diacritics (e.g. „Černá“, „Šimek“, „Chalupa“) to check fonts and ordering.
3. `make verify-shots PAGES="/ /employees/ /employees/new/"` – full-page screenshots in `.verify/screenshots/`. A non-zero exit means HTTP or browser console errors – treat it as a bug.
4. **Read every screenshot.** Check layout and alignment with existing screens, Czech texts, error and empty states, and that nothing English is visible to Zuza.
5. Interactions (modals, inline changes, form errors): a short Playwright script in the scratchpad based on `scripts/screenshots.py`. Target buttons inside the page content – `button[type=submit]` alone also matches „Odhlásit“ in the header.
6. `make verify-down` – always, also after a failure.

Give the developer the screenshot paths in the summary.

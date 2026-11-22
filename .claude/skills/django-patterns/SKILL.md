---
name: django-patterns
description: How code is written in Zuza's Manager – models, querysets, services, views, forms, URLs, templates, messages and tests, with reference files to copy. Use before writing or changing any Django code in this project.
---

# Django patterns of this project

The binding rules are in `AGENTS.md` → Architecture, Conventions and Testing. This skill shows **how** they look in code – copy the closest reference file instead of inventing a new style.

| Building | Copy from | Notes |
| --- | --- | --- |
| Model with choices | `employees/models.py` | `TextChoices` with English values and Czech labels; Czech `verbose_name`; `__str__` is what Zuza reads |
| Validation | `employees/validators.py` | small functions, Czech message, `code=` set |
| Query logic | `EmployeeQuerySet` in `employees/models.py` | queryset methods via `as_manager()`; name ordering through `Collate(field, COLLATION_NAME)` |
| Non-model logic | `backups/services.py` | plain functions; raise a domain exception, the view turns it into a message |
| List with filters | `EmployeeListView` | read query params, ignore invalid values, pass active filter + choices to the template |
| Create / edit | `EmployeeCreateView`, `EmployeeUpdateView` | `ModelForm` + `SuccessMessageMixin`, redirect to the list |
| POST-only action | `EmployeeStatusUpdateView`, `backups/views.py` | `http_method_names = ["post"]`, redirect via `get_safe_next_url`; expected failures → `messages.error` + `logger.exception` |
| Form | `employees/forms.py` | Bootstrap classes in widget `attrs`, `is-invalid` on errors, `type="date"` inputs, Czech blank choice label |
| URLs | `employees/urls.py` | `app_name` namespace, English paths |
| Page template | `templates/employees/employee_list.html` | extends `layout.html`, fills `title` and `content` |
| Form template | `templates/employees/employee_form.html` | one template for create and edit |
| Confirmation dialog | `templates/partials/_backup_modal.html` | Bootstrap modal, included from `layout.html` |
| Value from settings in templates | `dashboard/context_processors.py` | context processor registered in `config/settings.py` |
| Management command | `backups/management/commands/restore_backup.py` | validate input, ask for confirmation, `CommandError` with a clear message |
| Tests | `employees/tests/`, `backups/tests/` | factories in `tests/factories.py`; one behaviour per test |

Styling: Bootstrap components and utilities first; custom CSS only in `static/css/app.css` with the `--zm-*` variables. Icons: Bootstrap Icons with `aria-hidden="true"`; icon-only controls need `aria-label` / `title`.

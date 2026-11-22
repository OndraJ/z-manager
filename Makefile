# Zuza's Manager – common commands. Run `make` to list them.
#
# These run on the developer's machine. Zuza's Windows laptop has no make – production
# commands for it are plain `docker compose` calls in README.md.

DEV := docker compose -f compose.yaml -f compose.dev.yaml

.DEFAULT_GOAL := help
.PHONY: help up down restart logs ps shell migrate makemigrations createsuperuser \
	changepassword restore \
	verify-up verify-shots verify-manage verify-down install run test coverage lint format \
	check check-language check-migrations check-deploy

help: ## Show this help
	@grep -E '^(## ---|[a-zA-Z_-]+:.*## )' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*## "} \
			/^## ---/ {gsub(/^## -+ | -+$$/, ""); printf "\n\033[1m%s\033[0m\n", $$0; next} \
			{printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

## --- Docker (development) ---

up: ## Build and start the dev app at http://localhost:8000
	$(DEV) up -d --build

down: ## Stop the dev app (data in the volume is kept)
	$(DEV) down

restart: ## Restart the dev app (also applies new migrations)
	$(DEV) restart web

logs: ## Follow the app logs
	$(DEV) logs -f web

ps: ## Show container status
	$(DEV) ps

shell: ## Open a shell in the running container
	$(DEV) exec web sh

migrate: ## Apply database migrations in the running container
	$(DEV) exec web python manage.py migrate

makemigrations: ## Create migrations (written to the mounted source)
	$(DEV) exec web python manage.py makemigrations

createsuperuser: ## Create the login account
	$(DEV) exec web python manage.py createsuperuser

changepassword: ## Reset a password: make changepassword ACCOUNT=<username>
	@test -n "$(ACCOUNT)" || { echo "Usage: make changepassword ACCOUNT=<username>"; exit 1; }
	$(DEV) exec web python manage.py changepassword $(ACCOUNT)

restore: ## Restore the dev data from a backup e-mail attachment: make restore FILE=<file>
	@test -n "$(FILE)" || { echo "Usage: make restore FILE=<backup.sqlite3>"; exit 1; }
	$(DEV) cp "$(FILE)" web:/tmp/restore.sqlite3
	$(DEV) exec -u root web chmod 644 /tmp/restore.sqlite3
	$(DEV) exec web python manage.py restore_backup /tmp/restore.sqlite3

## --- Verification (isolated zm-test stack, port 8001, no real e-mail) ---

VERIFY := ZM_PORT=8001 docker compose -p zm-test -f compose.yaml -f compose.dev.yaml -f compose.verify.yaml
VERIFY_URL := http://127.0.0.1:8001
VERIFY_USER := verify
VERIFY_PASSWORD := verify-password-123
SHOTS_DIR ?= .verify/screenshots
PAGES ?= / /employees/ /employees/new/

verify-up: ## Start the isolated verification stack with a test account
	$(VERIFY) up -d --build
	@for i in $$(seq 1 60); do curl -sf -o /dev/null $(VERIFY_URL)/login/ && break; sleep 1; done
	@curl -sf -o /dev/null $(VERIFY_URL)/login/ || \
		{ echo "Verification stack did not start:"; $(VERIFY) logs --tail 30 web; exit 1; }
	@$(VERIFY) exec -T web python manage.py shell -c \
		"from django.contrib.auth.models import User; User.objects.filter(username='$(VERIFY_USER)').exists() or User.objects.create_superuser('$(VERIFY_USER)', '', '$(VERIFY_PASSWORD)')"
	@echo "Verification stack: $(VERIFY_URL) (user $(VERIFY_USER) / $(VERIFY_PASSWORD))"

verify-shots: ## Screenshot pages of the verification stack: make verify-shots PAGES="/ /employees/"
	uv run --quiet --with playwright python -m playwright install chromium
	uv run --quiet --with playwright python scripts/screenshots.py --base $(VERIFY_URL) \
		--out $(SHOTS_DIR) --user $(VERIFY_USER) --password $(VERIFY_PASSWORD) $(PAGES)

verify-manage: ## Run manage.py in the verification stack: make verify-manage ARGS='shell -c "…"'
	$(VERIFY) exec -T web python manage.py $(ARGS)

verify-down: ## Stop the verification stack and delete its data
	$(VERIFY) down -v

## --- Local (uv, without Docker) ---

install: ## Install dependencies
	uv sync

run: ## Run the dev server locally (needs .env with DJANGO_DEBUG=1)
	uv run python manage.py migrate
	uv run python manage.py runserver

test: ## Run unit tests
	uv run python manage.py test

coverage: ## Run unit tests with coverage (fails under 90 %)
	uv run coverage run manage.py test
	uv run coverage report

lint: ## Check code with ruff
	uv run ruff check .
	uv run ruff format --check .

format: ## Format code and fix lint issues
	uv run ruff check --fix .
	uv run ruff format .

check-language: ## Fail on Czech outside app texts (see AGENTS.md)
	uv run python scripts/check_language.py

check-migrations: ## Fail if a model change has no migration
	uv run python manage.py makemigrations --check --dry-run

check-deploy: ## Run Django's production security checks
	DJANGO_DEBUG=0 DJANGO_SECRET_KEY=$(DEPLOY_CHECK_KEY) \
		uv run python manage.py check --deploy --fail-level WARNING

# Throw-away key, only so the deploy check can load production settings.
DEPLOY_CHECK_KEY := deploy-check-only-6f1c2b9e4d7a0c3f8e5b1d9a7c4f2e0b8d6a3c1f

check: lint check-language check-migrations check-deploy coverage ## Full quality gate (run before committing)

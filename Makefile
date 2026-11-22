# Zuza's Manager – common commands. Run `make` to list them.
#
# Docker targets use the dev setup (runserver + mounted source) by default.
# prod-* targets use the production setup that runs on Zuza's laptop.

# Copy a backup into the container and restore it (asks for confirmation).
# $(1) = compose command
define restore_backup
	@test -n "$(FILE)" || { echo "Usage: make $@ FILE=<backup.sqlite3>"; exit 1; }
	$(1) cp "$(FILE)" web:/tmp/restore.sqlite3
	$(1) exec -u root web chmod 644 /tmp/restore.sqlite3
	$(1) exec web python manage.py restore_backup /tmp/restore.sqlite3
endef

DEV  := docker compose -f compose.yaml -f compose.dev.yaml
PROD := docker compose

.DEFAULT_GOAL := help
.PHONY: help up down restart logs ps shell migrate makemigrations createsuperuser \
	changepassword restore prod-up prod-down prod-restart prod-logs prod-migrate prod-restore \
	install run test coverage lint format check check-language check-migrations check-deploy

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

restore: ## Restore data from a backup e-mail attachment: make restore FILE=<file>
	$(call restore_backup,$(DEV))

## --- Docker (production, Zuza's laptop) ---

prod-up: ## Build and start the production app
	$(PROD) up -d --build

prod-down: ## Stop the production app (data in the volume is kept)
	$(PROD) down

prod-restart: ## Restart the production app
	$(PROD) restart web

prod-logs: ## Follow the production logs
	$(PROD) logs -f web

prod-migrate: ## Apply migrations in the production container
	$(PROD) exec web python manage.py migrate

prod-restore: ## Restore production data from a backup: make prod-restore FILE=<file>
	$(call restore_backup,$(PROD))

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

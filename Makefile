SHELL := /bin/sh

.PHONY: help up up-detached down logs
.PHONY: infra-up infra-down api web
.PHONY: migrate new-migration seed
.PHONY: test test-api test-web
.PHONY: typecheck lint-web lint-api format

help: ## Show available targets
	@grep -E '^[a-zA-Z-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "%-16s %s\n", $$1, $$2}'

# ---------------------------------------------------------------- URL
up: ## Build and start all services (docker compose up --build)
	docker compose up --build

up-detached: ## Build and start all services in background
	docker compose up --build -d

down: ## Stop and remove containers (keeps the postgres volume)
	docker compose down

logs: ## Tail logs of all services
	docker compose logs -f

infra-up: ## Start only PostgreSQL locally
	docker compose up -d postgres

infra-down: ## Stop only PostgreSQL
	docker compose down postgres

api: ## Run the FastAPI backend locally with hot reload (requires Postgres)
	cd apps/api && uvicorn app.main:app --reload --port $(or $(API_PORT),8001)

web: ## Run the Next.js frontend locally
	cd apps/web && npm run dev

# ------------------------------------------------------------ database
migrate: ## Apply all Alembic migrations
	cd apps/api && alembic upgrade head

new-migration: ## Create a new Alembic migration (MESSAGE="create_x") 
	cd apps/api && alembic revision --autogenerate -m "$(MESSAGE)"

seed: ## Load development seed data
	cd apps/api && python -m app.seed

# ----------------------------------------------------------------- tests
test: test-api test-web ## Run all tests

test-api: ## Run backend tests
	cd apps/api && python -m pytest

test-web: ## Run frontend tests
	cd apps/web && npm run test

# --------------------------------------------------------------- quality
typecheck: ## Type-check the frontend
	cd apps/web && npm run typecheck

lint-web: ## Lint the frontend
	cd apps/web && npm run lint

format: ## Format backend code (ruff)
	cd apps/api && ruff format .
SHELL := /bin/bash

up: ## Build and start everything
	docker compose up --build

down: ## Stop containers
	docker compose down

logs: ## Tail API logs
	docker compose logs -f api

ps: ## List services
	docker compose ps

test: ## Run backend tests
	docker compose exec api pytest -q app/tests || true

seed: ## Seed admin via API
	@bash scripts/seed.sh

curl-login: ## Example login curl
	@bash scripts/login.sh

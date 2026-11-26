.PHONY: help compose-up compose-down compose-logs compose-qdrant dev-agentik dev-front test qdrant-prod

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  make %-12s %s\n", $$1, $$2}'

# ----------------- COMPOSE (front :3000, agentik :8080, qdrant :6333) -----------------
compose-up: ## Build and start the whole stack
	docker compose up --build

compose-down: ## Stop the stack (keeps qdrant and chat history volumes)
	docker compose down

compose-logs: ## Follow logs of all services
	docker compose logs -f

# ----------------- DEV (hot reload: front :4321, agentik :8080) -----------------
compose-qdrant: ## Start only local qdrant, for dev-agentik
	docker compose up -d qdrant

dev-agentik: compose-qdrant ## Run agentik with reload (reads agentik/.env)
	$(MAKE) -C agentik dev

dev-front: ## Run front with Astro dev server (reads front/.env)
	cd front && npm install && npm run dev

test: ## Run front tests
	cd front && npm install && npx vitest run